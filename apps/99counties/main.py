import os
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.factory import Factory as F
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty, NumericProperty
from kivy.properties import ObjectProperty, DictProperty
from viewport import DualDisplayWindow



class DualDisplayScreen(F.FloatLayout):
    app = ObjectProperty(None)
    background = StringProperty("")


class TopScreen(DualDisplayScreen):
    pass


class BottomScreen(DualDisplayScreen):
    pass


class DualDisplay(DualDisplayWindow):
    app = ObjectProperty(None)


class Intro(DualDisplay):
    pass


class Menu(DualDisplay):
    pass


class ExhibitApp(App):
    def build(self):
        kivy.resources.resource_add_path(os.path.join(self.directory, "data"))
        self.root = F.Widget()
        self.menu_screen = Menu(app=self)
        self.active_screen = Intro(app=self)
        self.root.add_widget(self.menu_screen)
        self.root.add_widget(self.active_screen)
        return self.root

    def show_menu(self, *args):
        Animation(opacity=0.0).start(self.active_screen)


ExhibitApp().run()
