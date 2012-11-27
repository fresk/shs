from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane
from kivy.properties import BooleanProperty


class Viewport(ScatterPlane):
    rotate_to_fit = BooleanProperty(False)

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1920, 1080))
        kwargs.setdefault('rotate_to_fit', False)
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_translation', False)
        kwargs.setdefault('do_rotation', False)
        super(Viewport, self).__init__(**kwargs)
        Window.bind(system_size=self.on_window_resize)
        self.bind(rotate_to_fit=self.on_window_resize)
        Clock.schedule_once(self.fit_to_window, -1)

    def _set_child_size(self, child):
        shx, shy = child.size_hint
        if shx:
            child.width = shx * self.width
        if shy:
            child.height = shx * self.height

    def on_window_resize(self, window, size):
        self.fit_to_window()

    def fit_to_window(self, *args):
        self.scale = Window.width / float(self.width)
        self.aspect_ratio = self.width / float(self.height)

        if self.rotate_to_fit:
            win_aspect = Window.width / float(Window.height)
            if (self.aspect_ratio * win_aspect) < 0:
                self.scale = Window.height / float(self.width)
                self.rotation = -90

        self.center = Window.center
        for c in self.children:
            self._set_child_size(c)

    def add_widget(self, w, *args, **kwargs):
        super(Viewport, self).add_widget(w, *args, **kwargs)
        self._set_child_size(w)
