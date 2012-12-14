from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.properties import NumericProperty, ReferenceListProperty
from kivy.uix.relativelayout import RelativeLayout
from viewport import TransformLayer, Viewport


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
        self.primary_display = TransformLayer(size=self.display_size)
        self.secondary_display = TransformLayer(size=self.display_size)
        super(DualDisplayWindow, self).__init__(**kwargs)


    def add_widget(self, w, *args):
        if not isinstance(w, DualDisplayScreen):
            raise Exception("DualDisplayWindow must be DualDisplayScreen")
        if  len(self.children) == 0:
            self.primary_display = w
            return super(DualDisplayWindow, self).add_widget(w)
        if  len(self.children) == 1:
            self.secondary_display = w
            return super(DualDisplayWindow, self).add_widget(w)
        raise Exception("DualDisplayWindow can only hold two child screens")


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
        self.primary_display.pos = (0,0)

    def _set_child_size(self, child):
        self.arrange_displays()



class DualDisplayScreen(RelativeLayout):
    background = StringProperty("")


Builder.load_string("""

<DualDisplayWindow>:
    display_size: (1920,1080)


<DualDisplayScreen>:
    size: (1920,1080)
    background: 'data/img/bg.png'
    canvas.before:
        Color:
            rgba: 1,1,1,1 if self.background else 1,1,1,0
        Rectangle:
            pos: 0,0
            size: self.size
            source: self.background
""")


from kivy.animation import Animation
class TopScreen(DualDisplayScreen):
    pass


class BottomScreen(DualDisplayScreen):
    def on_parent(self, *args):
        p = self.parent
        if p:
            top = p.primary_display
            if top == self:
                return
            p.remove_widget(top)
            p.add_widget(top)
            p.secondary_display = p.top_screen = top
            p.primary_display = p.bottom_screen = self
            p.arrange_displays()


class DualDisplay(DualDisplayWindow):
    def show(self, callback=None):
        self.opacity = 0.0
        self.arrange_displays()
        anim = Animation(opacity=1.0)
        if callback:
            anim.bind(on_complete=callback)
        anim.start(self)

    def hide(self, callback=None):
        anim_top = Animation(y=self.top_screen.top, t='out_quad', d=1.0)
        anim_bottom = Animation(top=-self.bottom_screen.y, t='out_quad', d=1.0)
        if callback:
            anim_top.bind(on_complete=callback)
        anim_top.start(self.top_screen)
        anim_bottom.start(self.bottom_screen)



