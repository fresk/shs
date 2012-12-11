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


class CountyMap(Widget):
    display = ObjectProperty(None)
    fs = StringProperty(None)
    vs = StringProperty(None)
    texture = ObjectProperty(None, allownone=True)
    p_texture = ObjectProperty(None, allownone=True)
    map_texture = StringProperty("data/map/iowa_borders.png")

    def __init__(self, **kwargs):
        _vs = kwargs.pop('vs', "")
        _fs = kwargs.pop('fs', "")

        map_obj = resource_find("data/map/iowa.obj")
        self.scene = ObjFile(map_obj)

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

        # wait that all the instructions are in the canvas to set texture
        self.texture = self.fbo.texture
        super(CountyMap, self).__init__(**kwargs)

        self._p_render_ctx.shader.vs = open(resource_find('data/shaders/picking.vs')).read()
        self._p_render_ctx.shader.fs = open(resource_find('data/shaders/picking.fs')).read()


        #must be set in right order on some gpu, or fs will fail linking
        self.vs = open(resource_find("data/shaders/map.vs")).read()
        self.fs = open(resource_find("data/shaders/map.fs")).read()
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def add_widget(self, *largs):
        # trick to attach graphics instructino to fbo instead of canvas
        canvas = self.canvas
        self.canvas = self.render_ctx
        ret = super(CountyMap, self).add_widget(*largs)
        self.canvas = canvas
        return ret

    def remove_widget(self, *largs):
        canvas = self.canvas
        self.canvas = self.render_ctx
        super(CountyMap, self).remove_widget(*largs)
        self.canvas = canvas

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
        self._p_fbo_rect.pos = self.x, -self.height

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_p_texture(self, instance, value):
        self._p_fbo_rect.texture = value

    def mesh2county(self, meshname):
        v = meshname.split("_")
        if len(v) == 3:
            return v[1]
        else:
            return v[1]+"_"+v[2]

    def get_pixel(self, x, y):
         self._p_fbo.bind()
         pixel = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
         self._p_fbo.release()
         return map(ord, pixel)

    def on_touch_down(self, touch):
        x,y = touch.pos
        p = self.get_pixel(x,y)
        #r = p & 0xFF0000
        #r = p & 0xFFFF00
        #r = p & 0x0000FF
        #print "p:", p, r,g,b
        f_close = lambda a,l:min(l,key=lambda x:abs(x-a))
        k = f_close(p[0], self.picking_colors.keys())
        self.display.selected_county = self.picking_colors.get(k, "")

    def setup_scene(self):
        normal_txt = resource_find('data/map/iowa_tex.png')
        map_txt = resource_find(self.map_texture)

        Translate(0,-.12,-2)

        self.rot = Rotate(0, 0,1,0) # tilt
        Rotate(-0, 0,1,0) # tilt
        self.roty = Rotate(0,1,0,0)
        Rotate(0, 1,0,0) # tilt
        Scale(1.8)
        Translate(-.5,-.25, 0.05)
        self.meshes = {}
        self.mesh_transforms = {}
        Color(1,1,1,1)
        self.picking_colors = {}
        c = 0.0 #f=lambda a,l:min(l,key=lambda x:abs(x-a))
        for name in sorted(self.scene.objects.keys()):
            mesh = self.scene.objects[name]
            self.tex_binding_1 = BindTexture(source=self.map_texture, index=1)
            self.render_ctx['texture1'] = 1
            PushMatrix()
            self.mesh_transforms[name] = MatrixInstruction()
            Color(1,1,1,1)
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
        Rotate(-0, 0,1,0) # tilt
        self._p_roty = Rotate(0,1,0,0)
        Rotate(0, 1,0,0) # tilt
        Scale(1.8)
        Translate(-.5,-.25, 0.05)
        self._p_meshes = {}
        self._p_mesh_transforms = {}
        Color(1,1,1,1)
        self.picking_colors = {}
        c = 0.0 #f=lambda a,l:min(l,key=lambda x:abs(x-a))
        for name in sorted(self.scene.objects.keys()):
            mesh = self.scene.objects[name]
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
            self.picking_colors[int(c*255)] = self.mesh2county(name)
            c += 1.0/len(self.scene.objects)
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
        self.render_ctx['time'] = t = Clock.get_boottime()
        self.render_ctx['resolution'] = map(float, self.size)
        self.render_ctx['projection_mat'] = Matrix().view_clip(-.5,.5,-.5,.5, .95,100, 1)
        self.render_ctx['light_pos'] = [0, 0.0, 0]
        self.cb.ask_update()
        self.render_ctx.ask_update()
        self.fbo.ask_update()
        #self.rot.angle = sin(t*0.12)*cos(t*0.22)*20
        #self.roty.angle = cos(sin(t*0.23))*15

        self._p_render_ctx['time'] = t = Clock.get_boottime()
        self._p_render_ctx['resolution'] = map(float, self.size)
        self._p_render_ctx['projection_mat'] = Matrix().view_clip(-.5,.5,-.5,.5, .95,100, 1)
        self._p_render_ctx['light_pos'] = [0, 0.0, 0]
        self._p_cb.ask_update()
        self._p_render_ctx.ask_update()
        self._p_fbo.ask_update()
        #self._p_rot.angle = sin(t*0.12)*cos(t*0.22)*20
        #self._p_roty.angle = cos(sin(t*0.23))*15
        self.canvas.ask_update()





