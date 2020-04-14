import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
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
    def add_driver(self):
        print("button dziala")
        grid = self.ids.list

        id = self.ids.driver_id.text
        first_name = self.ids.name.text
        last_name = self.ids.last_name.text

        list = BoxLayout(size_hint_y=None, height=30, pos_hint={'top': .5})
        grid.add_widget(list)

        id = Label(text=id, size_hint_x=.2)
        first_name = Label(text=first_name, size_hint_x=.2)
        last_name = Label(text=last_name, size_hint_x=.2)
        empty = Label(text="", size_hint_x=.3)

        list.add_widget(id)
        list.add_widget(first_name)
        list.add_widget(last_name)
        list.add_widget(empty)


class LapifyApp(App):
    def build(self):
        lapi = TitleBar()
        return lapi


def show_popup():
    show = PopLay()
    popupWindow = Popup(title="Rozpocznij nowa sesje", content=show, size_hint=(.5, .7), auto_dismiss=False)
    popupWindow.open()


if __name__ == '__main__':
    LapifyApp().run()
