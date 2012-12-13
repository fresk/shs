from kivy.clock import Clock
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.factory import Factory as F
from kivy.animation import Animation
from kivy.graphics import *
from kivy.properties import *
from functools import partial
from imagebutton import ImageButton
from viewport import TransformLayer
from dualdisplay import BottomScreen, DualDisplay
from exhibit import BackToMenuButton
from kivy.app import App
import json
import random
from math import sqrt

fs_alpha_mask = """
$HEADER$
uniform sampler2D mask;
uniform float opacity;
void main (void){
    float a = texture2D(mask, tex_coord0).r ;
    vec4 col = frag_color * texture2D(texture0, tex_coord0);
    gl_FragColor = col * vec4(1.0,1.0,1.0,1.0-a * opacity);
}

"""


MASK = None


def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
    if dist < steps:
        return None
    o = []
    m = dist / steps
    for i in xrange(1, int(m)):
        mi = i / m
        lastx = x1 + dx * mi
        lasty = y1 + dy * mi
        o.append([lastx, lasty])
    return o



class AlphaMaskedImage(F.Widget):
    mask_texture = ObjectProperty(None)
    source = StringProperty("")
    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        self.canvas.shader.fs = fs_alpha_mask
        self.canvas.add(Callback(self.sync_matrices))
        self.canvas['mask'] = 1
        self.canvas['opacity'] = 1
        super(AlphaMaskedImage, self).__init__(**kwargs)
        self.reset()

    def reset(self, *args):
        with self.canvas:
            Color(1,1,1,1)
            if self.mask_texture:
                BindTexture(index=1, texture=self.mask_texture)
                Rectangle(pos=self.pos, size=self.size, source=self.source)

    def on_mask_texture(self, *args):
        self.reset()

    def sync_matrices(self, *largs):
        self.canvas['opacity'] = self.opacity
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['modelview_mat'] = Window.render_context['modelview_mat']


class ScratchImage(AlphaMaskedImage):
    display = ObjectProperty(None)

    def on_touch_down(self, touch):
        if self.display.top_mask:
            self.display.top_mask.mask_texture = self.mask_texture
        self.ox, self.oy = touch.pos
        touch.ud['old_pos']  = touch.pos
        self.paint_scratch(touch)

    def on_touch_move(self, touch):
        touch.ud['old_pos']  = touch.ud.get('old_pos', touch.pos)
        self.paint_scratch(touch)
        touch.ud['old_pos']  = touch.pos

    def on_touch_up(self, touch):
        touch.ud['old_pos']  = touch.ud.get('old_pos', touch.pos)
        self.paint_scratch(touch)
        self.fbo.remove_group(str(touch.id))


    def paint_scratch(self, touch):
        x,y = touch.pos
        ox,oy = touch.ud['old_pos']
        d = 200.0
        point_list = calculate_points(ox, oy, x,y)
        if not point_list:
            point_list = [touch.pos]
        self.fbo.remove_group(str(touch.id))
        with self.fbo:
            for p in point_list:
                #Ellipse(pos=p, size=(d,d), source="scratch.png", group=touch.id)
                pos = (p[0]-d/2.0,  self.height - p[1]-d/2.0)
                Rectangle(pos=pos, size=(d,d), group=str(touch.id), source='apps/scratch/scratch.png')



    def on_mask_texture(self, *args):
        pass


    def on_size(self, *args):
        self.reset()

    def reset(self, *args):
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            self.mask_texture = self.fbo.texture
            Color(1,1,1,1)
            BindTexture(index=1, texture=self.mask_texture)
            Rectangle(pos=self.pos, size=self.size, source=self.source)

        with self.fbo:
            Color(1,1,1,1)
        Clock.schedule_once(self.update_mask)

    def update_mask(self, *args):
        if self.display.top_mask:
            self.display.top_mask.mask_texture = self.mask_texture



class ScratchBackButton(ImageButton):
    display = ObjectProperty(None)


class ScratchDualDisplay(DualDisplay):
    menu = ObjectProperty(None)
    top_mask = ObjectProperty(None)
    scratch_img = ObjectProperty(None)
    fact_img = StringProperty("")
    present_img = StringProperty("")
    historic_img = StringProperty("")
    transitioning = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.transitioning:
            return True
        super(ScratchDualDisplay, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.transitioning:
            return True
        super(ScratchDualDisplay, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.transitioning:
            return True
        super(ScratchDualDisplay, self).on_touch_up(touch)

    def start_scratch(self, item, *args):
        if self.transitioning:
            return
        self.transitioning = True
        self.data = item
        self.fact_img = resource_find(self.data['img_facts'])
        self.present_img = resource_find(self.data['img_present'])
        self.historic_img = resource_find(self.data['img_historic'])

        transition_img_top = F.Image(source="apps/scratch/black.jpg", opacity=0.0)
        self.top_screen.add_widget(transition_img_top)
        Animation(opacity=1.0).start(transition_img_top)

        transition_img = F.Image(source=self.historic_img, opacity=0.0)
        self.bottom_screen.add_widget(transition_img)
        anim = Animation(opacity=1.0)
        anim.bind(on_complete=self.show_done)
        anim.start(transition_img)

    def show_done(self, *args):
        self.bottom_screen.content.clear_widgets()
        self.top_screen.content.clear_widgets()

        image_now = F.Image(source=self.present_img)
        self.scratch_img = ScratchImage(source=self.historic_img, display=self)
        self.bottom_screen.add_widget(image_now)
        self.bottom_screen.add_widget(self.scratch_img)

        image_fact = F.Image(source=self.fact_img)
        self.top_mask = AlphaMaskedImage(source='apps/scratch/black.jpg')
        self.img_top = F.Image(source="apps/scratch/black.jpg", opacity=1.0)
        self.top_screen.add_widget(image_fact)
        self.top_screen.add_widget(self.top_mask)
        self.top_screen.add_widget(self.img_top)

        Clock.schedule_once(self.scratch_img.update_mask)
        Clock.schedule_once(self.remove_black, 0.2)
        back_btn = ScratchBackButton(display=self)
        self.bottom_screen.add_widget(back_btn)


    def remove_black(self, *args):
        self.top_screen.content.remove_widget(self.img_top)
        self.img_top = None
        self.top_mask.mask_texture = self.scratch_img.mask_texture
        self.transitioning = False

    def show_menu(self, *args):
        if self.transitioning:
            return
        self.transitioning = True
        for c in self.bottom_screen.content.children:
            Animation(opacity=0.0).start(c)
        for c in self.top_screen.content.children:
            Animation(opacity=0.0).start(c)

        self.bottom_screen.add_widget(self.menu)
        self.menu.opacity = 0.0
        anim = Animation(opacity=1.0)
        anim.bind(on_complete=self.menu_done)
        anim.start(self.menu)

    def menu_done(self, *args):
        self.bottom_screen.content.clear_widgets()
        self.top_screen.content.clear_widgets()
        self.bottom_screen.add_widget(self.menu)
        self.bottom_screen.add_widget(BackToMenuButton())
        self.transitioning = False






class HistoryScratchMenu(F.StackLayout):
    screen = ObjectProperty(None)
    display = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(HistoryScratchMenu, self).__init__(**kwargs)
        self.data = App.get_running_app().scratches
        for item in self.data:
            btn = ImageButton(source=item['img_thumb'])
            btn.bind(on_release=partial(self.select_scratch, item))
            self.add_widget(btn)

    def select_scratch(self, item, *args):
        self.display.start_scratch(item)




