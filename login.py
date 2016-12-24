import requests
from bs4 import BeautifulSoup
import re

#main_url = "http://localhost:8080/"
main_url = "https://www.die-staemme.de/"
server_url = "https://{}.die-staemme.de/"

class User(object):
    def __init__(self):
        self.user = None
        self.password = None
        self.resources = None
        self.server = None

class Village(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.resources = None
        self.production = None
        self.units = None

def login(session, user):
    #Load main page to get cookies
    main_req = session.get(main_url)
    login_req = session.post(main_url + "index.php?action=login&show_server_selection=1", data={'clear': 'true', 'cookie': 'true', 'password': user.password, 'user': user.user})
    print(login_req)
    print(login_req.cookies)

    world_login_data = {'user': session.cookies['user'], 'password': session.cookies['password'], 'sso': 0}
    print(world_login_data)
    world_login_req = session.post(main_url + "index.php?action=login&server_{}".format(user.server), data=world_login_data)
    print(world_login_req)

def get_villages(session, user):
    main_page_req = session.get(server_url.format(user.server) + "game.php")
    print main_page_req
    soup = BeautifulSoup(main_page_req.content, 'html.parser')
    td = soup.find("td", id="menu_row2_village")
    a = td.find("a")
    link = a['href']
    name = a.text
    print link
    id_match = re.search("village=([0-9]*)", link).group(1)
    print id_match
    village = Village()
    village.id = id_match
    village.name = name
    return [village]
#    
#    overview_page_req = session.get(server_url.format(user.server) + "game.php?screen=overview_villages&mode=prod")
#    soup = BeautifulSoup(overview_page_req.content, 'html.parser')
#    prod_table = soup.find("table", id="production_table")
    

def update_resources(session, user, village):
    main_page_req = session.get(server_url.format(user.server) + "game.php?village={}&screen=overview".format(village.id))
    soup = BeautifulSoup(main_page_req.content, 'html.parser')
    print(soup.title)
    resources_table = soup.find("table", class_='menu_block_right')
    village.resources = {k:int(v) for k,v in {
            'wood': resources_table.find("span", id="wood").text,
            'stone': resources_table.find("span", id="stone").text,
            'iron': resources_table.find("span", id="iron").text,
            'storage': resources_table.find("span", id="storage").text,
            'pop_current': resources_table.find("span", id="pop_current_label").text,
            'pop_max': resources_table.find("span", id="pop_max_label").text
            }.iteritems()}

    production_table = soup.find("div", id="show_prod")
    strongs = production_table.find_all("strong")
    village.production = dict(zip(["wood", "stone", "iron"], map(lambda x: int(x.text), strongs)))

    units_table = soup.find("div", id="show_units")
    tds = units_table.find_all("td")
    def parse_unit(td):
        unit_link = td.find("a", class_="unit_link")
        if unit_link:
            unit_type = unit_link['data-unit']
            unit_value = int(td.find("strong").text)
            return (unit_type, unit_value)
        return None
    village.units = dict(filter(None, [parse_unit(td) for td in tds]))

def get_buildings(session, user, village):
    buildings_page_req = session.get(server_url.format(user.server) + "game.php?village={}&screen=main".format(village.id))
    soup = BeautifulSoup(buildings_page_req.content, 'html.parser')
    buildings_table = soup.find("table", id="buildings")
    trs = buildings_table.find_all("tr")
    def parse_row(tr):
        if 'id' in tr.attrs:
            res = {}
            building_id = str(re.match("main_buildrow_(.*)", tr['id']).group(1))
            first_td = tr.find("td")
            level_text = first_td.find("span").text
            level_match = re.match("Stufe ([0-9]*)", level_text)
            level = 0
            if level_match:
                level = int(level_match.group(1))
            res['level'] = level
            
            build_options = tr.find("td", class_="build_options")
            fully_built = build_options is None
            res['fully_built'] = fully_built
            if not fully_built:
                error_message = build_options.find("div", class_="inactive")
                buildable = False
                if error_message is None: 
                    build_a = build_options.find("a", id="main_buildlink_" + building_id + "_" + str(level + 1))
                    if build_a:
                        buildable = True
                        build_link = build_a['href']
                        h_val = re.search("h=([0-9a-zA-Z]*)", build_link).group(1)
                        res['h_val'] = h_val
                res['buildable'] = buildable
            else:
                res['buildable'] = False

            return (building_id, res)

    build_queue_table = soup.find("table", id="build_queue")
    queue_empty = build_queue_table is None

    return dict(filter(None, map(parse_row, trs))), queue_empty

def upgrade_building(session, user, village, building_id, h_val):
    print("Upgrading {}".format(building_id))
    building_upgrade_req = session.get(server_url.format(user.server) + "game.php?village={}&screen=main&action=upgrade_building&id={}&type=main&h={}".format(village.id, building_id, h_val))
    print(building_upgrade_req)

def select_building_to_upgrade(buildings, village):
    key = None
    if village.resources['pop_current'] > village.resources['pop_max'] * 0.8:
        #Uprade farm if population is nealy full
        key = 'farm'
    else:
        #Upgrade resource with least production
        key = min(village.production, key=village.production.get)

    print("Want to upgrade {}".format(key))
    if buildings[key]['buildable']:
        print("and we can")
        return key 
    else:
        print("but we cant")


def main():
    user = User()
    user.user = 'vuxoyuw'
    user.password = 'foobar'
    user.server = 'de136'

    s = requests.Session()
    login(s, user)
    village = get_villages(s, user)[0]

    update_resources(s, user, village)
    print village.resources
    print village.production
    print village.units

    buildings, queue_empty = get_buildings(s, user, village)
    print buildings 
    
    if queue_empty:
        bid = select_building_to_upgrade(buildings, village)
        if bid is not None:
            upgrade_building(s, user, village, bid, buildings[bid]['h_val'])
    else:
        print("Build queue not empty")

if __name__ == "__main__":
    main()
