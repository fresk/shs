import os
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
from exhibit import show_menu



class Intro(DualDisplay):
    def on_touch_down(self, touch):
        show_menu()
        return True


class MenuAppButton(ImageButton):
    app_name = StringProperty("")


class Menu(DualDisplay):
    layout = ObjectProperty(None)

    def add_app(self, app_name):
        btn = MenuAppButton(app_name=app_name)
        self.layout.add_widget(btn)

class ExhibitApp(App):
    def build(self):
        self._active_app_path = None
        self._active_app_mod = None
        self._active_app_kv = None

        self.root = F.Widget()
        self.menu_screen = Menu(app=self)
        self.active_screen = Intro(app=self)
        self.root.add_widget(self.active_screen)

        self.menu_screen.add_app('population')
        self.menu_screen.add_app('app2')
        return self.root

    def show_menu(self, *args):
        self.root.clear_widgets()
        print self.active_screen
        self.root.add_widget(self.menu_screen)
        self.root.add_widget(self.active_screen)
        def anim_done(*args):
            print self.root.children
            self.root.remove_widget(self.active_screen)
            self.active_screen = None
        self.active_screen.alpha_hide = 0.0
        anim = Animation(alpha_hide=1.0)
        anim.bind(on_complete=anim_done)
        anim.start(self.active_screen)

    def start_app(self, app_name):
        app_path = os.path.join(self.directory, "apps", app_name)

        #set active app, and add resource folder
        if self._active_app_path:
            kivy.resources.resource_remove_path(self._active_app_path)
        kivy.resources.resource_add_path(app_path)
        self._active_app_path = app_path

        #load applications main.py / code
        if self._active_app_mod:
            del self._active_app_mod
        m_name = "_mod_%s" % app_name
        m_path = os.path.join(app_path, 'main.py')
        m_file = open(m_path, 'r')
        self._active_app_mod = imp.load_source(m_name, m_path, m_file)

        #load apps ui.kv
        if self._active_app_kv:
            Builder.unload_file(self._active_app_kv)
        self._active_app_kv = os.path.join(app_path, 'ui.kv')
        self.active_screen = Builder.load_file(self._active_app_kv)

        #transition
        self.active_screen.alpha_show = 0
        self.root.add_widget(self.active_screen)
        def anim_done(*args):
            self.root.remove_widget(self.menu_screen)
        anim = Animation(alpha_show=1.0)
        anim.bind(on_complete=anim_done)
        anim.start(self.active_screen)

ExhibitApp().run()
