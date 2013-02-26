from glob import glob
from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.uix.image import AsyncImage
from kivy.lang import Builder
from kivy.factory import Factory as F
import gc
import pdb
import objgraph

kv_source = """
FloatLayout:
    Button:
        text: "next"
        on_release: app.next_image()
"""


class TestApp(App):
    def build(self):
        self.files = glob("resources/*_large.jpg")
        self.image = F.AsyncImage(source=self.files[0])
        self.root = Builder.load_string(kv_source)
        self.root.add_widget(self.image)

    def next_image(self):
        f = self.files.pop(0)
        self.files.append(f)


        print "popped:", f
        self.image._coreimage.remove_from_cache()
        self.image.source = self.files[0]
        print "set source:", self.files[0]


TestApp().run()

