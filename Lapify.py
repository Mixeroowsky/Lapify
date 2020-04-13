import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.config import Config
import kivy.utils

Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')


class Stack(StackLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def btn(self):
        show_popup()


class TitleBar(Widget):
    pass


class PopLay(FloatLayout):
    pass


class LapifyApp(App):
    def build(self):
        lapi = TitleBar()
        return lapi


def show_popup():
    show = PopLay()
    popupWindow = Popup(title="Rozpocznij nowa sesje", content=show, size_hint=(.7, .7), auto_dismiss=False)
    popupWindow.open()


if __name__ == '__main__':
    LapifyApp().run()
