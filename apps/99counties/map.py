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
from kivy.graphics.opengl import glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE




class MapView(Widget):
    selected_county = StringProperty("")
    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.counties = App.get_running_app().counties

        self.canvas = Canvas()
        with self.canvas:
            fbo_size = self.width, self.height
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

        self.texture = self.fbo.texture
        super(CountyMap, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        self.vs = open(resource_find("data/shaders/map.vs")).read()
        self.fs = open(resource_find("data/shaders/map.fs")).read()
        self._p_render_ctx.shader.vs = open(resource_find('data/shaders/picking.vs')).read()
        self._p_render_ctx.shader.fs = open(resource_find('data/shaders/picking.fs')).read()

        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = self.size
        self.aspect_ratio  = (self.width/float(self.height)) /2.0

    def setup_gl_context(self, *args):
        self.fbo.clear_buffer()
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_glsl(self, *largs):
        self.render_ctx['time'] = t = Clock.get_boottime()
        self.render_ctx['resolution'] = map(float, self.size)
        self.render_ctx['projection_mat'] = Matrix().view_clip(-va,va,-.5,.5, .95,100, 1)
        self.render_ctx['light_pos'] = [0, 0.0, 0]
        self.cb.ask_update()
        self.render_ctx.ask_update()
        self.fbo.ask_update()
        self.canvas.ask_update()

    def setup_scene(self):
        Color(1,1,1,1)
        Translate(0,0,-2)

        for name in sorted(self.counties.keys()):
            m = self.counties[name]['mesh']
            self.meshes[name] = Mesh(
                vertices=m.vertices,
                indices=m.indices,
                fmt = m.vertex_format,
                mode = 'triangles',
                source = 'data/map/iowa_land.png'
            )









