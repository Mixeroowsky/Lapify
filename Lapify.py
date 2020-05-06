from kivy.config import Config
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
# Config.set('kivy', 'exit_on_escape', '0')
import psycopg2 as db
import datetime
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition, SwapTransition, FadeTransition
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

connection = db.connect(database="lapify", user="postgres", password="postgres")


class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableButton(RecycleDataViewBehavior, Button):
    ''' Add selection support to the Button '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)



    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected



class DatabaseConnecion:
    def __init__(self):
        try:
            # connect to db
            self.connection = db.connect(
                user="postgres",
                password="postgres",
                database="lapify"
            )
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()

        except (Exception, db.Error) as error:
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
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(85, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=data[licznik][0], size=(160, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=data[licznik][1], size=(160, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=data[licznik][2], size=(150, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text="00:05:23", size=(170, 35)))

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
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(85, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=sortowane[licznik][0], size=(110, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=sortowane[licznik][1], size=(150, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=sortowane[licznik][2], size=(130, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=sortowane[licznik][3], size=(170, 35)))
            tab.add_widget(Button(text="Wiecej", size_hint=(None, None), size=(80, 35)))
            licznik += 1


class PoprzednieSesje(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaPoprzednie
        bg = self.ids.oknoPoprzednie

        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        cursor = connection.cursor()

        cursor.execute("select id_wyscigu, nazwa_wyscigu, data_wyscigu from wyscig")
        dane = cursor.fetchall()

        bg.add_widget(Label(text=f"Historia wyscigow: ",
                            size_hint=(None, None),
                            pos_hint={"x": 0.09, "y": 0.84},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Numer wyscigu", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwa wyscigu", size=(300, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Data wyscigu", size=(157, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(120, 35)))

        licznik = 0
        for i in dane:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][0]),
                           color=get_color_from_hex('ffffff'),
                           size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][1]),
                           color=get_color_from_hex('ffffff'),
                           size=(300, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][2]),
                           color=get_color_from_hex('ffffff'),
                           size=(157, 35)))
            tab.add_widget(
                Button(text="Wiecej",
                       size_hint=(None, None),
                       size=(120, 35)))
            licznik += 1

        cursor.close()
        connection.close()


class Pomoc(Screen):
    pass


class TitleBar(Widget):
    pass

class HistoriaWyscigu(Screen):
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaHistoria
        bg = self.ids.oknoHistoria

        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

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



class Rozpocznij(Screen):
    def swap(self):
        Manager.transition = SwapTransition()

    def input(self):
        nazwa_wyscigu = self.ids.wyscig

        cursor = connection.cursor()
        cursor.execute("select id_wyscigu, nazwa_wyscigu, data_wyscigu from wyscig")
        rows = cursor.fetchall()
        cursor.execute("insert into wyscig (id_wyscigu, nazwa_wyscigu, data_wyscigu ) values (%s, %s, %s);commit",
                       (len(rows) + 1, nazwa_wyscigu.text, datetime.date.today()))
        cursor.close()

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


class DodajKierowce(Screen):
    def add_driver(self):
        grid = self.ids.list


        imie = self.ids.name.text
        nazwisko = self.ids.last_name.text
        model = self.ids.model.text
        kategoria = self.ids.category.text
        rfid = self.ids.tag.text
        list = BoxLayout(size_hint_y=None, height=30, pos_hint={'top': .5})
        grid.add_widget(list)



        imie = Label(text=imie, size_hint_x=.2)
        nazwisko = Label(text=nazwisko, size_hint_x=.2)
        rfid = Label(text=rfid,size_hint_x=.2)
        model = Label(text=model, size_hint_x=.2)
        kategoria = Label(text=kategoria, size_hint_x=.2)
        empty = Label(text="", size_hint_x=.3)




        list.add_widget(imie)
        list.add_widget(nazwisko)
        list.add_widget(model)
        list.add_widget(kategoria)
        list.add_widget(rfid)
        list.add_widget(empty)



        connection = db.connect(
            database="lapify",
            user="postgres",
            password="postgres")

        cursor = connection.cursor()
        cursor.execute("SELECT id_kierowcy, imie, nazwisko, model_samochodu,kategoria FROM kierowca ")
        rows = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("SELECT id_przypisania, id_wyscigu, id_kierowcy, rfid FROM przypisanie ")
        t = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute(" INSERT INTO kierowca ( id_kierowcy, imie, nazwisko, model_samochodu, kategoria) VALUES (%s,%s,%s,%s,%s)",
                       (len(rows) + 1, self.ids.name.text, self.ids.last_name.text,self.ids.model.text,
                        self.ids.category.text))
        cursor.execute("INSERT INTO przypisanie (id_kierowcy,rfid,id_przypisania ) VALUES (%s,%s,%s)",
                       (len(rows)+1,self.ids.tag.text,len(t)+1)

                       )
        connection.commit()
        connection.close()


kv = Builder.load_file("design.kv")


class LapifyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        return kv


if __name__ == '__main__':
    database_connection = DatabaseConnecion()
    database_connection.getData()
    database_connection.getWyscig()
    LapifyApp().run()
