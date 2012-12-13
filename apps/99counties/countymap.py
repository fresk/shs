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

class CountyModel(Widget):
    display = ObjectProperty(None)
    selected_county = StringProperty("polk")
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
        super(CountyModel, self).__init__(**kwargs)
        _vs = open('data/shaders/county.vs', 'r').read()
        _fs = open('data/shaders/county.fs', 'r').read()
        self.render_ctx.shader.vs = _vs
        self.render_ctx.shader.fs = _fs
        Clock.schedule_interval(self.update_glsl, 1/30.0)

    def setup_scene(self):
        PushMatrix()
        Color(1,1,1,1)
        mesh = self.counties['des_moines']['mesh']
        cx, cy, cz = mesh.bounds.center

        Translate(0,0,-3)
        self.rot2 = Rotate(0, 1,0,0)
        self.rot = Rotate(0, 0,1,0)
        Rotate(0, 1,0,0)
        self.mi = MatrixInstruction()
        self.trans = Translate(-cx, -cy, 0)
        self.mesh = Mesh(
            vertices=mesh.vertices,
            indices=mesh.indices,
            fmt = mesh.vertex_format,
            mode = 'triangles',
            source = "data/map/iowa_land.png"
        )
        PopMatrix()

    def on_selected_county(self, *args):
        county = self.counties.get(self.selected_county, self.counties['polk'])
        m = county['mesh']
        self.mesh.vertices = m.vertices
        self.mesh.indices = m.indices
        cx,cy,cz = m.bounds.center
        self.trans.x = -cx
        self.trans.y = -cy


    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = self.size
        self.pos = self.pos

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value


    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def setup_gl_context(self, *args):
        self.fbo.clear_buffer()
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)


    def update_glsl(self, *largs):
        va = (self.width/float(self.height)) /2.0
        self.render_ctx['time'] = t = Clock.get_boottime()
        self.render_ctx['resolution'] = map(float, self.size)
        self.render_ctx['projection_mat'] = Matrix().view_clip(-va,va,-.5,.5, .95,100, 1)
        self.render_ctx['light_pos'] = [0, 0.0, 0]
        self.rot.angle = sin(t*0.5)* 15.0
        self.rot2.angle = sin(t*0.3)* 9.0
        self.mi.matrix = Matrix().scale(5,5,1).scale(6,6,6)
        self.cb.ask_update()
        self.render_ctx.ask_update()
        self.fbo.ask_update()
        self.canvas.ask_update()




class CountyMap(Widget):
    display = ObjectProperty(None)
    selected_county = StringProperty("")
    fs = StringProperty(None)
    vs = StringProperty(None)
    texture = ObjectProperty(None, allownone=True)
    p_texture = ObjectProperty(None, allownone=True)
    map_texture = StringProperty("data/map/iowa_wiki.png")

    def __init__(self, **kwargs):
        _vs = kwargs.pop('vs', "")
        _fs = kwargs.pop('fs', "")

        self.counties = App.get_running_app().counties

        self.canvas = Canvas()
        with self.canvas:
            fbo_size = self.width, self.height
            self.fbo = Fbo(size=fbo_size, with_depthbuffer=True, do_clear=True)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()
            self._p_fbo = Fbo(size=fbo_size, with_depthbuffer=True, do_clear=True)
            self._p_fbo_color = Color(1, 1, 1, 1)
            self._p_fbo_rect = Rectangle()

        with self.fbo:
            self.cb = Callback(self.setup_gl_context)
            self.render_ctx = RenderContext()
            self.cb2 = Callback(self.reset_gl_context)

        with self._p_fbo:
            self._p_cb = Callback(self.setup_gl_context)
            self._p_render_ctx = RenderContext()
            self._p_cb2 = Callback(self.reset_gl_context)

        with self.render_ctx:
            PushMatrix()
            self.setup_scene()
            PopMatrix();

        with self._p_render_ctx:
            PushMatrix()
            self.setup_scene_picking()
            PopMatrix();

        self.texture = self.fbo.texture
        super(CountyMap, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        self.vs = open(resource_find("data/shaders/map.vs")).read()
        self.fs = open(resource_find("data/shaders/map.fs")).read()
        self._p_render_ctx.shader.vs = open(resource_find('data/shaders/picking.vs')).read()
        self._p_render_ctx.shader.fs = open(resource_find('data/shaders/picking.fs')).read()

        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def on_size(self, instance, value):
        self.fbo.size = value
        self._p_fbo.size = value
        self.texture = self.fbo.texture
        self.p_texture = self._p_fbo.texture
        self.fbo_rect.size = self.size
        self._p_fbo_rect.size = self.size
        self._p_fbo_rect.pos = self.x,-self.height

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value
        self._p_fbo_rect.pos = self.x, self.height

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_p_texture(self, instance, value):
        self._p_fbo_rect.texture = value

    def get_pixel(self, x, y):
         self._p_fbo.bind()
         pixel = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
         self._p_fbo.release()
         return map(ord, pixel)

    def on_touch_down(self, touch):
        x,y = touch.pos
        p = self.get_pixel(x,y)
        f_close = lambda a,l:min(l,key=lambda x:abs(x-a))
        k = f_close(p[0], self.picking_colors.keys())
        App.get_running_app().selected_county = self.picking_colors.get(k, "")

    def on_selected_county(self, *args):
        for k in self.mesh_colors.keys():
            self.mesh_colors[k].rgba = (1,1,1,1)
        if self.mesh_colors.get(self.selected_county):
            self.mesh_colors[self.selected_county].rgba = (1,0,0,1)

    def setup_scene(self):
        normal_txt = resource_find('data/map/iowa_tex.png')
        map_txt = resource_find(self.map_texture)

        Translate(0,-.12,-2)

        self.rot = Rotate(0, 0,1,0) # tilt
        self.roty = Rotate(0,1,0,0)
        Scale(1.8)
        Translate(-.5,-.25, 0.05)
        self.meshes = {}
        self.mesh_transforms = {}
        self.mesh_colors = {}
        Color(1,1,1,1)
        self.picking_colors = {}
        c = 0.0 #f=lambda a,l:min(l,key=lambda x:abs(x-a))
        for name in sorted(self.counties.keys()):
            mesh = self.counties[name]['mesh']
            self.tex_binding_1 = BindTexture(source=self.map_texture, index=1)
            self.render_ctx['texture1'] = 1
            PushMatrix()
            self.mesh_transforms[name] = MatrixInstruction()
            self.mesh_colors[name] = Color(1,1,1,1)
            self.meshes[name] = Mesh(
                vertices=mesh.vertices,
                indices=mesh.indices,
                fmt = mesh.vertex_format,
                mode = 'triangles',
                source = normal_txt
            )
            Color(1,1,1,1)
            PopMatrix()



    def setup_scene_picking(self):
        Translate(0,-.12,-2)
        self._p_rot = Rotate(0, 0,1,0) # tilt
        self._p_roty = Rotate(0,1,0,0)
        Rotate(0, 1,0,0) # tilt
        Scale(1.8)
        Translate(-.5,-.25, 0.05)
        self._p_meshes = {}
        self._p_mesh_transforms = {}
        Color(1,1,1,1)
        self.picking_colors = {}
        c = 0.0 #f=lambda a,l:min(l,key=lambda x:abs(x-a))
        for name in sorted(self.counties.keys()):
            mesh = self.counties[name]['mesh']
            Color(c,c,1,1)
            PushMatrix()
            self._p_mesh_transforms[name] = MatrixInstruction()
            self._p_meshes[name] = Mesh(
                vertices=mesh.vertices,
                indices=mesh.indices,
                fmt = mesh.vertex_format,
                mode = 'triangles',
            )
            PopMatrix()
            self.picking_colors[int(c*255)] = name
            c += 1.0/len(self.counties)
        Color(1,1,1,1)

    def setup_gl_context(self, *args):
        self.fbo.clear_buffer()
        self._p_fbo.clear_buffer()
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)


    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        self.render_ctx.shader.fs = value


    def on_vs(self, instance, value):
        # set the fragment shader to our source code
        self.render_ctx.shader.vs = value

    def on_map_texture(self, *args):
        src = resource_find(self.map_texture)
        self.tex_binding1.source = src

    def update_glsl(self, *largs):
        va = (self.width/float(self.height)) /2.0
        self.render_ctx['time'] = t = Clock.get_boottime()
        self.render_ctx['resolution'] = map(float, self.size)
        self.render_ctx['projection_mat'] = Matrix().view_clip(-va,va,-.5,.5, .95,100, 1)
        self.render_ctx['light_pos'] = [0, 0.0, 0]

        for k in self.mesh_colors.keys():
            self.mesh_colors[k].rgba = (1,1,1,1)
        if self.mesh_colors.get(self.selected_county):
            self.mesh_colors[self.selected_county].rgba = (1,0,0,1)

        self.cb.ask_update()
        self.render_ctx.ask_update()
        self.fbo.ask_update()
        #self.rot.angle = sin(t*0.12)*cos(t*0.22)*20
        #self.roty.angle = cos(sin(t*0.23))*15

        self._p_render_ctx['time'] = t = Clock.get_boottime()
        self._p_render_ctx['resolution'] = map(float, self.size)
        self._p_render_ctx['projection_mat'] = Matrix().view_clip(-va,va,-.5,.5, .95,100, 1)
        self._p_render_ctx['light_pos'] = [0, 0.0, 0]
        self._p_cb.ask_update()
        self._p_render_ctx.ask_update()
        self._p_fbo.ask_update()

        #self._p_rot.angle = sin(t*0.12)*cos(t*0.22)*20
        #self._p_roty.angle = cos(sin(t*0.23))*15
        self.canvas.ask_update()





