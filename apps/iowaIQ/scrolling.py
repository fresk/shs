from kivy.clock import Clock
from kivy.factory import Factory as F
from kivy.properties import ObjectProperty, NumericProperty
from kivy.graphics.transformation import Matrix
from kivy.utils import interpolate
from kivy.animation import Animation
from kivy.loader import Loader

class PreviewImage(F.Image):
    pass

class ScrollingList(F.FloatLayout):
    drag_threshold = NumericProperty(20)
    drag_offset = NumericProperty(0)
    total_offset = NumericProperty(0)
    scroll_layer = ObjectProperty(None)
    item_list = ObjectProperty(None)
    selected = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(ScrollingList, self).__init__(**kwargs)
        self.drag_touch_id = None
        self.anim = None

    def add_image(self, s, img):
        w = F.PreviewImage(source=s)
        w.img_meta = img
        self.item_list.add_widget(w)
        Animation(opacity=1.0).start(w)


    def remove_image(self, w):
        self.item_list.remove_widget(w)
        w._coreimage.remove_from_cache()

    def clear_images(self):
        if not self.item_list:
            return
        for c in self.item_list.children[:]:
            self.item_list.remove_widget(c)

    def on_drag_offset(self, *args):
        if self.scroll_layer is None:
            return
        tox = self.total_offset
        dox = self.drag_offset
        dx, dy = self.x + tox + dox, self.y
        self.scroll_layer.transform = Matrix().translate(dx, dy, 0)

    def on_total_offset(self, *args):
        if self.scroll_layer is None:
            return
        tox = self.total_offset
        dox = self.drag_offset
        dx, dy = self.x + tox + dox, self.y
        self.scroll_layer.transform = Matrix().translate(dx, dy, 0)

    def on_touch_down(self, touch):
        if self.drag_touch_id != None:
            return False
        if self.collide_point(*touch.pos):
            if self.anim:
                Animation.cancel_all(self, 'total_offset')
                self.anim = None
            self.drag_touch_id = touch.uid
            self.velocity = 0
            touch.ud['last_x'] = touch.x
            t = (touch.time_update, touch.x)
            touch.ud['t_update'] = [t,t,t,t]
            touch.ud['move_distance'] = 0
            return True

    def on_touch_move(self, touch):
        if self.drag_touch_id == touch.uid:
            dx = touch.x - touch.ud['last_x']
            touch.ud['last_x'] = touch.x
            touch.ud['move_distance'] += abs(dx)
            t = (touch.time_update, touch.x)
            tupdate = touch.ud['t_update'][1:]
            tupdate.append(t)
            touch.ud['t_update'] = tupdate
            if touch.ud['move_distance'] > self.drag_threshold:
                self.drag_offset += dx
            return True


    def update_velocity(self, *args):
        if abs(self.velocity) < 1.0:
            self.velocity = 0

        w = self.width if self.width < 2050 else self.width -100
        min_offset = min(-0.001, 2048 - w )

        is_too_high = self.total_offset > 0.001
        is_too_low = self.total_offset < min_offset
        within_bounds = not (is_too_high or is_too_low)

        #print "offset", self.total_offset, is_too_low, is_too_high

        if self.velocity == 0 and within_bounds:
            return
        if is_too_high:
            self.total_offset = interpolate(self.total_offset, 0)
        if is_too_low:
            self.total_offset = interpolate(self.total_offset, min_offset)

        self.total_offset += self.velocity
        self.velocity = interpolate(self.velocity, 0, 15)
        Clock.schedule_once(self.update_velocity, 1.0/30.0)


    def on_touch_up(self, touch):
        if self.drag_touch_id == touch.uid:
            dx = touch.x - touch.ud['last_x']
            touch.ud['move_distance'] += abs(dx)
            if touch.ud['move_distance'] > self.drag_threshold:
                self.total_offset += self.drag_offset + dx
                self.drag_offset  = 0

                tup = touch.ud['t_update']
                dura = (tup[3][0] - tup[0][0]) * 100.0
                dist = tup[3][1] - tup[0][1]

                self.velocity = 2.5 * (dist/dura)
                Clock.schedule_once(self.update_velocity, 1.0/30.0)
            #if 'mov' in touch.profile:
            #    touch.Y
            else:
                self.drag_offset  = 0
                self.velocity = 0
                x,y = touch.x + self.total_offset, 200
                #print "select: ", x, y, "    ", touch.x, self.total_offset

                for itm in self.item_list.children:
                    if y < 50 and y > 450:
                        continue
                    if itm.x < x < itm.right:
                        self.selected = itm.img_meta
                        break
                else:
                    self.selected = None
                #idx = int(x / 8)
                #self.selected = self.item_list.children[idx]

            self.drag_touch_id = None
            return True

    def on_selected(self, *args):
        pass
