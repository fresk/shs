from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.properties import StringProperty, ObjectProperty
from objloader import ObjFile
import random



class Renderer(Widget):
    fs = StringProperty(None)
    vs = StringProperty(None)
    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        _vs = kwargs.pop('vs', "")
        _fs = kwargs.pop('fs', "")

        self.canvas = Canvas()
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()

        with self.fbo:
            self.render_ctx = RenderContext()

        with self.render_ctx.before:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()

        with self.render_ctx:
            self.setup_scene()

        with self.render_ctx.after:
            PopMatrix();
            self.cb = Callback(self.reset_gl_context)

        # wait that all the instructions are in the canvas to set texture
        self.texture = self.fbo.texture
        super(Renderer, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        Clock.schedule_once(self.load_shaders, 0.1)
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def add_widget(self, *largs):
        # trick to attach graphics instructino to fbo instead of canvas
        canvas = self.canvas
        self.canvas = self.render_ctx
        ret = super(Renderer, self).add_widget(*largs)
        self.canvas = canvas
        return ret

    def remove_widget(self, *largs):
        canvas = self.canvas
        self.canvas = self.render_ctx
        super(Renderer, self).remove_widget(*largs)
        self.canvas = canvas

    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def load_shaders(self, *args):
        self.vs = open("/Users/tehansen/code/shs/apps/99counties/shaders/3D.vs").read()
        self.fs = open("/Users/tehansen/code/shs/apps/99counties/shaders/3D.fs").read()

    def setup_scene(self):

        self.scene = ObjFile("map/iowa.obj")
        Translate(0,0,-2)

        Rotate(-20, 0,1,0) # tilt
        Rotate(-45, 1,0,0) # tilt
        Scale(2,2,2)
        Translate(-.5,-.25, 0.05)
        self.meshes = {}
        self.mesh_transforms = {}
        self.start_t = {}
        for name, mesh in self.scene.objects.iteritems():
            BindTexture(source='map/iowa_land.png', index=1)
            self.render_ctx['iowa_tex'] = 1

            PushMatrix()
            self.start_t[name] = 1.0# random.random()
            if "polk" in name:
                print "POLK", name
                self.start_t[name] = 4.0
                Color(1.0,.7,.4,1)
            #elif random.random() < .8:
            #    self.start_t[name] *= .5

            self.mesh_transforms[name] = MatrixInstruction()
            self.meshes[name] = Mesh(
                vertices=mesh.vertices,
                indices=mesh.indices,
                fmt = mesh.vertex_format,
                mode = 'triangles',
                source = "map/iowa_normal.png"
            )
            Color(1,1,1,1)
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
        shader = self.render_ctx.shader
        old_value = shader.fs
        shader.fs = value


    def on_vs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.render_ctx.shader
        old_value = shader.vs
        shader.vs = value

    def update_glsl(self, *largs):
        self.render_ctx['time'] = t = Clock.get_boottime()
        self.render_ctx['resolution'] = map(float, self.size)
        self.render_ctx['projection_mat'] = Matrix().view_clip(-.5,.5,-.5,.5, 1,100, 1)
        self.render_ctx['light_pos'] = [0, 0.0, 0]
        for k in self.mesh_transforms.keys():
            #v = t+t*(self.start_t[k]+1)
            #v = (sin(v)*cos(v)+2)
            v = self.start_t[k] + 1.0
            self.mesh_transforms[k].matrix = Matrix().scale(1,  1, v)

        #self.rot.angle +=1

