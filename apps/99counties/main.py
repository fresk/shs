import os
import sys
import imp
import kivy
import glob
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


class ExhibitRoot(F.Widget):

    def tuio_tranform(self, touch):
        if touch.device == 'tuio':
            touch.apply_transform_2d(lambda x,y: (x,y/2.0))

    def on_touch_down(self, touch):
        self.tuio_transform(touch)
        super(ExhibitRoot, self).on_touch_down()

    def on_touch_move(self, touch):
        self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_move()

    def on_touch_up(self, touch):
        self.tuio_transform(touch)
        return super(ExhibitRoot, self).on_touch_up()


class ExhibitApp(App):
    def build(self):
        self._child_apps = {}
        self.root = ExhibitRoot()
        self.menu_screen = Menu(app=self)
        self.app_screen = Intro(app=self)
        self.root.add_widget(self.app_screen)
        self.load_app_list()
        return self.root

    def load_app_list(self):
        for folder in glob.glob("apps/*"):
            app_name = os.path.basename(folder)
            if not app_name.startswith("_"):
                self.menu_screen.add_app(app_name)

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
