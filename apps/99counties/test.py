mesh_ids = {}

for line in open('data/map/iowa.obj'):
    if line.startswith("o"):
        mesh_id = line.split(" ")[1].strip()
        county = ""
        v = line.replace("'", "").split("_")
        if len(v) == 3:
            county = v[1]
        else:
            county = v[1]+"_"+v[2]
        mesh_ids[county] = mesh_id
        print county, "->", mesh_id

import json
json.dump(mesh_ids, open("mesh_ids.json", "w"))
