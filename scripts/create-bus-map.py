import bs4
import csv
import hashlib
import json
import math
import os
from tqdm import tqdm

xml = open(f'{os.path.dirname(__file__)}/../data/bus-tokyo-sanitized.xml').read()
shibuya_bus = list(csv.DictReader(open(f'{os.path.dirname(__file__)}/../data/shibuya-omote-bus-routes.csv')))
route_bus = json.load(open(f'{os.path.dirname(__file__)}/../data/route-bus.json'))

set_operator = set()
set_route_name = set()

for bus in shibuya_bus:
    operator, route_name = bus["name"].split("-")
    set_operator.add(operator)
    set_route_name.add(route_name.rstrip('折返'))

soup = bs4.BeautifulSoup(xml, 'lxml')
center = [35.662790903962346, 139.70905687170315]
radius = 0.075
minLati, minLong = center[0] - radius, center[1] - radius / math.cos(center[0] * math.pi / 180)
maxLati, maxLong = center[0] + radius, center[1] + radius / math.cos(center[0] * math.pi / 180)

count = 0
width = height = 4000

lines = []


def get_path_command(points):
    lines = " ".join(f"L {x} {y}" for x, y in points[1:])
    return f"M {points[0][0]} {points[0][1]} {lines}"


def get_point(lati, long):
    x = (long - minLong) * width / (maxLong - minLong)
    y = height - (lati - minLati) * height / (maxLati - minLati)
    return x, y


def is_h2o_friendly(points, node_float):
    xmin, ymin = get_point(35.66671461339284, 139.69952789791108)
    xmax, ymax = get_point(35.65772678767955, 139.71346691877417)
    northernLimit, easternLimit = 35.70655094827307, 139.76595308316382
    southernLimit, westernLimit = 35.61423817681835, 139.60721044880458
    return any(
        xmin <= p[0] <= xmax and ymin <= p[1] <= ymax
        for p
        in points
    ) and all(
        southernLimit <= lati <= northernLimit and westernLimit <= long <= easternLimit
        for lati, long
        in node_float
    )


for c in tqdm(soup.find_all("gmlcurve")):
    for p in c.find_all("gmlposlist"):
        points = []
        node_float = [
            tuple(map(float, node.split()))
            for node
            in p.string.split("\n")
            if node.strip()
        ]
        points = [get_point(lati, long) for lati, long in node_float
                  if route_bus[c["gmlid"][2:]]["operator"] in set_operator and route_bus[c["gmlid"][2:]]["route_name"].rstrip('折返') in set_route_name]

        if len(points) >= 2:
            color = hashlib.md5((route_bus[c["gmlid"][2:]]["operator"] + "-" + route_bus[c["gmlid"][2:]]["route_name"].rstrip('折返')).encode('utf-8')).hexdigest()[:6]
            print(f'<path stroke="#{color}" fill="none" stroke-width="6" id="{c["gmlid"]}" d="{get_path_command(points[::5] + [points[-1]])}" />')
