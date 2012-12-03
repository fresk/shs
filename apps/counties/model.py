VS_SRC = """
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* vertex attributes */
attribute vec3     vPosition;
attribute vec2     vTexCoords0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
uniform float      opacity;


void main (void) {
  frag_color = color * vec4(1.0, 1.0, 1.0, opacity);
  tex_coord0 = vTexCoords0;
  gl_Position = projection_mat * vec4(vPosition.xyz, 1.0);
}
"""

FS_SRC =  """
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

void main (void){
    gl_FragColor = frag_color * texture2D(texture0, tex_coord0);
}
"""

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import RenderContext, Mesh
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.properties import StringProperty



class Renderer(Widget):
    fs = StringProperty(None)
    vs = StringProperty(None)

    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        super(Renderer, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

        self.vertex_format = [('vPosition', 3, 'float'), ('vTexCoords0', 2, 'float')]
        self.vertices = [
                #   X     Y      Z        S    T
                  0.0,  0.0,  -2.0,     0.0, 0.0,
                  1.0,  0.0,  -2.0,     1.0, 0.0,
                  0.0,  1.0,  -2.0,     0.0, 1.0]
        self.indices = [0,1,2]
        with self.canvas:
            self.mesh = Mesh(
                vertices=self.vertices,
                indices=self.indices,
                fmt = self.vertex_format,
                mode = 'triangles'
            )


    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('setting fragment shader failed')


    def on_vs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.vs
        shader.vs = value
        if not shader.success:
            shader.vs = old_value
            raise Exception('setting vertex shader failed')

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self.size)
        #self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['projection_mat'] = Matrix().view_clip(-1,1,-1,1, .1, 10., 0)


class RenderApp(App):
    def build(self):
        return Renderer(vs=VS_SRC, fs=FS_SRC)

RenderApp().run()
