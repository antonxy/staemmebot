import requests
from bs4 import BeautifulSoup

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
        self.resources = None

def login(session, user):
    main_req = session.get(main_url)
    login_req = session.post(main_url + "index.php?action=login&show_server_selection=1", data={'clear': 'true', 'cookie': 'true', 'password': user.password, 'user': user.user})
    print(login_req)
    print(login_req.cookies)

    world_login_data = {'user': session.cookies['user'], 'password': session.cookies['password'], 'sso': 0}
    print(world_login_data)
    world_login_req = session.post(main_url + "index.php?action=login&server_{}".format(user.server), data=world_login_data)
    print(world_login_req)

def update_resources(session, user):
    main_page_req = session.get(server_url.format(user.server) + "game.php")
    soup = BeautifulSoup(main_page_req.content, 'html.parser')
    print(soup.title)
    resources_table = soup.find("table", class_='menu_block_right')
    user.resources = {k:int(v) for k,v in {
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
    update_resources(s, user)

    print user.resources

if __name__ == "__main__":
    main()
