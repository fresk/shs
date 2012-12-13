from kivy.lang import Builder
from kivy.factory import Factory as F


from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.core.image import Image as CoreImage
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty
from kivy.graphics import Rectangle, Color, Canvas

class ImageButton(Widget):
    state = OptionProperty('normal', options=('normal', 'down'))
    source = StringProperty('')
    image_size = ListProperty([0,0])

    def __init__(self, **kwargs):
        self._fname_normal = ""
        self._fname_down = ""
        self._img_rect = None

        self.register_event_type('on_press')
        self.register_event_type('on_release')
        self.register_event_type('on_cancel')
        self.canvas = Canvas()
        with self.canvas:
            Color(1,1,1,1)
            self._img_rect = Rectangle(pos=self.pos, size=self.size, source=self.source)
        super(ImageButton, self).__init__(**kwargs)


    def on_size(self, *args):
        if self._img_rect:
            self._img_rect.size = self.size

    def on_pos(self, *args):
        if self._img_rect:
            self._img_rect.pos = self.pos

    def on_state(self, *args):
        self._update_image_src()

    def on_source(self, *args):
        v = self.source.split(".")
        sourc_down = ''.join(v[:-1])+"_down"+v[-1]
        self._fname_normal = resource_find(self.source)
        self._fname_down = resource_find(self.source) or self._fname_normal
        self.image_size = CoreImage.load(self._fname_normal).size
        self._update_image_src()

    def _update_image_src(self):
        if self.state == "normal":
            self._img_rect.source = self._fname_normal
        else:
            self._img_rect.source = self._fname_down

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if 'button' in touch.profile and touch.button in ('scrolldown', 'scrollup'):
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True
        return self in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return self in touch.ud
        assert(self in touch.ud)
        touch.ungrab(self)
        self._do_release()
        if self.collide_point(touch.x, touch.y):
            self.dispatch('on_release')
        else:
            self.dispatch('on_cancel')

        return True

    def on_press(self):
        pass

    def on_cancel(self):
        pass

    def on_release(self):
        pass

Builder.load_string("""
<ImageButton>:
    size: self.image_size
    size_hint: None, None
""")
