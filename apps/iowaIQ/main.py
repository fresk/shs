import random
import json
from jsondata import JsonData


from os import makedirs
from os.path import join, exists
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.network.urlrequest import UrlRequest
from kivy.properties import *
from kivy.utils import platform
from kivy.clock import Clock
from viewport import Viewport


class ProgressionView(ModalView):
    text = StringProperty()
    progression = NumericProperty()


class IntroScreen(Screen):
    pass


class QuestionScreen(Screen):
    bg_image = StringProperty(errorvalue="ui/images/trans.png")
    text = StringProperty("")
    option_a = StringProperty("")
    option_b = StringProperty("")
    option_c = StringProperty("")
    option_d = StringProperty("")


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
        print "ANWER IMAGES", self.images
        self.image_layout.clear_widgets()
        for img in self.images:
            if img[0]:
                self.image_layout.add_widget(Image(source=img[0]))


class ResultsScreen(Screen):
    text = StringProperty("")



class IowaIQApp(App):

    def build_config(self, config):
        config.setdefaults('app', {
            'questions':
                'http://www.fresksite.net/dcadb/wp-content/themes/dca/api/questions.php'
        })

    def start_quiz(self):
        self.score = 0
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
        qscreen.bg_image = q['question_bg_image']
        print "set bg image to", q['question_bg_image']

        self.screen_manager.current = 'question'

    def check_answer(self, answer):
        ascreen = self.screen_manager.get_screen('answer')
        ascreen.correct = (answer == int(self.question['correct_answer']))
        if ascreen.correct:
            self.score += 1
        ascreen.text = self.question['answer_text']
        ascreen.images = self.question['answer_images']
        self.screen_manager.current = 'answer'


    def finish_quiz(self):
        rscreen = self.screen_manager.get_screen('results')
        rscreen.text = "You got {0} out of 4".format(self.score)
        self.screen_manager.current = 'results'

    def build(self):
        self.root = FloatLayout()
        self.load_questions()

    def show_app(self, *args):
        self._hide_progression()
        self.screen_manager = ScreenManager(transition=SlideTransition())
        self.screen_manager.add_widget(IntroScreen(name='intro'))
        self.screen_manager.add_widget(QuestionScreen(name='question'))
        self.screen_manager.add_widget(AnswerScreen(name='answer'))
        self.screen_manager.add_widget(ResultsScreen(name='results'))

        self.viewport = Viewport(size=(2048,1536))
        self.viewport.add_widget(self.screen_manager)

        self.root.add_widget(self.viewport)

    def get_data_dir(self):
        if platform() == 'ios':
            directory = join(self.directory, 'Documents')
        elif platform() == 'android':
            directory = join('/sdcard', '.{0}'.format(self.get_application_name))
        else:
            directory = self.directory
        if not exists(directory):
            makedirs(directory)
        return directory

    #
    # Update part
    # Manage the update of questions.json + associated data
    #
    def load_questions(self):
        # first step, download the questions.json
        self._req = UrlRequest(self.config.get('app', 'questions'),
                on_success=self._pull_update_2,
                on_error=self._pull_update_failed,
                on_progress=lambda req, cursize, totalsize: self._show_progression(
                    'Downloading questions...', cursize, totalsize))

    def _pull_update_2(self, request, result):
        # second step, download all the outdated resources
        self._questions_fn = join(self.get_data_dir(), 'questions.json')
        with open(self._questions_fn, 'w') as fd:
            json.dump(result, fd)

        self._jsondata = JsonData('questions.json',
                on_success=self._pull_update_3,
                on_progress=self._show_progression)

    def _pull_update_3(self, questions):
        self.questions = questions
        for q in self.questions:
            print q['question_bg_image']
        self._show_progression('Starting application...', 100, 100)
        Clock.schedule_once(self.show_app, 0.1)

    def _pull_update_failed(self, request, error):
        # XXX TODO
        pass

    #
    # Modal view for showing progression
    #
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
