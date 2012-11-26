from kivy.app import App
from kivy.factory import Factory as F
from kivy.properties import ListProperty
from functools import partial
import csv


class StringIndex(object):
    def __init__(self, str_list):
        records = [s.strip() for s in str_list]
        self.index = self.create_index(records)

    def create_index(self, items, level=0):
        if len(items) < 10 or level>10:
            return items

        lookup = {}
        for i in items:
            k = ''
            if len(i) > level:
                k = i[level].lower()
            lookup[k] = lookup.get(k) or []
            lookup[k].append(i)

        for idx in lookup.keys():
            lookup[idx] = self.create_index(lookup[idx], level+1)
        return lookup

    def find_all(self, root):
        matches = []
        for k in root.keys():
            sub = root[k]
            if type(sub) == type([]):
                matches.extend(sub)
            else:
                matches.extend(self.find_all(sub))
        return matches

    def find_prefix(self, prefix):
        root = self.index
        for c in prefix.lower():
            root = root.get(c, [])
            if type(root) == type([]):
                return root
        return self.find_all(root)




class AutoCompleteApp(App):

    def load_data(self):
        places = []
        with open('uscities.csv', 'rb') as f:
            reader = csv.DictReader(f)
            for row in reader:
                place = "{0}, {1}\n".format(row['name'], row['state_code'])
                places.append(place)
        self.text_index = StringIndex(places)



    def autocomplete(self, *args):
        self.completion_layout.clear_widgets()
        if len(self.text_input.text) == 0:
            return

        prefix = self.text_input.text
        completions = self.text_index.find_prefix(prefix)[:10]

        completions = [c for c in completions if c.lower().startswith(prefix.lower())]
        if len(completions) == 1:
            return


        for i in range(10 - len(completions)):
            self.completion_layout.add_widget(F.Widget(size_hint_y=.1))

        for c in completions:
            b = F.Button(
                    text=c,
                    size_hint_y=.1,
                    text_size=(self.text_input.width-50, None),
                    halign='left'
            )

            def _set_text(txt, *args):
                self.text_input.text = txt
            b.bind(on_release=partial(_set_text, c))
            self.completion_layout.add_widget(b)



    def build(self):
        self.load_data()
        self.root = F.BoxLayout(orientation='vertical')
        self.text_input = F.TextInput(size_hint_y=.1, focus=True)
        self.text_input.bind(text=self.autocomplete)
        self.completion_layout = F.BoxLayout(size_hint_y=.9, orientation='vertical')
        self.root.add_widget(self.completion_layout)
        self.root.add_widget(self.text_input)


AutoCompleteApp().run()





