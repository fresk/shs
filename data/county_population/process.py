fin = open("polpulation_by_county_1900-1990.txt")

data = fin.read()

sections = data.split("\n ")
for s in sections:
    with open("%d.txt" %sections.index(s), 'w') as fout:
        fout.write(s)



fips_county = {}
county_population = {}

def parse_section(s):
    lines = s.split("\n")
    col_names = lines[0].split()[1:]

    rows = []
    #skip USA, blank line and Iowa
    for l in lines[4:]:
        rows.append(l.split())

    for r in rows:
        if not r:
            continue
        fips = r.pop(0)
        county = county_population.get(fips) or {}
        county['FIPS'] = fips
        for col in col_names:
            v = r.pop(0)
            county[col] = int(v)
        name = county['name'] = " ".join(r)
        id_name = name.lower().replace(" ", "_").replace('_county', '')
        county['id'] = id_name

        county_population[fips] = county

for s in sections:
    parse_section(s)

population_by_name = {}
for k,v in county_population.iteritems():
    population_by_name[v['id']] = v

import json
json.dump(population_by_name, open("county_population.json", "w"))




