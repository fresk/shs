import json
from kivy.app import App
from kivy.factory import Factory as F
from kivy.resources import resource_find
from kivy.properties import *
from kivy.uix.listview import ListItemButton, ListView
from kivy.adapters.dictadapter import DictAdapter
from viewport import TransformLayer
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.animation import Animation
from countymap import CountyMap
from dualdisplay import DualDisplay

class WikiDisplay(DualDisplay):
    selected_county = StringProperty("")
    county_list = ObjectProperty(None)
    county_map = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WikiDisplay, self).__init__(**kwargs)
        with open(resource_find('countywiki.json'), 'r') as fp:
            self.data = sorted(json.load(fp), key=lambda c: c['title'])
        self.counties = {}
        for c in self.data:
            self.counties[c['name'].replace('-', "_")] = c
        def set_polk(*args):
            self.selected_county = "polk"
        Clock.schedule_once(set_polk)

    def on_county_list(self, *args):
        self.county_list.data = self.data
        self.county_list.load_data()

    def on_selected_county(self, *args):
        print "wiki selection", self.selected_county

class FactTitle(F.Label):
    pass

class FactText(F.Label):
    pass

class CountyHeader(F.Widget):
    text = StringProperty("")

class CountyInfoWiki(F.FloatLayout):
    display = ObjectProperty(None)
    selected_county = StringProperty("")
    county_name = StringProperty("")
    county_seat = StringProperty("")
    county_size = StringProperty("")
    established = StringProperty("")
    formed_from = StringProperty("")
    etymology = StringProperty("")
    population = StringProperty("")

    def on_selected_county(self, *args):
        self.data = App.get_running_app().counties[self.selected_county]
        self.county_name = self.data['title']
        self.county_seat = self.data['county_seat']
        self.county_size = self.data['size'] + "sq. miles"
        self.etymology = self.data['etymology']
        self.established = self.data['established']
        self.formed_from = self.data['formed_from']
        self.population = self.data['population']



class CountyListButton(F.ToggleButton):
    data = DictProperty()

class CountyList(F.FloatLayout):
    display = ObjectProperty(None)
    selected_county = StringProperty("")
    drag_threshold = NumericProperty(20)
    drag_offset = NumericProperty(0)
    total_offset = NumericProperty(0)
    scroll_layer = ObjectProperty(None)
    item_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CountyList, self).__init__(**kwargs)
        self.drag_touch_id = None
        self.anim = None
        Clock.schedule_once(self.load_data)

    def on_drag_offset(self, *args):
        if self.scroll_layer is None:
            return
        toy = self.total_offset
        doy = self.drag_offset
        dx, dy = self.x, self.y + toy + doy
        self.scroll_layer.transform = Matrix().translate(dx, dy, 0)

    def on_total_offset(self, *args):
        if self.scroll_layer is None:
            return
        toy = self.total_offset
        doy = self.drag_offset
        dx, dy = self.x, self.y + toy + doy
        self.scroll_layer.transform = Matrix().translate(dx, dy, 0)



    def on_touch_down(self, touch):
        if self.drag_touch_id != None:
            return False
        if self.collide_point(*touch.pos):
            if self.anim:
                Animation.cancel_all(self, 'total_offset')
                self.anim = None
            self.drag_touch_id = touch.uid
            self.velocity = 0
            touch.ud['last_y'] = touch.y
            t = (touch.time_update, touch.y)
            touch.ud['t_update'] = [t,t,t,t]
            touch.ud['move_distance'] = 0
            return True

    def on_touch_move(self, touch):
        if self.drag_touch_id == touch.uid:
            dy = touch.y - touch.ud['last_y']
            touch.ud['last_y'] = touch.y
            touch.ud['move_distance'] += abs(dy)
            t = (touch.time_update, touch.y)
            tupdate = touch.ud['t_update'][1:]
            tupdate.append(t)
            touch.ud['t_update'] = tupdate
            if touch.ud['move_distance'] > self.drag_threshold:
                self.drag_offset += dy
            return True

    def update_velocity(self, *args):
        #print self.velocity, self.total_offset
        if (self.velocity * self.velocity < 1.0):
            self.velocity = 0
            #print self.total_offset
            if self.total_offset > 0:
                of = self.total_offset *2.0
                dd = min(of, self.height) / (self.height+1.0)
                self.anim = Animation(total_offset = 0, t='out_quart', d=dd+0.3)
                self.anim.start(self)
            if self.total_offset < (1080 - self.item_list.height):
                of = abs(self.total_offset - (1080 - self.item_list.height)) * 2.0
                dd = max(of, self.height) / (self.height+1.0)
                self.anim = Animation(total_offset = (1080 - self.item_list.height),t='out_quart', d=dd+0.3)
                self.anim.start(self)
            return


        if self.total_offset > 0:
            of = self.total_offset *2.0
            dd = min(of, self.height) / (self.height+1.0)
            self.velocity =  self.velocity * (1.0-dd)
        if self.total_offset < (1080 - self.item_list.height):
            of = abs(self.total_offset - (1080 - self.item_list.height)) * 2.0
            dd = max(of, self.height) / (self.height+1.0)
            self.velocity =  self.velocity * (1.0-dd)

        self.total_offset += self.velocity
        self.velocity =  self.velocity * 0.95
        Clock.schedule_once(self.update_velocity, 1.0/30.0)

    def selection(self, item):
        App.get_running_app().selected_county = item['name'].replace("-", "_")

    def on_selected_county(self, *args):
        for btn in self.item_list.children:
            n = btn.data['name'].replace("-", "_")
            if n == self.selected_county:
                btn.state="down"
            else:
                btn.state="normal"


    def on_touch_up(self, touch):
        if self.drag_touch_id == touch.uid:
            dy = touch.y - touch.ud['last_y']
            touch.ud['move_distance'] += abs(dy)
            if touch.ud['move_distance'] > self.drag_threshold:
                self.total_offset += self.drag_offset + dy
                self.drag_offset  = 0

                tup = touch.ud['t_update']
                dura = (tup[3][0] - tup[0][0]) * 100.0
                dist = tup[3][1] - tup[0][1]

                self.velocity = 2.5 * (dist/dura)
                Clock.schedule_once(self.update_velocity, 1.0/30.0)
            #if 'mov' in touch.profile:
            #    touch.Y
            else:
                self.drag_offset  = 0
                self.velocity = 0
                x,y = 10, max(0,min(touch.y - self.total_offset, self.item_list.height-1))
                idx = int(y / 80)
                btn = self.item_list.children[idx]
                self.selection(btn.data)

            self.drag_touch_id = None
            return True

    def load_data(self, *args):
        for county in self.data:
            self.item_list.add_widget(CountyListButton(data=county))


