import os
import sys
import imp
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.factory import Factory as F
from imagebutton import ImageButton
from kivy.resources import resource_add_path, resource_remove_path
import gc

def show_menu():
    App.get_running_app().show_menu()


class ChildApp(object):

    def __init__(self, name):
        self.name = name
        self.parent_app = App.get_running_app()

        # setup paths
        self.parent_path = self.parent_app.directory
        self.app_path = os.path.join(self.parent_path, "apps", self.name)
        sys.path.append(self.app_path)
        resource_add_path(self.app_path)

        #load code
        m_name = "_child_app_"#.format(self.name)
        f_name = os.path.join(self.app_path, 'main.py')
        self.module = imp.load_source(m_name, f_name, open(f_name, 'r'))

        #load_kv
        self.kv_file = os.path.join(self.app_path, 'ui.kv')

    def build(self):
        self.root = Builder.load_file(self.kv_file)
        return self.root

    def unload(self):
        Builder.unload_file(self.kv_file)
        del self.module
        self.module = None
        gc.collect()

        sys.path.remove(self.app_path)
        resource_remove_path(self.app_path)




class BackToMenuButton(ImageButton):
    def on_release(self, *args):
        show_menu()



