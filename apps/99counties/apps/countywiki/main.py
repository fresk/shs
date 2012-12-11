import json
from kivy.factory import Factory as F
from kivy.resources import resource_find
from kivy.properties import *
from dualdisplay import DualDisplay
from kivy.uix.listview import ListItemButton, ListView
from kivy.adapters.dictadapter import DictAdapter
from viewport import TransformLayer
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.animation import Animation

class WikiDisplay(DualDisplay):
    county_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WikiDisplay, self).__init__(**kwargs)


class CountyListButton(F.ToggleButton):
    data = DictProperty()



class CountyList(F.FloatLayout):
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
        print self.velocity
        if (self.velocity * self.velocity < 1.0):
            self.velocity = 0
            if self.total_offset > 0:
                self.anim = Animation(total_offset = 0)
                self.anim.star(self)
            if self.total_offset < (1080 - self.item_list.height):
                self.anim = Animation(total_offset = (1080 - self.item_list.height))
                self.anim.star(self)
            return


        if self.total_offset > 0:
            self.velocity =  self.velocity * 0.5
        if self.total_offset < (1080 - self.item_list.height):
            self.velocity =  self.velocity * 0.5

        self.total_offset += self.velocity
        dx, dy = self.x, self.y + self.total_offset
        self.scroll_layer.transform = Matrix().translate(dx, dy, 0)
        self.velocity =  self.velocity * 0.95
        Clock.schedule_once(self.update_velocity, 1.0/30.0)



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
                print "SELECT ITEM AT", touch.pos, self.total_offset

            self.drag_touch_id = None
            return True

    def load_data(self, *args):
        with open(resource_find('countywiki.json'), 'r') as fp:
            self.data = sorted(json.load(fp), key=lambda c: c['title'])
        for county in self.data:
            self.item_list.add_widget(CountyListButton(data=county))


