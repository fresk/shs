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

class WikiDisplay(DualDisplay):
    county_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WikiDisplay, self).__init__(**kwargs)


class CountyListButton(F.ToggleButton):
    data = DictProperty()



class CountyList(F.FloatLayout):
    drag_threshold = NumericProperty(10)
    drag_offset = NumericProperty(0)
    total_offset = NumericProperty(0)
    scroll_layer = ObjectProperty(None)
    item_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CountyList, self).__init__(**kwargs)
        self.drag_touch_id = None
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
            self.drag_touch_id = touch.uid
            touch.ud['last_y'] = touch.y
            touch.ud['move_distance'] = 0
            return True

    def on_touch_move(self, touch):
        if self.drag_touch_id == touch.uid:
            dy = touch.y - touch.ud['last_y']
            touch.ud['last_y'] = touch.y
            touch.ud['move_distance'] += abs(dy)
            self.drag_offset += dy
            print touch.profile
            return True

    def on_touch_up(self, touch):
        if self.drag_touch_id == touch.uid:
            dy = touch.y - touch.ud['last_y']
            touch.ud['move_distance'] += abs(dy)
            self.drag_offset += dy
            if self.drag_offset > self.drag_threshold:
                self.total_offset += self.drag_offset
                self.drag_offset  = 0
            self.drag_touch_id = None
            return True

    def load_data(self, *args):
        with open(resource_find('countywiki.json'), 'r') as fp:
            self.data = sorted(json.load(fp), key=lambda c: c['title'])
        for county in self.data:
            self.item_list.add_widget(CountyListButton(data=county))


