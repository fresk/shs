import os
import sys
import imp
import kivy
import glob
import json
from kivy.app import App
from kivy.base import EventLoop
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
from objloader import ObjFile

import apps.countywiki
import apps.population
import apps.scratch
import apps.historicsites
import apps.iowans
import apps.hollywood


class Intro(DualDisplay):
    def on_touch_down(self, touch):
        App.get_running_app().show_menu()
        return True

    def hide(self, callback=None):
        self.opacity = 1.0
        self.arrange_displays()
        anim = Animation(opacity=0.0)
        if callback:
            anim.bind(on_complete=callback)
        anim.start(self)


class BackToMenuButton(ImageButton):
    pass


class MenuAppButton(ImageButton):
    app_name = StringProperty("")


class Menu(DualDisplay):
    layout = ObjectProperty(None)

    def add_app(self, app_name):
        btn = MenuAppButton(app_name=app_name)
        self.layout.add_widget(btn)


class ExhibitRoot(F.Widget):

    #def tuio_transform(self, touch):
    #    if touch.device == 'tuio':
    #        touch.apply_transform_2d(lambda x,y: (x,y/2.0))

    def on_touch_down(self, touch):
        if App.get_running_app().transitioning:
            return True
        #self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if App.get_running_app().transitioning:
            return True
        #self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if App.get_running_app().transitioning:
            return True
        #self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_up(touch)



class TuioTransform(object):
    def process(self, events):
        processed = []
        for etype, touch in events:
            if not touch.is_touch:
                continue
            if touch.device != "mouse":
                touch.sy = touch.sy/2.0
            processed.append((etype, touch))
        return processed



class ExhibitApp(App):
    selected_county = StringProperty("polk")

    def build(self):
        self.transitioning = False

        self.load_data()
        self.intro_screen = Intro(app=self)
        self.menu_screen = Menu(app=self)

        self.menu_screen.add_app("historicsites")
        self.menu_screen.add_app("population")
        self.menu_screen.add_app("scratch")
        self.menu_screen.add_app("countywiki")
        self.menu_screen.add_app("iowans")
        self.menu_screen.add_app("hollywood")

        self.child_apps = {}
        self.child_apps['population'] = Builder.load_file('apps/population/ui.kv')
        self.child_apps['historicsites'] = Builder.load_file('apps/historicsites/ui.kv')
        self.child_apps['scratch'] = Builder.load_file('apps/scratch/ui.kv')
        self.child_apps['countywiki'] = Builder.load_file('apps/countywiki/ui.kv')
        self.child_apps['iowans'] = Builder.load_file('apps/iowans/ui.kv')
        self.child_apps['hollywood'] = Builder.load_file('apps/hollywood/ui.kv')

        self.root = ExhibitRoot()
        self.show_intro()
        return self.root

    def show_intro(self):
        self.root.clear_widgets()
        self.app_screen = self.intro_screen
        self.root.add_widget(self.intro_screen)

    def load_data(self, *args):
        print "laoding obj model"
        self.map_model = ObjFile("data/map/iowa2.obj")

        print "laoding mesh ids"
        mesh_ids = json.load(open('data/mesh_ids.json', 'r'))

        print "laoding county data"
        county_wiki = json.load(open('resources/countywiki.json'))

        print "laoding scratch data"
        self.scratches = json.load(open('resources/scratches.json'))

        print "prepping data structures..."
        self.counties = {}
        for c in county_wiki:
            n = c['name'].replace("'","").replace("-", "_")
            mid = mesh_ids[n]
            c['name'] = n
            self.counties[n] = c
            self.counties[n]['mesh'] = self.map_model.objects[mid]

        print "laoding historic sites"
        self.historic_sites = {}
        historic_sites = json.load(open('resources/historicsites.json', 'r'))
        for site in historic_sites:
            n = site['name'].replace("'","").replace("-", "_")
            site['name']= n
            site['icon'] = 'historic'
            self.historic_sites[n] = site

        print "laoding hollywood iowans"
        self.hollywood = {}
        hollywood = json.load(open('resources/hollywood.json', 'r'))
        for site in hollywood:
            n = site['name'].replace("'","").replace("-", "_")
            site['name']= n
            site['icon'] = 'hollywood'
            self.hollywood[n] = site


        print "laoding medal of honor iowans"
        self.medals = {}
        medals = json.load(open('resources/medals.json', 'r'))
        for site in medals:
            n = site['name'].replace("'","").replace("-", "_")
            site['name']= n
            site['icon'] = 'medal'
            self.medals[n] = site


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

    def start_app(self, app_name):
        if self.transitioning:
            return
        self.transitioning = True

        def anim_done(*args):
            self.transitioning = False
            self.root.remove_widget(self.menu_screen)
        self.app_screen = self.child_apps[app_name]
        self.root.add_widget(self.app_screen)
        self.app_screen.show(callback=anim_done)


ExhibitApp().run()
