from kivy.lang import Builder
from kivy.factory import Factory as F
from kivy.properties import StringProperty, NumericProperty

class ImageButton(F.Button):
    pass

Builder.load_string("""

<ImageButton>:
    pos: self.pos
    size: btn_image.texture_size
    size_hint: None, None
    canvas:
        Clear
        Color:
            rgba: 1,1,1,1

    Image:
        pos: root.pos
        id: btn_image
        size_hint: None, None
        size: self.texture_size
        source: root.background_normal if root.state == 'normal' else root.background_down
""")
