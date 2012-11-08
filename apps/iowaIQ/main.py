from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen

import os
import glob
import random


class Question(object):
    def __init__(self, **kwargs):
        self.question = kwargs.get('question')
        self.options = kwargs.get('options')
        self.answer = kwargs.get('answer')
        self.image = kwargs.get('image')

    @classmethod
    def load(cls, path):
        qargs = {}
        fname = os.path.join(path, 'question.txt')
        qargs['question'] = open(fname, 'r').read()

        fname = os.path.join(path, 'answer.txt')
        qargs['answer'] = open(fname, 'r').read()


        fname = os.path.join(path, 'options.txt')
        qargs['options'] = []
        for opt in open(fname, 'r').readlines():
            if opt.startswith('!'):
                opt = opt[1:]
                qargs['options'].append((opt, True))
            else:
                qargs['options'].append((opt, False))

        return Question(**qargs)




class IntroScreen(Screen):
    pass


class PlayerInfoScreen(Screen):
    pass


class QuestionScreen(Screen):
    pass


class AnswerScreen(Screen):
    pass


class ResultsScreen(Screen):
    pass



class IowaIQApp(App):

    def load_questions(self):
        self.questions = [Question.load(q) for q in glob.glob('questions/*')]

    def build(self):
        self.load_questions()
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(IntroScreen(name='intro'))
        self.screen_manager.add_widget(PlayerInfoScreen(name='playerinfo'))
        self.screen_manager.add_widget(QuestionScreen(name='question'))
        self.screen_manager.add_widget(AnswerScreen(name='answer'))
        self.screen_manager.add_widget(ResultsScreen(name='results'))

        return self.screen_manager

IowaIQApp().run()
