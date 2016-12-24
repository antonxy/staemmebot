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
        self.troops = None

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

if __name__ == "__main__":
    main()
