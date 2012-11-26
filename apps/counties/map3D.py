from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.properties import StringProperty

from objloader import ObjFile


import random



class Renderer(Widget):
    fs = StringProperty(None)
    vs = StringProperty(None)

    def __init__(self, **kwargs):
        _vs = kwargs.pop('vs', "")
        _fs = kwargs.pop('fs', "")

        self.canvas = RenderContext()
        super(Renderer, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        self.vs = _vs
        self.fs = _fs

        Clock.schedule_interval(self.update_glsl, 1 / 60.)

        with self.canvas.before:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()

        with self.canvas:
            self.setup_scene()

        with self.canvas.after:
            PopMatrix();
            self.cb = Callback(self.reset_gl_context)


    def setup_scene(self):
        self.scene = ObjFile("map/iowa.obj")
        Translate(0,0,-2)
        Rotate(-10, 1,0,0)
        Rotate(30, 0,1,0)
        Translate(-.5,-.25, 0)
        self.meshes = {}
        self.mesh_transforms = {}
        self.start_t = {}
        for name, mesh in self.scene.objects.iteritems():
            PushMatrix()
            self.start_t[name] = random.random()
            self.mesh_transforms[name] = MatrixInstruction()
            self.meshes[name] = Mesh(
                vertices=mesh.vertices,
                indices=mesh.indices,
                fmt = mesh.vertex_format,
                mode = 'triangles'
            )
            PopMatrix()

    def setup_gl_context(self, *args):
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)


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
        self.canvas['time'] = t = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self.size)
        self.canvas['projection_mat'] = Matrix().view_clip(-.5,.5,-.5,.5, 1,100, 1)
        self.canvas['light_pos'] = [0, 0.0, 0]
        for k in self.mesh_transforms.keys():
            self.mesh_transforms[k].matrix = Matrix().scale(
                1,  1, (sin(t+t*(self.start_t[k]+1))+2)*2)

        #self.rot.angle +=1


class RenderApp(App):
    def build(self):
        return Renderer(
            vs = open("shaders/3D.vs").read(),
            fs = open("shaders/3D.fs").read()
            )
from math import sin
RenderApp().run()
