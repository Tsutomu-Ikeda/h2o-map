import bs4
import os

svg = open('map.svg').read()
map_soup = bs4.BeautifulSoup(svg, 'html.parser')

list_bus = [(c.get("id"), c.get("stroke")) for c in map_soup.find_all("path")]

bus_xml = open(f'{os.path.dirname(__file__)}/../data/bus-tokyo-sanitized.xml').read()
bus_soup = bs4.BeautifulSoup(bus_xml, 'lxml')
block_list = {'32c1ca', '277992', '2c8e7b', 'bc9513', '7efd59', 'e8bc15', 'bd06c4', '152da0', '8b4cdf', '4f2d73', '8b4cdf', '8b721b', '58a80a', '55f49d', '935521', 'e8042d', '4aa64a', '1cce95', 'abcb80', 'ee34ef', 'f880ad', 'f7a81d', '14110f', '94b64f', '5c7752', 'e0f4d4', 'f77d13', '78af4b', 'c4b149', 'edd55a', 'c74f43', 'd90410', 'beb2e0', '5ff10f', '9ca3b0'}

for bus_id, color in list_bus:
    if color not in block_list:
        bus_data = bus_soup.select_one(f"ksjBusRoute[gmlid='br{bus_id[2:]}']")
        print(", ".join([f"{bus_id: >6}", color, bus_data.find("ksjboc").string + '-' + bus_data.find("ksjbln").string]))
