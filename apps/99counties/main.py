import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory as F
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty, NumericProperty
from kivy.properties import ObjectProperty, DictProperty
from viewport import DualDisplayWindow

Builder.load_string("""

<ProjectorScreen>:
    text: "TOP  %s" % self.size

<MainScreen>:
    text: "MAIN  %s" % self.size

""")

class ProjectorScreen(F.Button):
    app = ObjectProperty(None)

class MainScreen(F.Button):
    app = ObjectProperty(None)

class ExhibitApp(App):
    def build(self):
        self.root = DualDisplayWindow(display_size=(1920,1080))
        self.projector_screen = ProjectorScreen(app=self)
        self.main_screen = MainScreen(app=self)
        self.root.primary_display.add_widget(self.main_screen)
        self.root.secondary_display.add_widget(self.projector_screen)
        return self.root


ExhibitApp().run()
