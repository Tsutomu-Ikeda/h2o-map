import bs4
import math
import os
from tqdm import tqdm

xml = open(f'{os.path.dirname(__file__)}/../data/train.xml').read()

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


for c in tqdm(soup.find_all("gml:curve")):
    for p in c.find_all("gml:poslist"):
        points = []
        node_float = [
            tuple(map(float, node.split()))
            for node
            in p.string.split("\n")
            if node.strip()
        ]
        points = [get_point(lati, long) for lati, long in node_float
                  if minLati <= lati <= maxLati and minLong <= long <= maxLong]

        if len(points) >= 2:
            print(f'<path stroke="black" fill="none" stroke-width="2" id="{c["gml:id"]}" type="train" d="{get_path_command(points[::5] + [points[-1]])}" />')
