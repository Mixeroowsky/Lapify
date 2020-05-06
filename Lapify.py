from kivy.config import Config      # Ta sekcja musi być na górze
Config.set('graphics', 'resizable', False)   # Fullscreen
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # Brak czerwonych kropek
#Config.set('kivy', 'exit_on_escape', '0')

import psycopg2 as db
import datetime
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition, SwapTransition, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.button import Button


# Żeby móc robić Labele z kolorowym tłem w pliku pythona:
# Nwm czemu muszą być takie małe wcięcia ale inaczej nie działa XD
Builder.load_string("""       
<PoleTabeli>:
  size_hint: (None, None)
  size: (110, 35)
  text: ""
  color: hex('#000000')
  bgcolor: hex('#FFFFFF')
  canvas.before:
    Color:
      rgba: self.bgcolor
    Rectangle:
      pos: self.pos
      size: self.size
""")





class PoleTabeli(Label):        # Kolorowy Label, polecam do tabelek
    bgcolor = ObjectProperty(None)


class NowaSesja(Screen):
    def fade(self):     # Żeby fade był tylko przy okienku Rozpocznij
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()




class NowyKierowca(Screen):
    pass


class WybierzKierowce(Screen):
    pass


class Live(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):      # Funkcja co nam wypełnia tabele
        tab = self.ids.tabelaLive     # Layout tabeli
        bg = self.ids.plansza         # Layout Ekranu
        czas = self.ids.czas          # text input

        dane = []

        # Dane które powinny przyjść z bazy:
        dejtaSajens = [("Mateusz", "Makrela", "1:34", "005"),
                       ("Robert", "Kubica", f"{czas.text}", "001"),
                       ("Gabrysia", "Delicja", "1:32", "004"),
                       ("Hanna", "Mostowiak", "1:19", "002"),
                       ("Karolina", "Brzeczyszczykiewicz", "1:37", "003"),
                       ("Amadeusz", "Adamczyk", "1:21", "007"),
                       ("Kamil", "Kapucyn", "1:28", "Brak przypisanego RFID"),
                       ("Tomasz", "Karolak", "1:40", "006")]

        licznik = 0
        dane.clear()        # Czyszczenie listy przed aktualizacją danych
        for i in dejtaSajens:   # Wprowadzanie nowych danych do listy
            wartosc = dejtaSajens[licznik][2]   # wartosc służy do sortowania
            try:
                wartosc = wartosc.replace(":", "")  # Wywalamy dwukropki z czasu
                wartosc = int(wartosc)      # Zmieniamy string w liczbe
            except ValueError:
                wartosc = 9999     # Jak ktoś złe dane wprowadzi
            dane.append((dejtaSajens[licznik][0],
                         dejtaSajens[licznik][1],
                         dejtaSajens[licznik][2],
                         dejtaSajens[licznik][3],
                         wartosc))
            licznik += 1

        sortowane = sorted(dane, key=lambda data: data[4])  # Lista posortowana wg wartosci

        nazwa_wyscigu = "[RACE NAME]"     # Tutaj wrzucić nazwe wyscigu z bazy

        bg.add_widget(Label(text=f"Wyscig {nazwa_wyscigu}",
                            size_hint=(None,None),
                            pos_hint={"x":0.1,"y":0.85},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imie", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(130, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Status RFID", size=(170, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(80, 35)))

        # Wyświetlanie wierszy tabeli:
        licznik = 0
        for i in sortowane:
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=f"{licznik+1}", size=(85, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][0], size=(110, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][1], size=(150, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][2], size=(130, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][3], size=(170, 35)))
            tab.add_widget(Button(text="Wiecej", size_hint=(None, None), size=(80, 35)))
            licznik += 1


class PoprzednieSesje(Screen):
    pass


class HistoriaWyscigu(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaHistoria
        bg = self.ids.oknoHistoria

        connection = db.connect(user="postgres",
                                password="dejtasajens",
                                host="127.0.0.1",
                                port="5432",
                                database="Lapify")

        cursor = connection.cursor()

        cursor.execute("SELECT k.imie, k.nazwisko, w.data, w.nazwa_wyscigu\
                        FROM public.kierowca AS k\
                        JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                        JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu;")

        dane = cursor.fetchall()

        nazwa_wyscigu = dane[0][3]

        bg.add_widget(Label(text=f"Historia wyscigu {nazwa_wyscigu}",
                            size_hint=(None,None),
                            pos_hint={"x":0.45,"y":0.73},
                            font_size="24",
                            color=get_color_from_hex('#000000')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imie", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(130, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Data", size=(170, 35)))

        licznik = 0
        for i in dane:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik+1}", color=get_color_from_hex('ffffff'),
                           size=(85, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=dane[licznik][0], color=get_color_from_hex('ffffff'),
                           size=(110, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=dane[licznik][1], color=get_color_from_hex('ffffff'),
                           size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text="", color=get_color_from_hex('ffffff'),
                           size=(130, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][2]), color=get_color_from_hex('ffffff'),
                           size=(170, 35)))
            licznik += 1

        cursor.close()
        connection.close()



class Pomoc(Screen):
    pass


class TitleBar(Widget):
    pass


class Rozpocznij(Screen):
    def swap(self):
        Manager.transition = SwapTransition()

    def unswap(self):
        Manager.transition = NoTransition()

    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()


class Refresh(Screen):      # Pusty ekran na który na moment przełączamy się żeby odświeżyć
    pass


class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.transition = NoTransition()


kv = Builder.load_file("design.kv")


class DodajKierowce(FloatLayout):
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


class LapifyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driverReference = DodajKierowce()

    def build(self):
        return kv


if __name__ == '__main__':
    LapifyApp().run()

