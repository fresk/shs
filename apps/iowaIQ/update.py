import json
import requests
from pprint import pprint


def pull_update():
    r = requests.get('http://www.fresksite.net/dcadb/api/questions.php')
    json.dump(r.json, open('questions.json', 'w'))




pull_update()
