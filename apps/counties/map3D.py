from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.properties import StringProperty

from objloader import OBJ


class Renderer(Widget):
    fs = StringProperty(None)
    vs = StringProperty(None)

    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        super(Renderer, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

        self.model = OBJ("map/iowa.obj")

        self.vertex_format = [
            ('v_pos', 3, 'float'),
            ('v_normal', 3, 'float'),
            ('v_tc0', 2, 'float')]

        self.vertices = []
        self.indices = []
        idx = 0
        for f in self.model.faces:
            verts =  f[0]
            norms = f[1]
            for i in range(3):
                v = self.model.vertices[verts[i]-1]
                n = self.model.normals[norms[i]-1]
                data = [v[0], v[1], v[2], n[0], n[1], n[2], 0.0,0.0]
                self.vertices.extend(data)
            tri = [idx, idx+1, idx+2]
            self.indices.extend(tri)
            idx += 3


        with self.canvas:
            self.cb = Callback(self.gl_callback)
            PushMatrix()
            Translate(-0,0,-7.0)
            self.rot = Rotate(10.0, 0.0, 1.0, 0.0)
            self.rot2 = Rotate(70.0, 1.0, 0.0, 0.0)

            self.mesh = Mesh(
                vertices=self.vertices,
                indices=self.indices,
                fmt = self.vertex_format,
                mode = 'triangles'
            )

            PopMatrix();


    def gl_callback(self, *args):
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)



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
        self.canvas['projection_mat'] = Matrix().view_clip(-1,1,-1,1, 1,100, 1)
        self.canvas['light_pos'] = [0, 0.0, 0]
        self.rot.angle +=1

class RenderApp(App):
    def build(self):
        return Renderer(
            vs = open('shaders/3D.vs', 'r').read(),
            fs = open('shaders/3D.fs', 'r').read()
        )

RenderApp().run()
