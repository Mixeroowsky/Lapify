from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition, SwapTransition, FadeTransition
from kivy.uix.widget import Widget
from kivy.config import Config
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
#Config.set('kivy', 'exit_on_escape', '0')

class NowaSesja(Screen):
    pass


class NowyKierowca(Screen):
    pass

class Lista(Screen):
    pass

class WybierzKierowce(Screen):
    pass


class Live(Screen):
    pass


class PoprzednieSesje(Screen):
    pass


class Pomoc(Screen):
    pass


class TitleBar(Widget):
    pass


class Rozpocznij(Screen):
    def swap(self):
        Manager.transition = SwapTransition()

    def unswap(self):
        Manager.transition = FadeTransition()


class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.transition = NoTransition()




class DodajKierowce(Screen):
    def add_driver(self):
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


kv = Builder.load_file("design.kv")
class LapifyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driverReference = DodajKierowce()

    def build(self):
        return kv




if __name__ == '__main__':
    LapifyApp().run()
