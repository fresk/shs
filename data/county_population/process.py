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
        name = name.lower().replace(" ", "_")
        county_population[name] = county

for s in sections:
    parse_section(s)



import json
json.dump(county_population, open("county_population.json", "w"))




