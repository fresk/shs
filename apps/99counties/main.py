import os
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

<DisplayScreen>:
    canvas:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
            source: "data/img/bg.png"

[VideoBG@Video]:
    source: ctx.source
    allow_stretch: True
    options: {'eos':'loop'}
    play: True



<ProjectorScreen>:
    VideoBG:
        source: 'data/video/1920p.ogg'


<MainScreen>:
    VideoBG:
        source: 'data/video/720p.ogg'



""")

class DisplayScreen(F.FloatLayout):
    app = ObjectProperty(None)

class ProjectorScreen(DisplayScreen):
    pass

class MainScreen(DisplayScreen):
    pass

class ExhibitApp(App):
    def build(self):
        kivy.resources.resource_add_path(os.path.join(self.directory, "data"))
        self.root = DualDisplayWindow(display_size=(1920,1080))
        self.projector_screen = ProjectorScreen(app=self)
        self.main_screen = MainScreen(app=self)
        self.root.primary_display.add_widget(self.main_screen)
        self.root.secondary_display.add_widget(self.projector_screen)
        return self.root


ExhibitApp().run()
