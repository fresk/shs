from kivy.lang import Builder
from kivy.factory import Factory as F


from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.core.image import Image as CoreImage
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty
from kivy.graphics import Rectangle, Color, Canvas

class ImageButton(F.Button):
    source = StringProperty('')
    image_size = ListProperty([0,0])

    def __init__(self, **kwargs):
        self._fname_normal = ""
        self._fname_down = ""
        self._img_rect = None

        super(ImageButton, self).__init__(**kwargs)


    def on_source(self, *args):
        v = self.source.split(".")
        source_down = ''.join(v[:-1])+"_down"+v[-1]
        self._fname_normal = resource_find(self.source)
        self._fname_down = resource_find(source_down) or self._fname_normal
        self.image_size = CoreImage.load(self._fname_normal).size
        self.background_normal = self._fname_normal
        self.background_down = self._fname_down


    def on_touch_up(self, touch):
        ret = super(ImageButton,self).on_touch_up(touch)
        if ret and self.collide_point(*touch.pos):
            return True


Builder.load_string("""
<ImageButton>:
    canvas.before:
        Color:
            rgba: 1,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size

    size: self.image_size
    size_hint: None, None
""")
