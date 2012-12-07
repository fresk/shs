from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory as F
from kivy.graphics import *
from kivy.properties import *
import random

fs_alpha_mask = """
$HEADER$
uniform sampler2D mask;
uniform float opacity;
void main (void){
    float a = texture2D(mask, tex_coord0).r ;
    vec4 col = frag_color * texture2D(texture0, tex_coord0);
    gl_FragColor = col * vec4(1.0,1.0,1.0,1.0-a);
}

"""


class AlphaMaskedImage(F.Widget):
    mask_texture = ObjectProperty(None)
    source = StringProperty("")
    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        self.canvas.shader.fs = fs_alpha_mask
        self.canvas.add(Callback(self.sync_matrices))
        self.canvas['mask'] = 1
        self.canvas['opacity'] = 0
        super(AlphaMaskedImage, self).__init__(**kwargs)
        self.reset()

    def reset(self, *args):
        with self.canvas:
            Color(1,1,1,1)
            if self.mask_texture:
                BindTexture(index=1, texture=self.mask_texture)
                Rectangle(pos=self.pos, size=self.size, source=self.source)

    def on_mask_texture(self, *args):
        self.reset()

    def sync_matrices(self, *largs):
        self.canvas['opacity'] = self.opacity
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['modelview_mat'] = Window.render_context['modelview_mat']


class ScratchImage(AlphaMaskedImage):

    def on_touch_move(self, touch):
        with self.fbo:
            Color(1,1,1,1)
            d = 200.0
            c = touch.x - d/2., self.height - (touch.y + d/2)
            PushMatrix()
            Translate(touch.x, self.height-(touch.y), 0)
            Ellipse(pos=(-d/2.0,-d/2.0), size=(d,d), source="scratch.png")
            PopMatrix()

    def on_mask_texture(self, *args):
        pass

    def on_size(self, *args):
        self.reset()

    def reset(self, *args):
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            self.mask_texture = self.fbo.texture
            Color(1,1,1,1)
            BindTexture(index=1, texture=self.mask_texture)
            Rectangle(pos=self.pos, size=self.size, source=self.source)


