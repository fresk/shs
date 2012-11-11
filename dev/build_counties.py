import os
import glob
import shutil
import json
import subprocess
import xml.etree.ElementTree as ET


DEV_PATH = os.path.dirname(__file__)
SHS_PATH = os.path.join(DEV_PATH, '..')


class BoundingBox(object):
    def __init__(self):
        self.x = float('inf')
        self.y = float('-inf')
        self.xmax = float('-inf')
        self.ymin = float('inf')
        self.height = 0

    def add_point(self, x,y):
        self.x = min(x, self.x)
        self.y = max(y, self.y)
        self.xmax = max(x, self.xmax)
        self.ymin = min(y, self.ymin)

        self.width = self.xmax - self.x
        self.height = self.y - self.ymin
        self.pos = (self.x, self.y)
        self.size = (self.width, self.height)


def load_svg_path(elem):
    return map(eval, elem.attrib['d'][2:-2].split("L"))


def dump_svg_path(elem, path):
    d = "M %f,%f " % path.pop(0)
    for p in path:
        d += "L %f,%f " % p
    elem.attrib['d'] = d+"z"


padding = 0
style = "fill:#ffffff;stroke:#000000;stroke-width:1;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none"
def extract_counties(infile):
    et = ET.parse(infile)
    root = et.getroot()

    counties = {}

    W = float(root.attrib['width'])
    H = float(root.attrib['height'])

    for elem in root.iter('path'):
        #county id

        eid = elem.attrib['id'].lower()

        #read in another copy and clear all paths out for blank svg
        ctree = ET.parse(infile)
        croot = ctree.getroot()
        croot.clear()

        #boundign box for this path/county:
        b = BoundingBox()
        for p in load_svg_path(elem):
            b.add_point(*p)


        #set width & height of extarcted path/county
        pad = padding
        pp = pad*2
        cw,ch = b.width+pp, b.height+pp
        cx,cy = pad - b.x, pad - b.y
        croot.set("width", str(cw))
        croot.set("height", str(ch))
        cropped = [(p[0]+cx, p[1]+cy+b.height) for p in load_svg_path(elem)]
        dump_svg_path(elem, cropped)



        counties[eid] = {
                'pos': (-cx, H+cy+ch),
                'size': (b.width, b.height),
                'name': elem.attrib['id'].replace("_", " "),
                'id': eid
        }

        #add only this path/county to the new svg
        elem.attrib['style'] = style
        croot.append(elem)

        #write county data
        county_path = os.path.join(SHS_PATH, "data/counties", eid)
        try:
            os.makedirs(county_path)
        except:
            pass
        ctree.write(os.path.join(county_path, "map.svg"))
        with open(os.path.join(county_path, "facts.txt"), 'w') as f:
            f.write("Some facts about {0}".format(counties[eid]['name']))

    county_path = os.path.join(SHS_PATH, "data/counties")
    json.dump(counties, open(os.path.join(county_path, 'counties.json'), 'w'))


def svg2png(infile, outfile):
    cmd = "rsvg-convert -z 4 -a {0} -o {1}".format(infile, outfile)
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    "creating counties sub-directory..."
    print "extarcting countues from iowa.svg..."
    extract_counties(os.path.join(DEV_PATH,'iowa.svg'))


