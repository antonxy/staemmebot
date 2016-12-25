import requests
import traceback
import random
import csv
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

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
        self.server = None
        
        self.resources = None
        self.production = None
        self.units = None
        self.units_h = None
        self.buildings = None
        self.build_queue_empty = None
        self.points = None
        self.recruit_queue_empty = None

    def __repr__(self):
        res = "Village {}: {}\n".format(self.id, self.name)
        res += "Resources: \n"
        for r,v in self.resources.iteritems():
            res += "   {}: {}\n".format(r, v)
        res += "Production: \n"
        for r,v in self.production.iteritems():
            res += "   {}: {}\n".format(r, v)
        if self.units is not None:
	    res += "Units: \n"
	    for r,v in self.units.iteritems():
	        res += "   {}: {}\n".format(r, v)
        res += "Buildings: \n"
        for r,v in self.buildings.iteritems():
            res += "   {}: Level {}, Buildable {}, Cost {} \n".format(r, v['level'], v['buildable'], v['cost'] if not v['fully_built'] else None)
        res += "Build queue empty: {}".format(self.build_queue_empty)
        return res


    def update(self, session):
        self.update_resources(session)
        self.update_buildings(session)
        self.update_recruitables(session)

    def update_resources(self, session):
        main_page_req = session.get(server_url.format(self.server) + "game.php?village={}&screen=overview".format(self.id))
        soup = BeautifulSoup(main_page_req.content, 'html.parser')
        resources_table = soup.find("table", class_='menu_block_right')
        self.resources = {k:int(v) for k,v in {
                'wood': resources_table.find("span", id="wood").text,
                'stone': resources_table.find("span", id="stone").text,
                'iron': resources_table.find("span", id="iron").text,
                'storage': resources_table.find("span", id="storage").text,
                'pop_current': resources_table.find("span", id="pop_current_label").text,
                'pop_max': resources_table.find("span", id="pop_max_label").text
                }.iteritems()}

        production_table = soup.find("div", id="show_prod")
        strongs = production_table.find_all("strong")
        self.production = dict(zip(["wood", "stone", "iron"], map(lambda x: int(x.text), strongs)))

        #units_table = soup.find("div", id="show_units")
        #tds = units_table.find_all("td")
        #def parse_unit(td):
        #    unit_link = td.find("a", class_="unit_link")
        #    if unit_link:
        #        unit_type = unit_link['data-unit']
        #        unit_value = int(td.find("strong").text)
        #        return (unit_type, unit_value)
        #    return None
        #self.units = dict(filter(None, [parse_unit(td) for td in tds]))

    def update_buildings(self, session):
        buildings_page_req = session.get(server_url.format(self.server) + "game.php?village={}&screen=main".format(self.id))
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
                    res['cost'] = {k: int(tr.find("td", class_="cost_"+k).text) for k in ['wood', 'stone', 'iron']}
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

        self.buildings = dict(filter(None, map(parse_row, trs)))
        self.build_queue_empty = queue_empty

    def upgrade_building(self, session, building_id, h_val):
        print("Upgrading {}".format(building_id))
        building_upgrade_req = session.get(server_url.format(self.server) + "game.php?village={}&screen=main&action=upgrade_building&id={}&type=main&h={}".format(self.id, building_id, h_val))
        print(building_upgrade_req)

    def update_recruitables(self, session):
        recruiting_page_req = session.get(server_url.format(self.server) + "game.php?village={}&screen=train".format(self.id))
        soup = BeautifulSoup(recruiting_page_req.content, 'html.parser')
        train_form = soup.find("form", id="train_form")
        if train_form is not None:
	    h_val = re.search("h=([0-9a-zA-Z]*)", train_form['action']).group(1)
	    trs = train_form.find_all("tr", class_="row_a")
	    print train_form.prettify()
	    def parse_unit_row(tr):
	        unit_id = tr.find("a", class_="unit_link")['data-unit']
	        affordable_text = tr.find("a", id=unit_id + "_0_a").text
	        affordable = int(re.search("\(([0-9]*)\)", affordable_text).group(1))
	        number_td_text = tr.find("td", style="text-align: center").text
	        number_match = re.search("([0-9]*)/([0-9]*)", number_td_text)
	        return unit_id, {
	    	    'affordable': affordable,
	    	    'num_in_village': int(number_match.group(1)),
	    	    'num_all': int(number_match.group(2))
	    	    } 
	    self.units = dict(filter(None, map(parse_unit_row, trs)))
	    self.units_h = h_val
        self.recruit_queue_empty = soup.find("div", id="trainqueue_wrap_barracks") is None

    def recruit(self, session, numbers):
        #numbers: {'spear': 10, 'sword': 5, ...} 
        print("Recruiting: {}".format(numbers))
        def format_data(e):
            return "units["+e[0]+"]", e[1]
        data = dict(map(format_data, numbers.iteritems()))
        recruit_req = session.post(server_url.format(self.server) + "game.php?village={}&screen=train&ajaxaction=train&mode=train&h={}&&client_time={}".format(self.id, self.units_h, int(time.time())), data=data)
        print recruit_req

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
    #main_page_req = session.get(server_url.format(user.server) + "game.php")
    #print main_page_req
    #soup = BeautifulSoup(main_page_req.content, 'html.parser')
    #td = soup.find("td", id="menu_row2_village")
    #a = td.find("a")
    #link = a['href']
    #name = a.text
    #print link
    #id_match = re.search("village=([0-9]*)", link).group(1)
    #print id_match
    #village = Village()
    #village.id = id_match
    #village.name = name
    #village.server = user.server
    #return [village]
    
    overview_page_req = session.get(server_url.format(user.server) + "game.php?screen=overview_villages&mode=prod")
    soup = BeautifulSoup(overview_page_req.content, 'html.parser')
    prod_table = soup.find("table", id="production_table")
    trs = soup.find_all("tr", class_="row_a")
    def parse_row(tr):
        v = Village()
        name_td = tr.find("span", class_="quickedit-content")
        name_a = name_td.find("a")
        name_span = name_a.find("span")
        v.name = name_span['data-text']
        id_match = re.search("village=([0-9]*)", name_a['href']).group(1)
        v.id = id_match
        v.server = user.server
        return v
        
    return filter(None, map(parse_row, trs))
    

def select_action(village):
    key = None
    def building_max_res(building):
        if not 'cost' in building:
            return 0
        else:
            return max(building['cost'].itervalues())
    max_building_resource_usage = max(map(building_max_res, village.buildings.itervalues()))
    print("Max building resource usage: {}".format(max_building_resource_usage))
    num_units = sum([u['num_all'] for u in village.units.itervalues()])
    print("Number of units: {}".format(num_units))
    building_level_sum = sum([b['level'] for b in village.buildings.itervalues()])
    print("Building level sum: {}".format(building_level_sum))
    wanted_troops = (building_level_sum ** 2) * 0.05
    print("Wanted troops: {}".format(wanted_troops))
    if max_building_resource_usage > village.resources['storage']:
        action = 'build'
        key = 'storage'
    elif village.resources['pop_current'] > village.resources['pop_max'] * 0.8:
        #Uprade farm if population is nealy full
        action = 'build'
        key = 'farm'
    # Spend similar amounts on troops and buildings if buildings cost quadratically over time
    elif num_units < wanted_troops:
        action = 'recruit'
        selectable = list(set(village.units.iterkeys()) & set(['sword', 'spear']))
        key = random.choice(selectable)
    else:
        #Upgrade resource with least production
        action = 'build'
        key = min(village.production, key=village.production.get)

    if action == 'build':
        print("Want to upgrade {}".format(key))
        if village.buildings[key]['buildable']:
            print("and we can")
            return key 
        else:
            print("but we cant")
    elif action == 'recruit':
        print("Want to recruit {}".format(key))
        if village.units[key]['affordable'] > 0:
            print("and we can")
            return action, key
        else:
            print("but we cant")




def main():
    exception_file = open("error.log", "a")
    while True:
        try:
            #Credentials format (csv): username,password,server
            user = User()
            with open('creds', 'rb') as csvfile:
                credsreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                for row in credsreader:
                    user.user = row[0]
                    user.password = row[1]
                    user.server = row[2]
                    break;

            s = requests.Session()
            login(s, user)
            village = get_villages(s, user)[0]

            while True:
                village.update(s)
                print village

                action, key = select_action(village)
                if action == 'build':
                    if village.build_queue_empty and False:
                        village.upgrade_building(s, key, village.buildings[bid]['h_val'])
                    else:
                        print("Build queue not empty")
                elif action == 'recruit':
                    if village.recruit_queue_empty:
                        village.recruit(s, {key: 1})
                    else:
                        print("Recruit queue not empty")

                time.sleep(10)
        except Exception as ex:
            traceback.print_exc()
            exception_file.write(str(datetime.now()) + "\n")
            traceback.print_exc(file=exception_file)
        time.sleep(100)

if __name__ == "__main__":
    main()
