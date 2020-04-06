from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.config import Config

Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')


class StackLayout(StackLayout):
    pass
class TitleBar(Widget):
    pass

class LapifyApp(App):
    def build(self):
        lapi = TitleBar()
        return lapi

if __name__ == '__main__':
    LapifyApp().run()
