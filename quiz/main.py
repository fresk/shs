from kivy.app import App
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import *

import json
import random


class QuizAnswer(Button):
    text = StringProperty("Answer Text")
    correct = BooleanProperty(False)



class QuizScreen(FloatLayout):
    question = StringProperty("Question")
    explanation = StringProperty("Explanation")
    answers = ListProperty(None)

    answerlayout = ObjectProperty(None)

    def _add_answers(self, *args):
        print self, self.answerlayout
        self.answerlayout.clear_widgets()
        for a in self.answers:
            w = QuizAnswer(**a)
            self.answerlayout.add_widget(w)

    def on_answers(self, *args):
        Clock.schedule_once(self._add_answers)



class ExplanationScreen(FloatLayout):
    answer = ObjectProperty(None)
    explanation = StringProperty("Explanation")






class QuizApp(App):
    def submit_answer(self, answer):
        self.root.clear_widgets()
        expl = ExplanationScreen(answer=answer, **self.quiz)
        self.root.add_widget(expl)

    def random_question(self, *args):
        self.quiz = random.choice(self.questions)
        self.root.clear_widgets()
        self.root.add_widget(QuizScreen(**self.quiz))

    def load_data(self):
        def _decode_list(data):
            rv = []
            for item in data:
                if isinstance(item, unicode):
                    item = item.encode('utf-8')
                elif isinstance(item, list):
                    item = _decode_list(item)
                elif isinstance(item, dict):
                    item = _decode_dict(item)
                rv.append(item)
            return rv

        def _decode_dict(data):
            rv = {}
            for key, value in data.iteritems():
                if isinstance(key, unicode):
                   key = key.encode('utf-8')
                if isinstance(value, unicode):
                   value = value.encode('utf-8')
                elif isinstance(value, list):
                   value = _decode_list(value)
                elif isinstance(value, dict):
                   value = _decode_dict(value)
                rv[key] = value
            return rv

        self.questions = json.load(open('questions.json', 'r'), object_hook=_decode_dict)


    def build(self):
        self.load_data()
        Clock.schedule_once(self.random_question)
        return FloatLayout()




if __name__ == "__main__":
    IowaIQApp().run()
