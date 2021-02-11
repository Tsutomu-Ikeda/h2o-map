import collections
import itertools
import json
import math
import os
from matplotlib import pyplot as plt
import numpy as np

width = height = 500
center = [35.662790903962346, 139.70905687170315]
radius = 0.075 * 0.6
minLati, minLong = center[0] - radius, center[1] - radius / math.cos(center[0] * math.pi / 180)
maxLati, maxLong = center[0] + radius, center[1] + radius / math.cos(center[0] * math.pi / 180)


def get_point(lati, long):
    x = (long - minLong) * width / (maxLong - minLong)
    y = height - (lati - minLati) * height / (maxLati - minLati)
    return x, y


def get_cost_minute_point(points):
    result = collections.defaultdict(set)
    for p in points:
        result[p["cost"]["minute"]].add(tuple([*map(int, get_point(*p["coord"]))] * 2 + [p["cost"]["minute"]] * 2))
    return result


def calc_costs_mesh(costs, walk_lim=15):
    cost_minute_point = get_cost_minute_point(costs)

    costs_mesh = np.full((width, height), np.nan)
    cost_minute = 0
    point_stack = cost_minute_point[0]

    def assume_minute(a, b):
        return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) * (maxLong - minLong) * 110959 / (height * 90)

    while point_stack:
        next_stack = set()
        for p in point_stack:
            if not(0 <= p[0] < width and 0 <= p[1] < height):
                continue

            if assume_minute((p[0], p[1]), (p[2], p[3])) + p[4] <= cost_minute:
                if (
                    assume_minute((p[0], p[1]), (p[2], p[3])) <= walk_lim
                ) or (
                    not np.isnan(costs_mesh[p[0], p[1]])
                ):
                    if np.isnan(costs_mesh[p[0], p[1]]):
                        costs_mesh[p[0], p[1]] = assume_minute((p[0], p[1]), (p[2], p[3])) + p[4]
                    else:
                        costs_mesh[p[0], p[1]] = min(costs_mesh[p[0], p[1]], assume_minute((p[0], p[1]), (p[2], p[3])) + p[4])

                for i, j in itertools.product([-1, 0, 1], repeat=2):
                    if (
                        0 <= p[0] + i < width
                    ) and (
                        0 <= p[1] + j < height
                    ) and (
                        (
                            np.isnan(costs_mesh[p[0] + i, p[1] + j])
                        ) or (
                            assume_minute((p[0] + i, p[1] + j), (p[2], p[3])) + p[4] < min(costs_mesh[p[0] + i, p[1] + j], cost_minute)
                        )
                    ) and (
                        (
                            assume_minute((p[0] + i, p[1] + j), (p[2], p[3])) <= walk_lim
                        ) or (
                            not np.isnan(costs_mesh[p[0] + i, p[1] + j])
                        )
                    ):
                        next_stack.add((p[0] + i, p[1] + j, p[2], p[3], p[4]))
            else:
                next_stack.add(p)

        cost_minute += 1
        point_stack = next_stack | cost_minute_point[cost_minute]

    return costs_mesh


use_cache = True
costs_mesh = []

import pickle
if use_cache:
    costs_mesh = pickle.load(open("costs_mesh.pickle", 'rb'))
else:
    costs = json.load(open(f'{os.path.dirname(__file__)}/../data/costs-from-sansan.json'))
    train_costs_mesh = calc_costs_mesh(c for c in costs if c["cost"]["type"] in {"walk", "train"})
    bus_costs_mesh = calc_costs_mesh((c for c in costs if c["cost"]["type"] in {"walk", "bus"}), walk_lim=40)
    costs_mesh = np.ma.masked_array(np.fmin(train_costs_mesh, bus_costs_mesh), mask=np.isnan(train_costs_mesh))
    neighbors = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1),
                 (0, 2), (0, -2), (2, 0), (-2, 0))
    a_copy = costs_mesh.copy()
    for hor_shift, vert_shift in neighbors:
        if not np.any(costs_mesh.mask):
            break
        a_shifted = np.roll(a_copy, shift=hor_shift, axis=1)
        a_shifted = np.roll(a_shifted, shift=vert_shift, axis=0)
        idx = ~a_shifted.mask * costs_mesh.mask
        costs_mesh[idx] = a_shifted[idx]
    pickle.dump(costs_mesh, open("costs_mesh.pickle", 'wb'))


X = np.linspace(0, 100, width)
Y = np.linspace(0, 100, height)

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot()
contf = ax.contourf(X, Y, np.flipud(costs_mesh.transpose()), levels=10, cmap='coolwarm')
contf.set_clim(0, 40)
ax.set_aspect('equal', 'box')
plt.axis('off')
plt.savefig(f'{os.path.dirname(__file__)}/../static/contourf.svg', bbox_inches='tight', pad_inches=0, dpi='figure')
cbar = fig.colorbar(contf)
cbar.ax.tick_params(labelsize=20)
plt.savefig(f'{os.path.dirname(__file__)}/../static/colorbar.svg', bbox_inches='tight', pad_inches=0, dpi='figure')
plt.imsave(f'{os.path.dirname(__file__)}/../static/contourf.png', costs_mesh.transpose(), cmap="coolwarm")
