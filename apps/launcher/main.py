## CONFIGURATION
window_size = (3840, 1080)
virtual_desktop_1 = (0, 0)
virtual_desktop_2 = (3840, 0)
##


from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.base import EventLoop
from subprocess import Popen
from kivy.lang import Builder

Builder.load_string('''
<Launcher>:
    AnchorLayout:
        GridLayout:
            cols: 1
            size_hint: None, None
            size: 200, 200
            spacing: 50

            Button:
                text: 'Touchtracer'
                on_release: app.start('python', '/home/tito/code/kivy/examples/demo/touchtracer/main.py')

            Button:
                text: 'Showcase'
                on_release: app.start('python', '/home/tito/code/kivy/examples/demo/showcase/main.py')
''')


class Launcher(FloatLayout):
    pass


class LauncherApp(App):
    def build(self):
        return Launcher()

    def cmd(self, *args, **kwargs):
        print '>> command {0}'.format((args, kwargs))
        Popen(*args, **kwargs).communicate()

    def start(self, *args):
        cmd = self.cmd

        # switch to a new virtual desktop
        cmd(['xdotool', 'set_desktop_viewport'] + map(str, virtual_desktop_2))

        # stop our event loop (will stop all the input provider)
        # also, avoid to auto remove the providers created by runTouchApp
        EventLoop.input_providers_autoremove = []
        EventLoop.stop()

        # start the command
        options = ['-k', '--size', 'x'.join(map(str, window_size))]
        cmd(list(args) + options)

        # restart our event loop
        EventLoop.start()

        # switch back to the main virtual desktop
        cmd(['xdotool', 'set_desktop_viewport'] + map(str, virtual_desktop_1))


LauncherApp().run()
