import json
from kivy.factory import Factory as F
from kivy.resources import resource_find
from kivy.properties import *
from dualdisplay import DualDisplay

class WikiDisplay(DualDisplay):
    county_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WikiDisplay, self).__init__(**kwargs)


class CountyListButton(F.ToggleButton):
    pass



class CountyList(F.ScrollView):

    def __init__(self, **kwargs):
        super(CountyList, self).__init__(**kwargs)
        self.load_data()

    def load_data(self, *args):
        with open(resource_find('countywiki.json'), 'r') as fp:
            self.data = json.load(fp)

        layout = F.GridLayout(cols=1, spacing=2, size_hint_y=None )
        layout.bind(minimum_height=layout.setter('height'))
        #layout = F.BoxLayout()
        self.add_widget(layout)
        for c in self.data:
            btn = CountyListButton(text=c['title'])
            layout.add_widget(btn)
            layout.height += 10

