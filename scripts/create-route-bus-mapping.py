import bs4
import json
import os
from tqdm import tqdm

bus_xml = open(f'{os.path.dirname(__file__)}/../data/bus-tokyo-sanitized.xml').read()
soup = bs4.BeautifulSoup(bus_xml, 'html.parser')

data = {}

for route in tqdm(soup.select('ksjbusroute[gmlid]')):
    data[route["gmlid"][2:]] = {
        "operator": route.find("ksjboc").string,
        "route_id": route.find("ksjbln").string
    }


with open("route-bus.json", 'w') as f:
    f.write(json.dumps(data))
