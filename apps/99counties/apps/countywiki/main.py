import json
from kivy.factory import Factory as F
from kivy.resources import resource_find
from kivy.properties import *
from dualdisplay import DualDisplay
from kivy.uix.listview import ListItemButton, ListView
from kivy.adapters.dictadapter import DictAdapter


class WikiDisplay(DualDisplay):
    county_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WikiDisplay, self).__init__(**kwargs)


class CountyListButton(F.ToggleButton):
    pass



class CountyList(F.RelativeLayout):

    def __init__(self, **kwargs):
        super(CountyList, self).__init__(**kwargs)
        self.load_data()

    def load_data(self, *args):
        with open(resource_find('countywiki.json'), 'r') as fp:
            self._county_list = json.load(fp)

        #layout = F.GridLayout(cols=1, size_hint_y=None )
        #layout.bind(minimum_height=layout.setter('height'))
        #layout = F.BoxLayout()

        self.data = {}
        for c in self._county_list:
            self.data[c['title']] = c

        _args = lambda idx, data:{'text': data['title']}
        dict_adapter = DictAdapter(sorted_keys=sorted(self.data.keys()),
            data=self.data, args_converter=_args, selection_mode='single',
            allow_empty_selection=False, cls=ListItemButton)
        layout = ListView(adapter=dict_adapter)

        self.add_widget(layout)
