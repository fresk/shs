from kivy.app import App
from kivy.resources import resource_find
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.graphics.texture import *
from kivy.properties import StringProperty, ObjectProperty
from objloader import ObjFile
import random
import json
from math import sin, cos


class Renderer(Widget):
    fs = StringProperty(None)
    vs = StringProperty(None)
    texture = ObjectProperty(None, allownone=True)
    map_texture = StringProperty("map/iowa_borders.png")
    slider_val = StringProperty("1900")

    def __init__(self, **kwargs):
        _vs = kwargs.pop('vs', "")
        _fs = kwargs.pop('fs', "")

        self.canvas = Canvas()
        with self.canvas:
            fbo_size = self.width*2, self.height*2
            self.fbo = Fbo(size=fbo_size, with_depthbuffer=True, do_clear=True)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()

        with self.fbo:
            self.cb = Callback(self.setup_gl_context)
            self.render_ctx = RenderContext()
            self.cb2 = Callback(self.reset_gl_context)


        with self.render_ctx:
            PushMatrix()
            self.setup_scene()
            PopMatrix();


        # wait that all the instructions are in the canvas to set texture
        self.texture = self.fbo.texture
        super(Renderer, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        self.vs = open(resource_find("shaders/3D.vs")).read()
        self.fs = open(resource_find("shaders/3D.fs")).read()
        self.population_data = json.load(open(resource_find('data/county_population.json'), 'r'))


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


    def setup_scene(self):
        map_obj = resource_find("map/iowa.obj")
        normal_txt = resource_find('map/iowa_tex.png')
        map_txt = resource_find(self.map_texture)
        self.scene = ObjFile(map_obj)

        Translate(0,-.12,-2)

        self.rot = Rotate(0, 0,1,0) # tilt
        Rotate(-0, 0,1,0) # tilt
        self.roty = Rotate(0,1,0,0)
        Rotate(-30, 1,0,0) # tilt
        Scale(1.8)
        Translate(-.5,-.25, 0.05)
        self.meshes = {}
        self.mesh_transforms = {}
        self.start_t = {}
        Color(1,1,1,1)
        for name, mesh in self.scene.objects.iteritems():
            self.tex_binding_1 = BindTexture(source=self.map_texture, index=1)
            self.render_ctx['texture1'] = 1

            PushMatrix()
            self.start_t[name] = 1.0# random.random()
            self.mesh_transforms[name] = MatrixInstruction()
            self.meshes[name] = Mesh(
                vertices=mesh.vertices,
                indices=mesh.indices,
                fmt = mesh.vertex_format,
                mode = 'triangles',
                source = normal_txt
            )
            Color(1,1,1,1)
            PopMatrix()

    def setup_gl_context(self, *args):
        self.fbo.clear_buffer()
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

    def on_map_texture(self, *args):
        src = resource_find(self.map_texture)
        self.tex_binding1.source = src

    def update_glsl(self, *largs):
        self.render_ctx['time'] = t = Clock.get_boottime()
        self.render_ctx['resolution'] = map(float, self.size)
        self.render_ctx['projection_mat'] = Matrix().view_clip(-.5,.5,-.5,.5, .95,100, 1)
        self.render_ctx['light_pos'] = [0, 0.0, 0]
        for k in self.mesh_transforms.keys():
            parts = k.split("_")
            county = parts[1]
            if len(parts) > 3:
                county += "_" +parts[2]

            pop = self.population_data[county][self.slider_val]
            #v = t+t*(self.start_t[k]+1)
            #v = (sin(v)*cos(v)+2)
            v = pop / 100000.0 + 0.5
            self.mesh_transforms[k].matrix = Matrix().scale(1,  1, v)
        self.cb.ask_update()
        self.render_ctx.ask_update()
        self.fbo.ask_update()
        self.canvas.ask_update()
        self.rot.angle = sin(t*0.12)*cos(t*0.22)*20
        self.roty.angle = cos(sin(t*0.23))*15




