import random
import json
import urllib
from jsondata import JsonData


from os import makedirs
from os.path import join, exists, expanduser
from functools import partial
from kivy.app import App
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.listview import ListView
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.screenmanager import *
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Fbo, Canvas, Color, Quad, Translate
from kivy.properties import (
    BooleanProperty, NumericProperty, StringProperty, ObjectProperty,
    ListProperty, DictProperty, AliasProperty, OptionProperty)

from math import sin, pi
from viewport import Viewport

class StringIndex(object):
    def __init__(self, str_list):
        records = [s.strip() for s in str_list]
        self.index = self.create_index(records)

    def create_index(self, items, level=0):
        if len(items) < 10 or level>10:
            return items

        lookup = {}
        for i in items:
            k = ''
            if len(i) > level:
                k = i[level].lower()
            lookup[k] = lookup.get(k) or []
            lookup[k].append(i)

        for idx in lookup.keys():
            lookup[idx] = self.create_index(lookup[idx], level+1)
        return lookup

    def find_all(self, root):
        matches = []
        for k in root.keys():
            sub = root[k]
            if type(sub) == type([]):
                matches.extend(sub)
            else:
                matches.extend(self.find_all(sub))
        return matches

    def find_prefix(self, prefix):
        root = self.index
        for c in prefix.lower():
            root = root.get(c, [])
            if type(root) == type([]):
                return root
        return self.find_all(root)


class CompletionButton(Button):
    data = DictProperty()

class CompletionLabel(Label):
    pass

class CustomTextInput(Label):
    rawtext = StringProperty()
    data = DictProperty({})
    _keyboard = ObjectProperty(allownone=True)
    autocomplete_source = StringProperty()
    autocomplete_placeholder = ObjectProperty()
    autocomplete_hidelist = ListProperty()
    autocomplete_minkeys = NumericProperty(0)
    _autocomplete_index = ObjectProperty()

    def _is_valid(self):
        return len(self.data.keys()) >= self.autocomplete_minkeys and len(self.rawtext) > 2
    is_valid = AliasProperty(_is_valid, None, bind=('data', 'rawtext'))

    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        if not self.collide_point(*touch.pos):
            if self._keyboard:
                self._keyboard.release()
                self._keyboard = None
            return False
        if self._keyboard:
            return True
        self._keyboard = self.get_root_window().request_keyboard(
                self._on_keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        self._on_open()
        return True

    def _on_keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_key_down)
        self._keyboard = None
        self.rawtext = self.rawtext.strip()
        self._on_close()

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'backspace':
            self.rawtext = self.rawtext[:-1]
            self.data = {}
        elif keycode[1] == 'escape':
            keyboard.release()
        elif keycode[1] == 'delete':
            pass
        elif len(text):
            self.rawtext += text
            self.data = {}
        return True

    def _on_open(self):
        if not self.autocomplete_source:
            return
        a = Animation(opacity=0, d=0.3, t='out_quart')
        for child in self.autocomplete_hidelist:
            a.start(child)
        a = Animation(opacity=1., d=0.3, t='out_quart')
        a.start(self.autocomplete_placeholder)

    def _on_close(self):
        if not self.autocomplete_source:
            return
        a = Animation(opacity=1., d=0.3, t='out_quart')
        for child in self.autocomplete_hidelist:
            a.start(child)
        a = Animation(opacity=0., d=0.3, t='out_quart')
        a.start(self.autocomplete_placeholder)

    def on_autocomplete_source(self, instance, value):
        data = json.load(open('ui/uscities.json', 'r'))
        places = data['places']
        self._rows = data['rows']
        #with open(value, 'rb') as f:
        #    reader = csv.DictReader(f)
        #    for row in reader:
        #        place = "{0}, {1}".format(row['name'], row['state_code'])
        #        self._rows[place] = row
        #        places.append(place)
        self._autocomplete_index = StringIndex(places)
        self.autocomplete_minkeys = 2

    def on_rawtext(self, instance, value):
        if not self.autocomplete_source:
            return

        completions = self._autocomplete_index.find_prefix(value)[:10]
        completions = [c for c in completions if c.lower().startswith(value.lower())]
        if len(completions) == 1:
            return

        ph = self.autocomplete_placeholder
        ph.clear_widgets()
        ph.add_widget(CompletionLabel(text='Do you mean?'))
        for text in completions[:3]:
            btn = CompletionButton(text=text, data=self._rows.get(text, {}))
            btn.bind(on_release=self._set_text)
            ph.add_widget(btn)

    def _set_text(self, instance):
        if self._keyboard:
            print 'SET TEXT FROM', instance, instance.data
            self.rawtext = instance.text
            self.data = instance.data
            self._keyboard.release()



class ProgressionView(ModalView):
    text = StringProperty()
    progression = NumericProperty()


class IntroScreen(Screen):
    pass


class QuestionButton(Button):
    disabled = BooleanProperty()
    alpha_rotation = NumericProperty(0)
    background_default = StringProperty()
    background_wrong = StringProperty()
    color_wrong = ListProperty([1, 1, 1, 0])
    text_wrong = StringProperty()

    def __init__(self, **kwargs):
        super(QuestionButton, self).__init__(**kwargs)
        self._origin = {}
        Clock.schedule_once(self._prepare_fbo, 0)

    def on_text(self, *args):
        self._update_mesh()

    def _prepare_fbo(self, *args):
        # put all the current canvas into an FBO
        # then use the fbo texture into a Quad, for animating when disable

        # create the Fbo
        self.fbo = Fbo(size=(1, 1))
        with self.fbo.before:
            self.g_translate = Translate(self.x, self.y)
        self.orig_canvas = self.canvas
        self.fbo.add(self.canvas)

        # create a new Canvas
        self.canvas = Canvas()
        self.canvas.add(self.fbo)
        with self.canvas:
            Color(1, 1, 1)
            self.g_quad = Quad(texture=self.fbo.texture)

        # replace the canvas from the parent with the new one
        self.parent.canvas.remove(self.orig_canvas)
        self.parent.canvas.add(self.canvas)

        # ensure we'll be updated when we'll change position
        self.bind(pos=self._update_mesh,
                size=self._update_mesh,
                alpha_rotation=self._update_mesh)
        self._update_mesh()

    def _update_mesh(self, *args):
        m = self.g_quad
        alpha = self.alpha_rotation

        # don't do anything if the fbo size will be messup.
        if 0 in self.size:
            return

        # update fbo size, and reassign the new texture to the quad
        if self.fbo.size != self.size:
            self.fbo.size = self.size
            self.g_quad.texture = self.fbo.texture

        # change the background to red, and ensure we are not seeing any
        # changes when clicking
        if alpha >= 0.5 and self.background_normal != self.background_wrong:
            self._origin = {
                'background_normal': self.background_normal,
                'background_down': self.background_down,
                'color': (1, 1, 1, 1)}
            self.background_normal = self.background_wrong
            self.background_down = self.background_wrong
            self.color = self.color_wrong
            self.text = self.text_wrong

        # correctly setup the positionning for the quad rendering
        self.g_translate.xy = -self.x, -self.y

        # 3d fake effect
        dx = sin(alpha * pi / 2.) * self.width
        dy = sin(alpha * pi) * 25
        if alpha > 0.5:
            dy = -dy
            dx = self.width - dx
        m.points = (
            self.x + dx,        self.y + dy,
            self.right - dx,    self.y - dy,
            self.right - dx,    self.top + dy,
            self.x + dx,        self.top - dy)

    def disable(self):
        if self.alpha_rotation > 0:
            return
        d = 1.
        hd = 0.16 # at 0.16, the animation will be at the middle
        t = 'out_quart'
        Animation(alpha_rotation=1., t=t, d=d).start(self)
        (Animation(color=self.color_wrong, t=t, d=hd) +
         Animation(color=self.color, t=t, d=1 - hd)).start(self)

    def reset(self):
        self.alpha_rotation = 0
        self.background_normal =  "ui/screens/question/qbg.png"
        for key, value in self._origin.iteritems():
            setattr(self, key, value)


class QuestionScreen(Screen):
    bg_image = StringProperty(errorvalue="ui/images/trans.png")
    text = StringProperty()
    markedup_text = StringProperty()
    option_a = StringProperty()
    option_b = StringProperty()
    option_c = StringProperty()
    option_d = StringProperty()
    option_wrong_a = StringProperty()
    option_wrong_b = StringProperty()
    option_wrong_c = StringProperty()
    option_wrong_d = StringProperty()
    button_grid = ObjectProperty(None)
    reset = BooleanProperty()

    def on_text(self, *args):
        first_words = " ".join(self.text.split(" ")[:3])
        other_words = " ".join(self.text.split(" ")[3:])
        text_parts = (first_words, other_words)
        self.markedup_text = "[size=60sp]%s[/size] %s\n" % text_parts

    def on_reset(self, *args):
        for c in self.button_grid.children:
            c.reset()


    def on_transition_progress(self, *args):
        if self.transition_progress == 1.0 and self.transition_state == "in":
            print "done transitioning"
            App.get_running_app().preload_answer_screen()


class AnswerImagePopup(ModalView):
    answer = ObjectProperty()
    alpha = NumericProperty(0)
    scatter = ObjectProperty()

    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.reset()
            return True
        return super(AnswerImagePopup, self).on_touch_down(touch)

    def reset(self):
        rotation = 360. if self.scatter.rotation > 180 else 0.
        Animation(rotation=rotation, scale=1., center=self.center,
                d=0.5, t='out_quart').start(self.scatter)

    def open(self):
        super(AnswerImagePopup, self).open()
        Animation(alpha=1., d=.5, t='out_quart').start(self)

    def dismiss(self):
        super(AnswerImagePopup, self).dismiss()
        Animation(alpha=0., d=.5, t='out_quart').start(self)


class AnswerImage(AsyncImage):
    img_data = ObjectProperty()
    text = StringProperty()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.open()
            return True
        super(AnswerImage, self).on_touch_down(touch)


    def _get_smallest(self):
        print "XXXX", self.img_data
        if self.img_data.get('medium'):
            return self.img_data['medium']
        return self.img_data['full']

    def on_img_data(self, *args):
        self.source = self._get_smallest()
        self.text = self.img_data.get('caption') or ''

    def open(self):
        self._popup = AnswerImagePopup(answer=self)
        self._popup.open()



class ThumnailList(BoxLayout):
    def clear(self):
        self._next_x = 50
        self.clear_widgets()


    def add_thumb(self, img):
        print "ADDING", img
        if not img.get('full'):
            return
        w = AnswerImage(img_data=img)
        w.size_hint = (None, None)
        w.height = 400
        w.width = 400 * w.image_ratio
        self.minimum_width = self.minimum_width + w.width + 50
        self.add_widget(w)

    def add_images(self, images):
        self.clear()
        self.minimum_width = 50
        for img in images:
            self.add_thumb(img)
        self.add_widget(Widget(size_hint=(None, None), width=200))
        self.minimum_width = self.minimum_width + 250
        self.width = self.minimum_width
        self.parent.update_from_scroll()
        print "THIMBS", self.width



class AnswerScreen(Screen):
    text = StringProperty("")
    correct = BooleanProperty(False)
    feedback = StringProperty("")
    images = ListProperty([])
    image_layout = ObjectProperty()

    _feedback_right = open('ui/screens/answer/feedback_right.txt').readlines()
    _feedback_wrong = open('ui/screens/answer/feedback_wrong.txt').readlines()

    def on_text(self, *args):
        if self.correct:
            self.feedback = random.choice(self._feedback_right).strip()
        else:
            self.feedback = random.choice(self._feedback_wrong).strip()

    def on_images(self, *args):
        self.image_layout.clear()
        self.image_layout.add_images(self.images)


class ResultsScreen(Screen):
    text = StringProperty("")

    def fadein(self, fadelist):
        a = Animation(color=(.5, .5, .5, .7), d=0.3, t='out_quart')
        [a.start(x) for x in fadelist]

    def fadeout(self, fadelist):
        a = Animation(color=(1, 1, 1, 1), d=0.3, t='out_quart')
        [a.start(x) for x in fadelist]

class NickStandingEntry(BoxLayout):
    entry = DictProperty()
class CityStandingEntry(BoxLayout):
    entry = DictProperty()
class CountyStandingEntry(BoxLayout):
    entry = DictProperty()
class StateStandingEntry(BoxLayout):
    entry = DictProperty()

class StandingsScreen(Screen):
    tp = OptionProperty('nick', options=('nick', 'city', 'county', 'state'))
    container = ObjectProperty()
    def on_transition_state(self, instance, value):
        if value == 'in':
            self.reload()

    def reload(self):
        App.get_running_app().load_standings(self.tp)

    def on_tp(self, instance, value):
        self.reload()

    def set_standings(self, tp, result):
        tcls = {'nick': NickStandingEntry,
                'city': CityStandingEntry,
                'county': CountyStandingEntry,
                'state': StateStandingEntry}[tp]
        args_converter = lambda index, rec: {'entry': rec}
        adapter = ListAdapter(data=result,
                args_converter=args_converter,
                cls=tcls)
        self.container.clear_widgets()
        self.container.add_widget(ListView(adapter=adapter))




class StatusBar(RelativeLayout):
    score = NumericProperty(0)
    questions_left = NumericProperty(0)
    alpha_show = NumericProperty(0.0)

    def show(self, *args):
        (Animation(d=1.5) + Animation(alpha_show=1.0, t='out_quad', d=1.0)
        ).start(self)

    def hide(self, *args):
        Animation(alpha_show=0.0, t='out_quad', d=1.0).start(self)


class IowaIQApp(App):

    def build_config(self, config):
        default_config = json.load(open('default_config.json'))
        for k, v in default_config.iteritems():
            config.setdefaults(k, v)

    def build(self):
        self.root = self.viewport = Viewport(size=(2048, 1536))
        self.ensure_directories()
        self.load_questions()

    def ensure_directories(self):
        resources_dir = join(self.get_data_dir(), 'resources')
        if not exists(resources_dir):
            makedirs(resources_dir)

    def show_app(self, *args):
        self._hide_progression()

        self.screen_manager = ScreenManager(transition=FadeTransition(duration=0.3))
        self.screen_manager.add_widget(IntroScreen(name='intro'))
        self.screen_manager.add_widget(QuestionScreen(name='question'))
        self.screen_manager.add_widget(AnswerScreen(name='answer'))
        self.screen_manager.add_widget(ResultsScreen(name='results'))
        self.screen_manager.add_widget(StandingsScreen(name='standings'))
        self.viewport.add_widget(self.screen_manager)

        self.status_bar = StatusBar()
        self.viewport.add_widget(self.status_bar)

    def start_viewstandings(self):
        self.screen_manager.current = 'standings'

    def start_quiz(self):
        self.quiz = random.sample(self.questions, 5)
        self.status_bar.score = 0
        self.status_bar.show()
        self.next_question()

    def next_question(self):
        if not self.quiz:
            return self.finish_quiz()
        q = self.question = self.quiz.pop()
        self.status_bar.questions_left = 5 - len(self.quiz)

        qscreen = self.screen_manager.get_screen('question')
        qscreen.text = q['question']
        qscreen.option_a = q['answers'][0]
        qscreen.option_b = q['answers'][1]
        qscreen.option_c = q['answers'][2]
        qscreen.option_d = q['answers'][3]

        #qscreen.bg_image = q['question_bg_image']
        qscreen.reset = True
        qscreen.reset = False

        #def _goto_screen(*args):
        self.screen_manager.current = 'question'
        #Clock.schedule_once(_goto_screen, 0.2)

    def preload_answer_screen(self):
        q = self.question
        ascreen = self.screen_manager.get_screen('answer')
        ascreen.correct = True
        ascreen.text = q['answer_text']
        ascreen.images = q['answer_images']



    def check_answer(self, ui_question, ui_button, answer):
        q = self.question
        is_correct = (answer == int(q['correct_answer']))
        print "answer is:", is_correct
        if is_correct:
            self.status_bar.score += 4
            ui_button.background_normal = "ui/screens/question/qbg_correct.png"
            ui_button._update_mesh()
            #def _go_answer(*args):
            self.screen_manager.current = 'answer'
            #Clock.schedule_once(_go_answer, 0)
        else:
            self.status_bar.score -= 1
            ui_button.text_wrong = q['answer_corrections'][answer - 1]
            ui_button.disable()

    def finish_quiz(self):
        rscreen = self.screen_manager.get_screen('results')
        rscreen.text = "You got {0} points.".format(self.status_bar.score)
        self.screen_manager.current = 'results'
        self.status_bar.hide()

    def get_data_dir(self):
        if platform() == 'ios':
            directory = join(expanduser('~'), 'Documents')
        elif platform() == 'android':
            app_name = self.get_application_name
            directory = join('/sdcard', '.{0}'.format(app_name))
        else:
            directory = self.directory
        if not exists(directory):
            makedirs(directory)
        return directory

    def on_pause(self):
        return True

    #
    # Score part
    #

    def submit_score(self, nick, city):
        d = dict(
            nick=nick.rawtext,
            city=city.data['name'],
            county=city.data['county'],
            state=city.data['state'],
            state_code=city.data['state_code'],
            score=self.status_bar.score)
        body = urllib.urlencode(d)
        self._show_progression('Submitting score...', 0, 1)
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        self._req = UrlRequest(self.config.get('app', 'score'),
                req_body=body, req_headers=headers,
                on_success=self._on_submit_success,
                on_error=self._on_submit_failed)

    def _on_submit_success(self, req, result):
        self._hide_progression()
        self.screen_manager.current = 'standings'

    def _on_submit_failed(self, req, result):
        self._hide_progression()
        self.screen_manager.current = 'intro'

    def load_standings(self, tp):
        self._req = UrlRequest(self.config.get('app', 'standings') + '?q=' + tp,
            on_success=partial(self._on_standings_success, tp),
            on_error=self._on_standings_error)

    def _on_standings_success(self, tp, req, result):
        self.screen_manager.current = 'standings'
        self.screen_manager.current_screen.set_standings(tp, result)

    def _on_standings_error(self, req, error):
        pass


    # Update part
    # Manage the update of questions.json + associated data
    def load_questions(self):
        self._show_progression('Downloading questions...', 0, 1)
        # first step, download the questions.json
        self._req = UrlRequest(self.config.get('app', 'questions'),
            on_success=self._pull_update_success,
            on_error=self._pull_update_failed,
            on_progress=self._progress_update,
        )

    def _progress_update(self, req, cursize, totalsize):
        msg = 'Downloading questions...'
        self._show_progression(msg, cursize, totalsize)

    def _pull_update_success(self, request, result):
        # second step, download all the outdated resources
        self._questions_fn = join(self.get_data_dir(), 'questions.json')
        with open(self._questions_fn, 'w') as fd:
            json.dump(result, fd)

        self._jsondata = JsonData('questions.json',
            on_success=self._pull_update_done,
            on_progress=self._show_progression
        )

    def _pull_update_done(self, questions):
        self.questions = questions
        for q in self.questions:
            print q['question_bg_image']
        self._show_progression('Starting application...', 100, 100)
        Clock.schedule_once(self.show_app, 0.1)

    def _pull_update_failed(self, request, error):
        # XXX TODO
        pass

    # Modal view for showing progression
    def _show_progression(self, text, size, total):
        if not hasattr(self, '_progression'):
            self._progression = ProgressionView()
            self._progression.open()
        self._progression.text = text
        if total > 0:
            self._progression.progression = size / float(total) * 100.
        else:
            self._progression.progression = 0

    def _hide_progression(self, *largs):
        if hasattr(self, '_progression'):
            self._progression.dismiss()
            del self._progression

APP = IowaIQApp()
APP.run()
