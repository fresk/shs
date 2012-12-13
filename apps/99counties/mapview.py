import random
import json
import kivy
from kivy.app import App
from kivy.resources import resource_find
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.factory import Factory as F
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics.transformation import Matrix
from kivy.graphics.texture import *
from kivy.graphics.opengl import *
from kivy.graphics import *

from objloader import ObjFile
from math import sin, cos
from latlon import iowa_relative
from objloader import ObjFile




class MapView(Widget):
    selected_county = StringProperty("")
    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.aspect = 1.0
        self.map_model = App.get_running_app().map_model
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
        self.init_scene()
        with self.render_ctx:
            PushMatrix()
            self.render_scene()
            PopMatrix();

        self.texture = self.fbo.texture
        super(MapView, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        self.render_ctx.shader.vs = open(resource_find("data/shaders/map.vs")).read()
        self.render_ctx.shader.fs = open(resource_find('data/shaders/map.fs')).read()
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_size(self, instance, value):
        self.aspect = (self.width/float(self.height))
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = self.size
        self.update_projection()

    def setup_gl_context(self, *args):
        self.fbo.clear_buffer()
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_projection(self):
        hw = self.aspect /2.0
        self.projection_mat = Matrix().view_clip(-hw,hw,-.5,.5, .98, 100, 1)

    def update_glsl(self, *largs):
        self.render_ctx['projection_mat'] = self.projection_mat
        self.update_scene()

    def update_scene(self):
        pass

    def init_scene(self, *args):
        self.meshes = {}
        self.update_projection()

    def render_scene(self):
        PushMatrix()
        Translate(0,0,-1.1)

        bbox = self.map_model.bounds
        self.t_viewtrans = MatrixInstruction()

        Translate(-bbox.cx, -bbox.cy, -0.01)
        self.marker_canvas = Canvas()
        Translate(0,0,-bbox.zmax)
        Color(1,1,1,1)
        for name in sorted(self.counties.keys()):
            m = self.counties[name]['mesh']
            self.meshes[name] = Mesh(
                vertices=m.vertices,
                indices=m.indices,
                fmt = m.vertex_format,
                mode = 'triangles',
                source = 'data/map/iowa_land.png' )
        PopMatrix()



class InteractiveMapView(MapView):
    def __init__(self, **kwargs):
        super(InteractiveMapView, self).__init__(**kwargs)
        self.scatter = F.ScatterPlane(do_rotation=False)
        self.add_widget(self.scatter)
        self.canvas.remove(self.scatter.canvas)

    def update_scene(self):
        xpan = self.scatter.center_x - self.center_x
        ypan = self.scatter.center_y - self.center_y
        s = self.scatter.scale
        tx = xpan/float(self.height) * 1.3
        ty = ypan/float(self.height) * 1.3
        mat = Matrix().scale(s,s,s).translate(tx,ty,0)
        self.t_viewtrans.matrix = mat

    def on_size(self, instance, value):
        super(InteractiveMapView, self).on_size(instance, value)
        self.scatter.size = self.size


class MapMarker(object):
    def __init__(self, name="des moines", loc=(41.590833,-93.620833)):
        self.name = name
        self.loc = loc

class MarkerMapView(InteractiveMapView):
    def __init__(self, **kwargs):
        super(MarkerMapView, self).__init__(**kwargs)
        self.cube_mesh = ObjFile("data/map/unitcube.obj").objects.values()[0]
        self.add_marker(MapMarker())

    def add_marker(self, marker):
        with self.marker_canvas:
            m = self.cube_mesh
            mbox = self.map_model.bounds
            rx, ry = iowa_relative(marker.loc)
            rx, ry = rx*mbox.width, ry*mbox.height

            Color(1,0,0,1)
            PushMatrix()
            Translate(rx, ry, 0)
            MatrixInstruction().matrix = Matrix().scale(.01, .01, .01)
            Mesh(
                vertices=m.vertices,
                indices=m.indices,
                fmt = m.vertex_format,
                mode = 'triangles')
            PopMatrix()










