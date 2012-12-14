##


from kivy.app import App
from kivy.clock import Clock
from subprocess import Popen
from kivy.lang import Builder

Builder.load_string('''
<Launcher>:
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: 'loading...'
        Label:
            text: 'loading...'
''')


class Launcher(FloatLayout):
    pass


class LauncherApp(App):
    def build(self):
        Clock.schedule_once(self.start_exhibit, 1.0)
        return Launcher()

    def cmd(self, *args, **kwargs):
        print '>> command {0}'.format((args, kwargs))
        Popen(*args, **kwargs).communicate()

    def start_exhibit(self, *args):
        self.start('python', 'main.py')


    def start(self, *args):

        # switch to a new virtual desktop
        #cmd(['xdotool', 'set_desktop_viewport'] + map(str, virtual_desktop_2))

        # stop our event loop (will stop all the input provider)
        # also, avoid to auto remove the providers created by runTouchApp
        EventLoop.input_providers_autoremove = []
        EventLoop.stop()

        # start the command
        options = ['-k', '--size', 'x'.join(map(str, window_size))]
        self.cmd(list(args) + options)

        # restart our event loop
        #EventLoop.start()

        # switch back to the main virtual desktop
        #cmd(['xdotool', 'set_desktop_viewport'] + map(str, virtual_desktop_1))


LauncherApp().run()
