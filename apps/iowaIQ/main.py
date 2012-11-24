import random
import json
from jsondata import JsonData


from os import makedirs
from os.path import join, exists, expanduser
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Fbo, Canvas, Color, Quad, Translate
from kivy.properties import (
    BooleanProperty, NumericProperty, StringProperty, ObjectProperty,
    ListProperty)

from math import sin, pi
from viewport import Viewport


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
        hd = d / 2.0
        t = 'out_quart'
        Animation(alpha_rotation=1., t=t, d=d).start(self)
        (Animation(color=self.color_wrong, t=t, d=hd) +
         Animation(color=self.color, t=t, d=hd)).start(self)

    def reset(self):
        self.alpha_rotation = 0
        self.background_normal =  "ui/screens/question/qbg.png"
        for key, value in self._origin.iteritems():
            setattr(self, key, value)


class QuestionScreen(Screen):
    bg_image = StringProperty(errorvalue="ui/images/trans.png")
    text = StringProperty()
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

    def on_reset(self, *args):
        for c in self.button_grid.children:
            c.reset()


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


class AnswerImage(Image):
    text = StringProperty()
    source_full = StringProperty()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.open()
            return True
        super(AnswerImage, self).on_touch_down(touch)

    def open(self):
        self._popup = AnswerImagePopup(answer=self)
        self._popup.open()


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
        self.image_layout.clear_widgets()
        print "IMAGES:", self.images
        for img in self.images:
            if not img.get('full'):
                continue
            src = img['full']
            if img.get('medium'):
                src = img['medium'][0]
            self.image_layout.add_widget(AnswerImage(
                source=src,
                source_full=img['full'],
                text=img.get('caption') or '',
            ))


class ResultsScreen(Screen):
    text = StringProperty("")


class StatusBar(RelativeLayout):
    alpha_show = NumericProperty(0.0)
    def show(self, *args):
        (
        Animation(d=0.8) +
        Animation(alpha_show=1.0, t='out_quad', d=1.0)
        ).start(self)

    def hide(self, *args):
        Animation(alpha_show=1.0, t='out_quad', d=0.0).start(self)


class IowaIQApp(App):

    def build_config(self, config):
        default_config = json.load(open('default_config.json'))
        for k, v in default_config.iteritems():
            config.setdefaults(k, v)

    def build(self):
        self.root = FloatLayout()
        self.ensure_directories()
        self.load_questions()

    def ensure_directories(self):
        resources_dir = join(self.get_data_dir(), 'resources')
        if not exists(resources_dir):
            makedirs(resources_dir)

    def show_app(self, *args):
        self._hide_progression()
        self.viewport = Viewport(size=(2048, 1536))

        self.screen_manager = ScreenManager(transition=SlideTransition())
        self.screen_manager.add_widget(IntroScreen(name='intro'))
        self.screen_manager.add_widget(QuestionScreen(name='question'))
        self.screen_manager.add_widget(AnswerScreen(name='answer'))
        self.screen_manager.add_widget(ResultsScreen(name='results'))
        self.viewport.add_widget(self.screen_manager)

        self.status_bar = StatusBar()
        self.viewport.add_widget(self.status_bar)

        self.root.add_widget(self.viewport)

    def start_quiz(self):
        self.score = 0
        self.status_bar.show()
        self.quiz = random.sample(self.questions, 5)
        self.next_question()

    def next_question(self):
        if not self.quiz:
            return self.finish_quiz()
        q = self.question = self.quiz.pop()
        qscreen = self.screen_manager.get_screen('question')
        qscreen.text = q['question']
        qscreen.option_a = q['answers'][0]
        qscreen.option_b = q['answers'][1]
        qscreen.option_c = q['answers'][2]
        qscreen.option_d = q['answers'][3]
        qscreen.bg_image = q['question_bg_image'].get('full')
        # trigger button reset
        qscreen.reset = True
        qscreen.reset = False

        self.screen_manager.current = 'question'

    def check_answer(self, ui_question, ui_button, answer):
        q = self.question
        is_correct = (answer == int(q['correct_answer']))
        if is_correct:
            self.score += 1
            ui_button.background_normal = "ui/screens/question/qbg_correct.png"
            ui_button._update_mesh()
            def _go_answer(*args):
                ascreen = self.screen_manager.get_screen('answer')
                ascreen.correct = True
                ascreen.text = q['answer_text']
                ascreen.images = q['answer_images']
                self.screen_manager.current = 'answer'
            Clock.schedule_once(_go_answer, 0.5)
        else:
            ui_button.text_wrong = q['answer_corrections'][answer - 1]
            ui_button.disable()

    def finish_quiz(self):
        rscreen = self.screen_manager.get_screen('results')
        rscreen.text = "You got {0} out of 4".format(self.score)
        self.screen_manager.current = 'results'

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

    # Update part
    # Manage the update of questions.json + associated data
    def load_questions(self):
        self._show_progression('Downloading questions...', 0, 1)
        # first step, download the questions.json
        self._req = UrlRequest(self.config.get('app', 'questions'),
            on_success=self._pull_update_success,
            on_error=self._pull_update_failed,
            on_progress=self._progress_update
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
