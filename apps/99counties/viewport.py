from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane
from kivy.properties import NumericProperty, ObjectProperty
from kivy.properties import ReferenceListProperty


class TransformLayer(ScatterPlane):
    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1920, 1080))
        kwargs.setdefault('rotate_to_fit', False)
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_translation', False)
        kwargs.setdefault('do_rotation', False)
        super(TransformLayer, self).__init__(**kwargs)

    def on_size(self, *args):
        for w in self.children:
            self._set_child_size(w)

    def add_widget(self, w, *args, **kwargs):
        super(TransformLayer, self).add_widget(w, *args, **kwargs)
        self._set_child_size(w)

    def _set_child_size(self, child):
        shx, shy = child.size_hint
        if shx:
            child.width = shx * self.width
        if shy:
            child.height = shx * self.height


class Viewport(TransformLayer):
    aspect_ratio = NumericProperty(1.0)
    '''Aspect ratio of the layer (width/height).

    :data:`aspect_ratio` is a :class:`~kivy.properties.NumericProperty`,
    default to 1.0.
    '''

    window_aspect_ratio = NumericProperty(1.0)
    '''Aspect ratio of the Window.

    :data:`window_aspect_ratio` is a :class:`~kivy.properties.NumericProperty`,
    default to 1.0.
    '''

    def __init__(self, **kwargs):
        super(Viewport, self).__init__(**kwargs)
        Window.bind(system_size=self.on_window_resize)
        Clock.schedule_once(self.fit_to_window, -1)

    def on_window_resize(self, window, size):
        self.fit_to_window()

    def on_size(self, *args):
        self.fit_to_window()

    def fit_to_window(self, *args):
        self.aspect_ratio = self.width / float(self.height)
        self.window_aspect_ratio = Window.width / float(Window.height)

        if self.aspect_ratio > self.window_aspect_ratio:
            self.scale = Window.width / float(self.width)
        else:
            self.scale = Window.height / float(self.height)

        self.center = Window.center
        for c in self.children:
            self._set_child_size(c)


class DualDisplayWindow(Viewport):
    primary_display = ObjectProperty()
    ''' The Primary Display  (pos is 0,0)'''

    secondary_display = ObjectProperty()
    ''' The Secondary Display  (wither on top or to the right based
    on aspect ratio of Window '''

    display_width = NumericProperty(1920)
    '''Width of the individual Displays.

    :data:`display_width` is a :class:`~kivy.properties.NumericProperty`,
    default to 1920.
    '''

    display_height = NumericProperty(1080)
    '''Height of the individual Displays.

    :data:`display_height` is a :class:`~kivy.properties.NumericProperty`,
    default to 1080.
    '''

    display_size = ReferenceListProperty(display_width, display_height)
    '''Size of the individual Displays.

    :data:`display_size` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:data:`width`, :data:`height`) properties.
    '''

    def __init__(self, **kwargs):
        self.primary_display = Layer(size=self.display_size)
        self.secondary_display = Layer(size=self.display_size)
        super(DualDisplayWindow, self).__init__(**kwargs)
        self.add_widget(self.primary_display)
        self.add_widget(self.secondary_display)

    def on_display_size(self, *args):
        self.primary_display.size = self.display_size
        self.secondary_display.size = self.display_size
        self.arrange_displays()

    def arrange_displays(self):
        if self.window_aspect_ratio > 1.0:
            self.size = self.display_width*2, self.display_height
            self.secondary_display.pos = (self.primary_display.width, 0)
        else:
            self.size = self.display_width, self.display_height*2
            self.secondary_display.pos = (0, self.primary_display.height)

    def _set_child_size(self, child):
        self.arrange_displays()
