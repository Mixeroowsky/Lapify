import psycopg2
from kivy.config import Config  # Ta sekcja musi być na górze

Config.set('graphics', 'resizable', False)  # Fullscreen
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # Brak czerwonych kropek
# Config.set('kivy', 'exit_on_escape', '0')

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

dane = []  # Przyda sie potem
data = []
wyscig = []


class DatabaseConnecion:
    def __init__(self):
        try:
            # connect to db
            self.connection = psycopg2.connect(
                user="postgres",
                password="postgresql",
                host='localhost',
                port="5432",
                database="lapify"
            )
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()

        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def getData(self):
        # pobieranie danych do ostatniej sesji
        data_command = "select k.imie, k.nazwisko, k.model_samochodu " \
                       "from kierowca k " \
                       "    join przypisanie p " \
                       "    on k.id_kierowcy = p.id_kierowcy " \
                       "    join wyscig w " \
                       "    on p.id_wyscigu=w.id_wyscigu " \
                       "where w.data_wyscigu=(select max(data_wyscigu) from wyscig)"
        self.cursor.execute(data_command)
        all = self.cursor.fetchall()

        licznik = 0
        for a in all:
            data.append((a[0], a[1], a[2]))

        # pobieranie danych o ostatnim wyscigu

    def getWyscig(self):
        nazwa_wyscigu = "select nazwa_wyscigu, data_wyscigu " \
                        "from wyscig " \
                        "where data_wyscigu = (select max(data_wyscigu) from wyscig)"

        self.cursor.execute(nazwa_wyscigu)
        all = self.cursor.fetchall()

        for a in all:
            wyscig.append((a[0], a[1]))


class PoleTabeli(Label):  # Kolorowy Label, polecam do tabelek
    bgcolor = ObjectProperty(None)


class NowaSesja(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def fade(self):  # Żeby fade był tylko przy okienku Rozpocznij
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    # dane do tabeli
    def generujtabele(self):
        tabela = self.ids.tabelaOstatniaSesja
        ekran = self.ids.p_ostatnia_sesja

        nazwa_wyscigu = str(wyscig[0][0])
        data_wyscigu = str(wyscig[0][1])

        ekran.add_widget(Label(text=f"{str(nazwa_wyscigu)}",
                               size_hint=(None, None),
                               pos_hint={"x": 0.27, "y": 0.8},
                               font_size="30",
                               color=get_color_from_hex('#EF8B00')))

        ekran.add_widget(Label(text=f"{str(data_wyscigu)}",
                               size_hint=(None, None),
                               pos_hint={"x": 0.27, "y": 0.75},
                               font_size="15",
                               color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Miejsce", size=(85, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Imie", size=(160, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Nazwisko", size=(160, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Model samochodu", size=(150, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Czas okrazenia", size=(170, 35)))

        licznik = 0
        all = len(data)
        for i in range(all):
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=f"{licznik + 1}", size=(85, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=data[licznik][0], size=(160, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=data[licznik][1], size=(160, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=data[licznik][2], size=(150, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text="00:05:23", size=(170, 35)))

            licznik += 1


class NowyKierowca(Screen):
    pass


class WybierzKierowce(Screen):
    pass


class Live(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):  # Funkcja co nam wypełnia tabele
        tab = self.ids.tabelaLive  # Layout tabeli
        bg = self.ids.plansza  # Layout Ekranu
        czas = self.ids.czas  # text input

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
        dane.clear()  # Czyszczenie listy przed aktualizacją danych
        for i in dejtaSajens:  # Wprowadzanie nowych danych do listy
            wartosc = dejtaSajens[licznik][2]  # wartosc służy do sortowania
            try:
                wartosc = wartosc.replace(":", "")  # Wywalamy dwukropki z czasu
                wartosc = int(wartosc)  # Zmieniamy string w liczbe
            except ValueError:
                wartosc = 9999  # Jak ktoś złe dane wprowadzi
            dane.append((dejtaSajens[licznik][0],
                         dejtaSajens[licznik][1],
                         dejtaSajens[licznik][2],
                         dejtaSajens[licznik][3],
                         wartosc))
            licznik += 1

        sortowane = sorted(dane, key=lambda data: data[4])  # Lista posortowana wg wartosci

        nazwa_wyscigu = "[RACE NAME]"  # Tutaj wrzucić nazwe wyscigu z bazy

        bg.add_widget(Label(text=f"Wyscig {nazwa_wyscigu}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.1, "y": 0.85},
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
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=f"{licznik + 1}", size=(85, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][0], size=(110, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][1], size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][2], size=(130, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#B0B0B0'), text=sortowane[licznik][3], size=(170, 35)))
            tab.add_widget(Button(text="Wiecej", size_hint=(None, None), size=(80, 35)))
            licznik += 1


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
        Manager.transition = NoTransition()

    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()


class Refresh(Screen):  # Pusty ekran na który na moment przełączamy się żeby odświeżyć
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
    database_connection = DatabaseConnecion()
    database_connection.getData()
    database_connection.getWyscig()
    LapifyApp().run()
