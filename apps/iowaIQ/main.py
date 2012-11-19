import os
import md5
import random
import urllib2
import json
import jsondata
import requests


from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.properties import *
from viewport import Viewport


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

    def pull_update(self):
        r = requests.get('http://www.fresksite.net/dcadb/wp-content/themes/dca/api/questions.php')
        if r.status_code == 200:
            json.dump(r.json, open('questions.json', 'w'))
        print "XXXXXXXXXXXXXxx", type(r.status_code)
    def load_questions(self):
        self.pull_update()
        self.questions = jsondata.load('questions.json')
        for q in self.questions:
            print q['question_bg_image']

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
        self.load_questions()
        self.screen_manager = ScreenManager(transition=SlideTransition())
        self.screen_manager.add_widget(IntroScreen(name='intro'))
        self.screen_manager.add_widget(QuestionScreen(name='question'))
        self.screen_manager.add_widget(AnswerScreen(name='answer'))
        self.screen_manager.add_widget(ResultsScreen(name='results'))

        self.viewport = Viewport(size=(2048,1536))
        self.viewport.add_widget(self.screen_manager)
        return self.viewport

APP = IowaIQApp()
APP.run()
