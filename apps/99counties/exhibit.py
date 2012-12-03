from kivy.app import App
from kivy.properties import StringProperty
from kivy.factory import Factory as F
from imagebutton import ImageButton

def show_menu():
    App.get_running_app().show_menu()


class BackToMenuButton(ImageButton):
    def on_release(self, *args):
        show_menu()



