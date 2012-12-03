import os
import sys
import imp
import kivy
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
from exhibit import show_menu, ChildApp



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

class ExhibitApp(App):
    def build(self):
        self._child_apps = {}
        self.root = F.Widget()
        self.menu_screen = Menu(app=self)
        self.app_screen = Intro(app=self)
        self.root.add_widget(self.app_screen)

        self.menu_screen.add_app('population')
        return self.root

    def show_menu(self, *args):
        self.root.clear_widgets()
        self.root.add_widget(self.menu_screen)
        self.root.add_widget(self.app_screen)
        def anim_done(*args):
            self.root.remove_widget(self.app_screen)
            self.app_screen = None
        self.app_screen.hide(callback=anim_done)

    def load_app(self, app_name):
        if self._child_apps.get(app_name):
            return self._child_apps[app_name]
        child_app = ChildApp(app_name)
        self._child_apps[app_name] = child_app
        return child_app

    def unload_app(self, child_app):
        app_name = child_app.name
        child_app.unload()
        self._child_apps.pop(app_name)

    def start_app(self, app_name):
        self.child_app = self.load_app(app_name)
        self.app_screen = self.child_app.build()

        def anim_done(*args):
            self.root.remove_widget(self.menu_screen)
        self.root.add_widget(self.app_screen)
        self.app_screen.show(callback=anim_done)


ExhibitApp().run()
