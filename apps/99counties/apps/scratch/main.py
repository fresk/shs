from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory as F
from kivy.graphics import *


fs_alpha_mask = """
$HEADER$
uniform sampler2D mask;

void main (void){
    float a = texture2D(mask, tex_coord0).r;
    vec4 col = frag_color * texture2D(texture0, tex_coord0);
    gl_FragColor = col * vec4(1.0,1.0,1.0,1.0-a);
}

"""


class AlphaMaskedImage(F.Widget):
    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        self.canvas.shader.fs = fs_alpha_mask
        self.canvas.add(Callback(self.sync_matrices))
        self.canvas['mask'] = 1
        super(AlphaMaskedImage, self).__init__(**kwargs)


    def sync_matrices(self, *largs):
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['modelview_mat'] = Window.render_context['modelview_mat']


