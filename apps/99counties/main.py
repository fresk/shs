import os
import sys
import imp
import kivy
import glob
import json
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.core.image import Image
from kivy.properties import StringProperty, NumericProperty
from kivy.properties import ObjectProperty, DictProperty
from kivy.factory import Factory as F
from dualdisplay import DualDisplay
from imagebutton import ImageButton
from kivy.cache import Cache
from exhibit import show_menu, ChildApp
from objloader import ObjFile
import gc


class Intro(DualDisplay):
    def on_touch_down(self, touch):
        show_menu()
        return True

    def hide(self, callback=None):
        self.opacity = 1.0
        self.arrange_displays()
        anim = Animation(opacity=0.0)
        if callback:
            anim.bind(on_complete=callback)
        anim.start(self)

class MenuAppButton(ImageButton):
    app_name = StringProperty("")


class Menu(DualDisplay):
    layout = ObjectProperty(None)

    def add_app(self, app_name):
        btn = MenuAppButton(app_name=app_name)
        self.layout.add_widget(btn)


class ExhibitRoot(F.Widget):

    def tuio_transform(self, touch):
        if touch.device == 'tuio':
            touch.apply_transform_2d(lambda x,y: (x,y/2.0))

    def on_touch_down(self, touch):
        if App.get_running_app().transitioning:
            return True
        self.tuio_transform(touch)
        super(ExhibitRoot, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if App.get_running_app().transitioning:
            return True
        self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if App.get_running_app().transitioning:
            return True
        self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_up(touch)


class ExhibitApp(App):
    selected_county = StringProperty("polk")


    def build(self):
        self._child_app = None
        self.transitioning = False
        self.root = ExhibitRoot()
        self.menu_screen = Menu(app=self)
        self.app_screen = Intro(app=self)
        self.root.add_widget(self.app_screen)
        self.load_app_list()
        self.load_data()
        return self.root

    def load_data(self, *args):
        print "laoding obj model"
        self.map_model = ObjFile("data/map/iowa.obj")

        print "laoding mesh ids"
        mesh_ids = json.load(open('mesh_ids.json', 'r'))


        print "laoding historix sites"
        historic_sites = json.load(open('historicsites.json', 'r'))

        print "laoding county data"
        county_wiki = json.load(open('countywiki.json'))

        print "mixing shit together..."
        self.counties = {}
        for c in county_wiki:
            n = c['name'].replace("'","").replace("-", "_")
            mid = mesh_ids[n]
            c['name'] = n
            self.counties[n] = c
            self.counties[n]['mesh'] = self.map_model.objects[mid]

        self.historic_sites = {}
        for site in historic_sites:
            n = site['name'].replace("'","").replace("-", "_")
            site['name']= n
            self.historic_sites[n] = site


    def load_app_list(self):
        for folder in glob.glob("apps/*"):
            app_name = os.path.basename(folder)
            if not app_name.startswith("_"):
                self.menu_screen.add_app(app_name)

    def show_menu(self, *args):
        if self.transitioning:
            return
        self.transitioning = True
        self.root.clear_widgets()
        self.root.add_widget(self.menu_screen)
        self.root.add_widget(self.app_screen)
        def anim_done(*args):
            self.transitioning = False
            self.root.remove_widget(self.app_screen)
            self.app_screen = None
        self.app_screen.hide(callback=anim_done)

    def load_app(self, app_name):
        if self._child_app:
            self.unload_app(self._child_app)
        self._child_app = ChildApp(app_name)
        return self._child_app

    def unload_app(self, child_app):
        app_name = child_app.name
        child_app.unload()
        Cache._objects['kv.image'] = {}
        Cache.register('kv.image', timeout=10)
        self._child_app = None
        gc.collect()

    def start_app(self, app_name):
        if self.transitioning:
            return
        self.transitioning = True
        self._child_app = self.load_app(app_name)
        self.app_screen = self._child_app.build()

        def anim_done(*args):
            self.transitioning = False
            self.root.remove_widget(self.menu_screen)
        self.root.add_widget(self.app_screen)
        self.app_screen.show(callback=anim_done)


ExhibitApp().run()
