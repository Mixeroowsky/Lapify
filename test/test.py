import psycopg2 as db
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

connection = db.connect(database="lapify", user="postgres", password="dupa")


class LoginScreen(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check(self):

        cursor = connection.cursor()
        cursor.execute("select id_kierowcy, imie, nazwisko from kierowca")
        rows = cursor.fetchall()
        grid = self.ids.grid
        list = BoxLayout(size_hint_y=None, height=30, pos_hint={'top': .5})
        grid.add_widget(list)
        for r in rows:
            id = Label(text=str(r[0]), size_hint_x=.2)
            first_name = Label(text=str(r[1]), size_hint_x=.2)
            last_name = Label(text=str(r[2]), size_hint_x=.2)
            empty = Label(text="", size_hint_x=.3)
            list.add_widget(id)
            list.add_widget(first_name)
            list.add_widget(last_name)
            list.add_widget(empty)

        cursor.close()

    def input(self):
        driver_name = self.ids.name
        driver_last = self.ids.last_name

        cursor = connection.cursor()
        cursor.execute("select id_kierowcy, imie, nazwisko from kierowca")
        rows = cursor.fetchall()
        cursor.execute("insert into kierowca (id_kierowcy, imie, nazwisko) values (%s, %s, %s)",
                       (len(rows) + 1, driver_name.text, driver_last.text))
        cursor.close()


class testApp(App):
    def build(self):
        return LoginScreen()


if __name__ == '__main__':
    testApp().run()
