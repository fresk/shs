import os
import glob
import shutil
import json
import subprocess
import xml.etree.ElementTree as ET

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

    for elem in root.iter('path'):
        #county id
        eid = elem.attrib['id']

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
                'pos':(-cx,-cy),
                'size':(cw,ch),
                'name':eid.replace("_", " "),
                'svg': 'counties/{0}.svg'.format(eid),
                'png': 'counties/{0}.png'.format(eid)
        }

        #add only this path/county to the new svg
        elem.attrib['style'] = style
        croot.append(elem)
        ctree.write(counties[eid]['svg'])
    json.dump(counties, open('counties.json', 'w'))


def svg2png(infile, outfile):
    cmd = "rsvg-convert -z 4 -a {0} -o {1}".format(infile, outfile)
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    "creating counties sub-directory..."
    shutil.rmtree("counties", ignore_errors=True)
    os.makedirs("counties")


    print "extarcting countues from iowa.svg..."
    extract_counties('iowa.svg')

    print "rendering png images from svgs"
    for f in glob.glob('counties/*.svg'):
        print "rendering", f
        svg2png(f, f.replace('.svg', '.png'))

