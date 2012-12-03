from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from viewport import DualDisplayWindow


class DualDisplayScreen(FloatLayout):
    app = ObjectProperty(None)
    background = StringProperty("")


class TopScreen(DualDisplayScreen):
    pass


class BottomScreen(DualDisplayScreen):
    pass


class DualDisplay(DualDisplayWindow):
    app = ObjectProperty(None)
    alpha_hide = NumericProperty(0.0)
    alpha_show = NumericProperty(1.0)



Builder.load_string("""

<DualDisplayWindow>:
    display_size: (1920,1080)


<DualDisplayScreen>:
    size: (1920,1080)
    background: 'data/img/bg.png'
    canvas:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
            source: self.background
""")
