import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.button import Button
import kivy.utils

Window.clearcolor = kivy.utils.get_color_from_hex('#303030')


class NowaSesja(Screen):
    pass


class Live(Screen):
    pass


class PoprzednieSesje(Screen):
    pass


class Pomoc(Screen):
    pass


class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.transition = NoTransition()


kv = Builder.load_file("xd.kv")


class MyApp(App):
    def build(self):
        return kv


if __name__ == "__main__":
    MyApp().run()

