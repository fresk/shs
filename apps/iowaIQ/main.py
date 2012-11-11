from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

import os
import glob
import random




class Question(object):
    def __init__(self, **kwargs):
        self.text = kwargs.get('text', "")
        self.options = kwargs.get('options', (("", 0),)*4)
        self.answer = kwargs.get('answer', "")
        self.detail = kwargs.get('detail', "")
        self.image = kwargs.get('image', "")

    @classmethod
    def load(cls, path):
        qargs = {}
        fname = os.path.join(path, 'question.txt')
        qargs['text'] = open(fname, 'r').read()

        fname = os.path.join(path, 'answer.txt')
        qargs['detail'] = open(fname, 'r').read()


        fname = os.path.join(path, 'options.txt')
        qargs['options'] = []
        for opt in open(fname, 'r').readlines():
            if opt.startswith('!'):
                opt = opt[1:]
                qargs['answer'] = opt
            qargs['options'].append(opt)

        return Question(**qargs)




class IntroScreen(Screen):
    pass


class PlayerInfoScreen(Screen):
    pass


class QuestionScreen(Screen):
    text = StringProperty("")
    option_a = StringProperty("")
    option_b = StringProperty("")
    option_c = StringProperty("")
    option_d = StringProperty("")


class AnswerScreen(Screen):
    text = StringProperty("")
    correct = BooleanProperty(False)


class ResultsScreen(Screen):
    text = StringProperty("")



class IowaIQApp(App):

    def load_questions(self):
        self.questions = [Question.load(q) for q in glob.glob('questions/*')]

    def start_quiz(self):
        self.score = 0
        self.quiz = random.sample(self.questions, 4)
        self.next_question()

    def next_question(self):
        if not self.quiz:
            return self.finish_quiz()
        q = self.question = self.quiz.pop()
        qscreen = self.screen_manager.get_screen('question')
        qscreen.text = q.text
        qscreen.option_a = q.options[0]
        qscreen.option_b = q.options[1]
        qscreen.option_c = q.options[2]
        qscreen.option_d = q.options[3]
        self.screen_manager.current = 'question'

    def check_answer(self, answer):
        ascreen = self.screen_manager.get_screen('answer')
        if (answer == self.question.answer):
            self.score += 1
        ascreen.text = self.question.detail
        ascreen.correct = (answer == self.question.answer)
        self.screen_manager.current = 'answer'


    def finish_quiz(self):
        rscreen = self.screen_manager.get_screen('results')
        rscreen.text = "You got {0} out of 4".format(self.score)
        self.screen_manager.current = 'results'

    def build(self):
        self.load_questions()
        self.screen_manager = ScreenManager(transition=SlideTransition())
        self.screen_manager.add_widget(IntroScreen(name='intro'))
        self.screen_manager.add_widget(PlayerInfoScreen(name='playerinfo'))
        self.screen_manager.add_widget(QuestionScreen(name='question'))
        self.screen_manager.add_widget(AnswerScreen(name='answer'))
        self.screen_manager.add_widget(ResultsScreen(name='results'))
        return self.screen_manager

APP = IowaIQApp()
APP.run()
