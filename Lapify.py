from kivy.config import Config
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
# Config.set('kivy', 'exit_on_escape', '0')
import psycopg2 as db
from _datetime import datetime, date
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition, SwapTransition, FadeTransition
from kivy.utils import get_color_from_hex
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup


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
<HistoriaButton>:
  background_down: 'graphics/pressed.png'
  id: 0
  on_release: 
    app.root.switch(self.id)
    app.root.current = "historia"
<KierowcaButton>:
  background_down: 'graphics/pressed.png'
  id: 0
  on_release: 
    app.root.switch(self.id)
    app.root.current = "kierowca"
<OkrazenieButton>:
  background_down: 'graphics/pressed.png'
  id: 0
  enum_id: 0
  on_release: 
    app.root.inside_switch(self.id)
    app.root.enum_switch(self.enum_id)
    app.root.current = "okrazenie"
""")

number = 0
number_update = 0
inside_number = 0
enum_number = 0

dane = []  # Przyda sie potem
okrazenie = []
wyscig = []
sortowane_ok = []

connection = db.connect(database="lapify", user="postgres", password="postgres")


class PoleTabeli(Label):  # Kolorowy Label, polecam do tabelek
    bgcolor = ObjectProperty(None)


class PolaczButton(Button):
    id = ObjectProperty(None)


class HistoriaButton(Button):
    id = ObjectProperty(None)


class KierowcaButton(Button):
    id = ObjectProperty(None)


class OkrazenieButton(Button):
    id = ObjectProperty(None)
    enum_id = ObjectProperty(None)


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
        data_command = "select  distinct p.id_ok, k.imie, k.nazwisko, k.model_samochodu, k.kategoria, (bramka3-bramka1) as okrazenie " \
                       "from  przejazd p join " \
                       "(select id_ok, czas as bramka1 from przejazd where id_bramki = 1 )a " \
                       "on p.id_ok = a.id_ok " \
                       "join przypisanie przy " \
                       "on przy.id_przypisania = p.id_przypisania " \
                       "join " \
                       "(select id_ok, czas as bramka3 from przejazd where id_bramki = 3)b " \
                       "on b.id_ok = p.id_ok " \
                       "join kierowca k  " \
                       "on przy.id_kierowcy = k.id_kierowcy " \
                       "join wyscig w " \
                       "on przy.id_wyscigu = w.id_wyscigu " \
                       "where w.data_wyscigu=(select max(data_wyscigu) from wyscig) ; "
        self.cursor.execute(data_command)

        all_data = self.cursor.fetchall()

        licznik = 0
        for a in all_data:
            okrazenie.append((a[0], a[1], a[2], a[3], a[4], a[5]))

        # pobieranie danych o ostatnim wyscigu

    def getWyscig(self):
        nazwa_wyscigu = "select nazwa_wyscigu, data_wyscigu " \
                        "from wyscig " \
                        "where data_wyscigu = (select max(data_wyscigu) from wyscig)"

        self.cursor.execute(nazwa_wyscigu)
        all_data = self.cursor.fetchall()

        for a in all_data:

            wyscig.append((a[0], a[1]))

class Startowa(Screen):
    def skip(self, dt):
        self.manager.current = "nowa"

    def on_enter(self, *args):
        Clock.schedule_once(self.skip, 1)


class NowaSesja(Screen):

    text1 = "Strona główna"
    text2 = "Rozpocznij nową sesję"


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

        licznik = 0
        sortowane_ok.clear()  # Czyszczenie listy przed aktualizacją danych
        for i in okrazenie:  # Wprowadzanie nowych danych do listy
            wartosc = str(okrazenie[licznik][5])  # wartosc służy do sortowania

            try:
                wartosc = wartosc.replace(":", "")  # Wywalamy dwukropki z czasu
                wartosc = int(wartosc)  # Zmieniamy string w liczbe
            except ValueError:
                wartosc = 9999  # Jak ktoś złe dane wprowadzi
            sortowane_ok.append((okrazenie[licznik][0],
                                 okrazenie[licznik][1],
                                 okrazenie[licznik][2],
                                 okrazenie[licznik][3],
                                 okrazenie[licznik][4],
                                 wartosc))
            licznik += 1

        sortowanie = sorted(sortowane_ok, key=lambda data: data[5])  # Lista posortowana wg wartosci

        # Wyświetlanie tytułów tabeli:

        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Miejsce", size=(70, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Imie", size=(120, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Nazwisko", size=(150, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="      Model \nsamochodu", size=(170, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Kategoria", size=(125, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="    Czas \nokrazenia", size=(90, 35)))

        licznik = 0
        all = len(okrazenie)
        for i in sortowanie:
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(70, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][1],
                                         size=(120, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][2],
                                         size=(150, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][3],
                                         size=(170, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][4],
                                         size=(125, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=str(sortowanie[licznik][5]),
                                         size=(90, 35)))

            licznik += 1


class NowyKierowca(Screen):
    pass



class Live(Screen):
    text1 = "Strona główna"
    text2 = "Dodaj kierowcę"

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def fade(self):  # Żeby fade był tylko przy okienku Rozpocznij
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    def generuj(self):  # Funkcja co nam wypełnia tabele
        tab = self.ids.tabelaLive  # Layout tabeli
        bg = self.ids.plansza  # Layout Ekranu
        dejtaSajens = []

        cursor = connection.cursor()

        data_command = "select distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu,\
                       (bramkaKoniec-bramkaPoczatek) as okrazenie, k.kategoria, r.rfid \
                       from kierowca k \
                       join przypisanie r  \
                       on k.id_kierowcy = r.id_kierowcy  \
                       join przejazd p \
                       on r.id_przypisania = p.id_przypisania \
                       join (select id_ok, czas as bramkaPoczatek from przejazd  \
                       where id_bramki = (select min(distinct id_bramki) from przejazd \
                       join przypisanie on przejazd.id_przypisania = przypisanie.id_przypisania \
                       join wyscig on przypisanie.id_wyscigu = wyscig.id_wyscigu \
                       where wyscig.data_wyscigu=(select max(data_wyscigu) from wyscig)) )a  \
                       on p.id_ok = a.id_ok  \
                       join (select id_ok, czas as bramkaKoniec from przejazd  \
                       where id_bramki = (select max(distinct id_bramki) from przejazd \
                       join przypisanie on przejazd.id_przypisania = przypisanie.id_przypisania \
                       join wyscig on przypisanie.id_wyscigu = wyscig.id_wyscigu \
                       where wyscig.data_wyscigu=(select max(data_wyscigu) from wyscig)) )b  \
                       on b.id_ok = p.id_ok  \
                       join wyscig w  \
                       on r.id_wyscigu = w.id_wyscigu  \
                       where w.data_wyscigu=(select max(data_wyscigu) from wyscig) ; "

        cursor.execute(data_command)

        dejtaSajens.clear()
        dejtaSajens = cursor.fetchall()

        unikalne_id = []
        unikalny_kierowca = []

        for i in range(0, len(dejtaSajens)):
            if dejtaSajens[i][0] not in unikalne_id:
                unikalne_id.append(dejtaSajens[i][0])
                unikalny_kierowca.append(dejtaSajens[i])
                continue
            else:
                for j in range(0, i):
                    if dejtaSajens[i][0] == unikalny_kierowca[j][0] \
                            and dejtaSajens[i][4] < unikalny_kierowca[j][4]:
                        unikalny_kierowca[j] = dejtaSajens[i]
                        continue

        sortowane = sorted(unikalny_kierowca, key=lambda data: data[4])  # Lista posortowana wg wartosci

        nazwa_wyscigu = "select nazwa_wyscigu, data_wyscigu " \
                        "from wyscig " \
                        "where data_wyscigu = (select max(data_wyscigu) from wyscig)"

        cursor.execute(nazwa_wyscigu)
        all_data = cursor.fetchall()
        wyscig.clear()

        for a in all_data:
            wyscig.append((a[0], a[1]))

        nazwa_wyscigu = f"{str(wyscig[len(wyscig) - 1][0])}"

        bg.add_widget(Label(text=f"Wyścig {nazwa_wyscigu}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.15, "y": 0.85},

                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(140, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(160, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Status RFID", size=(100, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(80, 35)))

        # Wyświetlanie wierszy tabeli:
        licznik = 0
        for i in sortowane:
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                      color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(85, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][0]), size=(110, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][1]), size=(150, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][2]), size=(140, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][3]), size=(120, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][4]), size=(160, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][5]), size=(100, 35)))
            tab.add_widget(KierowcaButton(text="Więcej", size_hint=(None, None), size=(80, 35),
                                          id=int(sortowane[licznik][0])))
            licznik += 1
        cursor.close()


class WynikiKierowcy(Screen):
    text1 = "Strona główna"
    text2 = "Powrót"

    def generuj(self):
        tab = self.ids.tabelaKierowca
        bg = self.ids.planszaKierowca

        cursor = connection.cursor()

        data_command = f"select distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu,\
                       (bramkaKoniec-bramkaPoczatek) as okrazenie, k.kategoria, w.nazwa_wyscigu, p.id_ok \
                       from kierowca k  \
                       join przypisanie r  \
                       on k.id_kierowcy = r.id_kierowcy  \
                       join przejazd p \
                       on r.id_przypisania = p.id_przypisania \
                       join (select id_ok, czas as bramkaPoczatek from przejazd  \
                       where id_bramki = (select min(distinct id_bramki) from przejazd) )a  \
                       on p.id_ok = a.id_ok  \
                       join (select id_ok, czas as bramkaKoniec from przejazd  \
                       where id_bramki = (select max(distinct id_bramki) from przejazd) )b  \
                       on b.id_ok = p.id_ok  \
                       join wyscig w  \
                       on r.id_wyscigu = w.id_wyscigu  \
                       where w.data_wyscigu=(select max(data_wyscigu) from wyscig) \
                       AND k.id_kierowcy = {number};"

        cursor.execute(data_command)

        wyniki = cursor.fetchall()

        bg.add_widget(Label(text=f"Wyścig {wyniki[0][6]}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.15, "y": 0.8},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text=f"{wyniki[0][1]} {wyniki[0][2]}",
                                  size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][3]}", size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][5]}", size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 3)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Numer okrążenia", size=(151, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Czas okrążenia", size=(699, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))

        licznik = 0
        for i in wyniki:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik + 1}",
                           color=get_color_from_hex('ffffff'),
                           size=(151, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(wyniki[licznik][4]),
                           color=get_color_from_hex('ffffff'),
                           size=(699, 35)))
            tab.add_widget(OkrazenieButton(text="Szczegóły", size_hint=(None, None), size=(100, 35),
                                          id=int(wyniki[licznik][7]), enum_id=licznik+1))
            licznik += 1
        cursor.close()
        wyniki.clear()


class SzczegolyOkrazenia(Screen):
    text1 = "Strona główna"
    text2 = "Powrót"

    def generuj(self):
        tab = self.ids.tabelaOkrazenia
        bg = self.ids.planszaOkrazenia

        cursor = connection.cursor()

        cursor.execute(f"SELECT k.imie, k.nazwisko, k.model_samochodu, r.czas, k.kategoria, w.nazwa_wyscigu\
                               FROM public.kierowca AS k\
                               JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                               JOIN public.przejazd AS r ON p.id_przypisania = r.id_przypisania\
                               JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu\
                               WHERE data_wyscigu = (select max(data_wyscigu) from wyscig)\
                               AND r.id_ok = {inside_number};"
                       )

        wyniki = cursor.fetchall()

        czasy = []
        odcinki = []

        licznik = 0
        for i in wyniki:
            czasy.append(wyniki[licznik][3])
            licznik += 1

        for i in range(0, len(czasy)-1):
            duration = datetime.combine(date.min, czasy[i+1]) - datetime.combine(date.min, czasy[i])
            odcinki.append(duration)

        bg.add_widget(Label(text=f"Wyścig {wyniki[0][5]}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.15, "y": 0.8},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text=f"{wyniki[0][0]} {wyniki[0][1]}",
                                  size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][2]}", size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][4]}", size=(952, 35)))
        #tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 3)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(151, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'),
                                  text=f"Okrążenie {enum_number}", size=(699, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(100, 35)))
        #tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 1.5)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Odcinek trasy", size=(151, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Czas na odcinku", size=(699, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))

        licznik = 0
        for i in odcinki:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik + 1}",
                           color=get_color_from_hex('ffffff'),
                           size=(151, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(odcinki[licznik]),
                           color=get_color_from_hex('ffffff'),
                           size=(699, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))
            licznik += 1
        cursor.close()
        wyniki.clear()


class PoprzednieSesje(Screen):
    text1 = "Strona główna"


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

        bg.add_widget(Label(text=f"Historia wyścigów: ",
                            size_hint=(None, None),
                            pos_hint={"x": 0.09, "y": 0.84},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Numer wyścigu", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwa wyścigu", size=(300, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Data wyścigu", size=(157, 35)))
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
                HistoriaButton(text="Więcej",
                               size_hint=(None, None),
                               size=(120, 35),
                               id=int(dane[licznik][0])
                              ))
            licznik += 1

        cursor.close()
        connection.close()


class Pomoc(Screen):
    text1 = "Strona główna"
    text2 = "W przypadku problemów z aplikacją \n                 prosimy o kontakt:"
    text3 = "Aleksandra Chudzińska"
    text4 = "Mikołaj Stojek"
    text5 = "Anna Zięba"


class TitleBar(Widget):
    pass


class HistoriaWyscigu(Screen):
    text1 = "Strona główna"
    text2 = 'Wróć'

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaHistoria
        bg = self.ids.oknoHistoria

        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        cursor = connection.cursor()


        cursor.execute("SELECT k.imie, k.nazwisko, k.model_samochodu, k.kategoria, w.data_wyscigu, w.nazwa_wyscigu\
                        FROM public.kierowca AS k\
                        JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                        JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu"
                       f"    where w.id_wyscigu = {number} ;")

        dane = cursor.fetchall()

        nazwa_wyscigu = dane[0][5]
        data = dane[0][4]

        bg.add_widget(Label(text=f"Historia wyścigu {nazwa_wyscigu}",
                            size_hint=(None,None),
                            pos_hint={"x":0.45,"y":0.755},
                            font_size="24",
                            color=get_color_from_hex('#000000')))

        bg.add_widget(Label(text=f"Data: {data}",
                            size_hint=(None,None),
                            pos_hint={"x":0.24,"y":0.7},
                            font_size="20",
                            color=get_color_from_hex('#000000')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(170, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(130, 35)))

        licznik = 0
        for i in dane:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik+1}", color=get_color_from_hex('ffffff'),
                           size=(85, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][0]), color=get_color_from_hex('ffffff'),
                           size=(110, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][1]), color=get_color_from_hex('ffffff'),
                           size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][2]), color=get_color_from_hex('ffffff'),
                           size=(170, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text="", color=get_color_from_hex('ffffff'),
                           size=(120, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][3]), color=get_color_from_hex('ffffff'),
                           size=(130, 35)))

            licznik += 1

        cursor.close()


class Bramki(Screen):
    def swap(self):
        Manager.transition = SwapTransition()

    def input(self):
        bramka_start = self.ids.start
        bramka_srodek = self.ids.srodek
        bramka_meta = self.ids.meta

        cursor = connection.cursor()
        cursor.execute("select id_bramki, nr_bramki from public.bramka")
        dane = cursor.fetchall()

        input1 = int(bramka_start.text)
        input2 = int(bramka_srodek.text)
        input3 = int(bramka_meta.text)

        cursor.execute("UPDATE public.bramka SET nr_bramki=%s WHERE id_bramki =1; commit",[input1])
        cursor.execute("UPDATE public.bramka SET nr_bramki=%s WHERE id_bramki =2; commit",[input2])
        cursor.execute("UPDATE public.bramka SET nr_bramki=%s WHERE id_bramki =3; commit",[input3])

        cursor.close()
        connection.close()

    def unswap(self):
        Manager.transition = NoTransition()

    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()


class Rozpocznij(Screen):
    text1 = "Strona główna"
    text2 = "Nazwa wyścigu:"
    text3 = "Dodaj kierowcę"
    text4 = "Wybierz kierowcę"

    def swap(self):
        Manager.transition = SwapTransition()

    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    error = Popup(title='Wpisz nazwę wyścigu!',
                  title_align='center',
                  title_size=16,
                  content=content,
                  size_hint=(None, None), size=(220, 100),
                  auto_dismiss=False,
                  separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])
    content.bind(on_release=error.dismiss)

    def input(self):
        nazwa_wyscigu = self.ids.wyscig

        if nazwa_wyscigu.text == "":
            self.error.open()
        else:
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

text_input = []
text_id = []

class PolaczRFID(Screen):      # Pusty ekran na który na moment przełączamy się żeby odświeżyć
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaRFID

        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        cursor = connection.cursor()

        cursor.execute("SELECT distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu,  p.rfid\
                                  FROM public.kierowca AS k\
                                  LEFT JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                                  JOIN public.przejazd AS r ON p.id_przypisania = r.id_przypisania")

        daner = cursor.fetchall()
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="ID", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(170, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="RFID", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(130, 35)))
        licznik = 0
        global text_input
        for i in daner:
            text_id.append(daner[licznik][0])
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][0]),
                           color=get_color_from_hex('ffffff'),
                           size=(85, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][1]),
                                      color=get_color_from_hex('ffffff'),
                                      size=(110, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][2]),
                           color=get_color_from_hex('ffffff'),
                           size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][3]),
                           color=get_color_from_hex('ffffff'),
                           size=(170, 35)))
            text_input.append(TextInput(size_hint=(None, None), size=(120, 35)))
            tab.add_widget(text_input[licznik])
            tab.add_widget(
                PolaczButton(id=licznik, text="Polacz", size_hint=(None, None), size=(130, 35),
                             on_release=lambda x: self.update()))

            licznik += 1

    def update(self):
        global text_input
        global text_id
        global number
        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        text = text_input[number].text

        cursor = connection.cursor()
        cursor.execute("SELECT id_przypisania, id_wyscigu, id_kierowcy, rfid FROM przypisanie ")
        t = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("select id_wyscigu " \
                       "from wyscig " \
                       "where data_wyscigu = (select max(data_wyscigu) from wyscig)")

        b = cursor.fetchall()
        print(b)

        cursor = connection.cursor()
        cursor.execute("INSERT INTO przypisanie (id_przypisania, id_wyscigu, id_kierowcy, rfid) VALUES (%s,%s,%s,%s)",
                       (len(t) + 1, b[0], text_id[number], text))
        # cursor.execute(f"UPDATE public.przypisanie SET rfid = %s WHERE id_kierowcy={text_id[number]} ; commit", [text])
        print(text)
        cursor.close()
        connection.commit()
        connection.close()


class Manager(ScreenManager):

    @staticmethod
    def switch(x):
        global number
        number = x

    @staticmethod
    def inside_switch(x):
        global inside_number
        inside_number = x

    @staticmethod
    def enum_switch(x):
        global enum_number
        enum_number = x

    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.transition = NoTransition()


class DodajKierowce(Screen):

    def clear_inputs(self, text_inputs):
        for text_input in text_inputs:
            text_input.text = ""

    def unswap(self):
        Manager.transition = NoTransition()

    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    text1 = "Strona główna"
    text2 = "Dodawanie kierowców"
    text3 = "Imię"


    def add_driver(self):
        grid = self.ids.list
        imie = self.ids.name.text
        nazwisko = self.ids.last_name.text
        model = self.ids.model.text
        kategoria = self.ids.category.text

        list = BoxLayout(size_hint_y=None, height=50, pos_hint={'top': .5})
        grid.add_widget(list)

        imie = Label(text=imie, size_hint_x=.2)
        nazwisko = Label(text=nazwisko, size_hint_x=.2)
        model = Label(text=model, size_hint_x=.2)
        kategoria = Label(text=kategoria, size_hint_x=.2)
        empty = Label(text="", size_hint_x=.3)

        list.add_widget(imie)
        list.add_widget(nazwisko)
        list.add_widget(model)
        list.add_widget(kategoria)
        list.add_widget(empty)

        connection = db.connect(
            database="lapify",
            user="postgres",
            password="postgres")

        cursor = connection.cursor()
        cursor.execute("SELECT id_kierowcy, imie, nazwisko, model_samochodu,kategoria FROM kierowca ")
        rows = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("SELECT id_wyscigu FROM wyscig WHERE data_wyscigu = (select max(data_wyscigu) from wyscig) ")
        b = cursor.fetchall()


        cursor = connection.cursor()
        cursor.execute(" INSERT INTO kierowca ( id_kierowcy, imie, nazwisko, model_samochodu, kategoria) VALUES (%s,%s,%s,%s,%s)",
                       (len(rows) + 1, self.ids.name.text, self.ids.last_name.text,self.ids.model.text,
                        self.ids.category.text))

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
    connection.close()
=======
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
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition, SwapTransition, FadeTransition
from kivy.utils import get_color_from_hex
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup


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
<HistoriaButton>:
  background_down: 'graphics/pressed.png'
  id: 0
  on_release: 
    app.root.switch(self.id)
    app.root.current = "historia"
""")

number = 0
number_update = 0
dane = []  # Przyda sie potem
okrazenie = []
wyscig = []
sortowane_ok = []

connection = db.connect(database="lapify", user="postgres", password="postgres")


class PoleTabeli(Label):  # Kolorowy Label, polecam do tabelek
    bgcolor = ObjectProperty(None)


class PolaczButton(Button):
    id = ObjectProperty(None)


class HistoriaButton(Button):
    id = ObjectProperty(None)


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
        data_command = "select  distinct p.id_ok, k.imie, k.nazwisko, k.model_samochodu, k.kategoria, (bramka3-bramka1) as okrazenie " \
                       "from  przejazd p join " \
                       "(select id_ok, czas as bramka1 from przejazd where id_bramki = 1 )a " \
                       "on p.id_ok = a.id_ok " \
                       "join przypisanie przy " \
                       "on przy.id_przypisania = p.id_przypisania " \
                       "join " \
                       "(select id_ok, czas as bramka3 from przejazd where id_bramki = 3)b " \
                       "on b.id_ok = p.id_ok " \
                       "join kierowca k  " \
                       "on przy.id_kierowcy = k.id_kierowcy " \
                       "join wyscig w " \
                       "on przy.id_wyscigu = w.id_wyscigu " \
                       "where w.data_wyscigu=(select max(data_wyscigu) from wyscig) ; "
        self.cursor.execute(data_command)

        all_data = self.cursor.fetchall()

        licznik = 0
        for a in all_data:
            okrazenie.append((a[0], a[1], a[2], a[3], a[4], a[5]))

        # pobieranie danych o ostatnim wyscigu

    def getWyscig(self):
        nazwa_wyscigu = "select nazwa_wyscigu, data_wyscigu " \
                        "from wyscig " \
                        "where data_wyscigu = (select max(data_wyscigu) from wyscig)"

        self.cursor.execute(nazwa_wyscigu)
        all_data = self.cursor.fetchall()

        for a in all_data:

            wyscig.append((a[0], a[1]))

class Startowa(Screen):
    def skip(self, dt):
        self.manager.current = "nowa"

    def on_enter(self, *args):
        Clock.schedule_once(self.skip, 1)


class NowaSesja(Screen):

    text1 = "Strona główna"
    text2 = "Rozpocznij nową sesję"


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

        licznik = 0
        sortowane_ok.clear()  # Czyszczenie listy przed aktualizacją danych
        for i in okrazenie:  # Wprowadzanie nowych danych do listy
            wartosc = str(okrazenie[licznik][5])  # wartosc służy do sortowania

            try:
                wartosc = wartosc.replace(":", "")  # Wywalamy dwukropki z czasu
                wartosc = int(wartosc)  # Zmieniamy string w liczbe
            except ValueError:
                wartosc = 9999  # Jak ktoś złe dane wprowadzi
            sortowane_ok.append((okrazenie[licznik][0],
                                 okrazenie[licznik][1],
                                 okrazenie[licznik][2],
                                 okrazenie[licznik][3],
                                 okrazenie[licznik][4],
                                 wartosc))
            licznik += 1

        sortowanie = sorted(sortowane_ok, key=lambda data: data[5])  # Lista posortowana wg wartosci

        # Wyświetlanie tytułów tabeli:

        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Miejsce", size=(70, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Imie", size=(120, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Nazwisko", size=(150, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="      Model \nsamochodu", size=(170, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="Kategoria", size=(125, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#E27814'), text="    Czas \nokrazenia", size=(90, 35)))

        licznik = 0
        all = len(okrazenie)
        for i in sortowanie:
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(70, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][1],
                                         size=(120, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][2],
                                         size=(150, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][3],
                                         size=(170, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=sortowanie[licznik][4],
                                         size=(125, 35)))
            tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                         color=get_color_from_hex('ffffff'), text=str(sortowanie[licznik][5]),
                                         size=(90, 35)))

            licznik += 1


class NowyKierowca(Screen):
    pass



class Live(Screen):
    text1 = "Strona główna"
    text2 = "Dodaj kierowcę"

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def fade(self):  # Żeby fade był tylko przy okienku Rozpocznij
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    def generuj(self):  # Funkcja co nam wypełnia tabele
        tab = self.ids.tabelaLive  # Layout tabeli
        bg = self.ids.plansza  # Layout Ekranu


        # Dane które powinny przyjść z bazy:
        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        cursor = connection.cursor()

        cursor.execute("SELECT k.imie, k.nazwisko, k.model_samochodu,r.czas, k.kategoria, p.rfid\
                               FROM public.kierowca AS k\
                               JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                               JOIN public.przejazd AS r ON p.id_przypisania = r.id_przypisania\
                               JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu WHERE data_wyscigu = (select max(data_wyscigu) from wyscig) "

                       )

        dejtaSajens = cursor.fetchall()

        licznik = 0
        dane.clear()  # Czyszczenie listy przed aktualizacją danych
        for i in dejtaSajens:  # Wprowadzanie nowych danych do listy
            wartosc =str(dejtaSajens[licznik][3]) # wartosc służy do sortowania
            #print(type(wartosc))
            try:
                wartosc = wartosc.replace(":"," ")  # Wywalamy dwukropki z czasu
                wartosc = int(wartosc)  # Zmieniamy string w liczbe
            except ValueError:
                wartosc = 9999  # Jak ktoś złe dane wprowadzi
            dane.append((dejtaSajens[licznik][0],
                         dejtaSajens[licznik][1],
                         dejtaSajens[licznik][2],
                         dejtaSajens[licznik][3],
                         dejtaSajens[licznik][4],
                         dejtaSajens[licznik][5],
                         wartosc))
            licznik += 1

        sortowane = sorted(dane, key=lambda data: data[6])  # Lista posortowana wg wartosci

        try:
            # connect to db
            self.connection = db.connect(user="postgres", password="postgres", database="lapify")
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()

        except (Exception, db.Error) as error:
            print("Error while connecting to PostgreSQL", error)

        nazwa_wyscigu = "select nazwa_wyscigu, data_wyscigu " \
                        "from wyscig " \
                        "where data_wyscigu = (select max(data_wyscigu) from wyscig)"

        self.cursor.execute(nazwa_wyscigu)
        all_data = self.cursor.fetchall()
        wyscig.clear()

        for a in all_data:
            wyscig.append((a[0], a[1]))

        nazwa_wyscigu = f"{str(wyscig[len(wyscig) - 1][0])}"

        bg.add_widget(Label(text=f"Wyścig {nazwa_wyscigu}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.15, "y": 0.85},

                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(140, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(160, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Status RFID", size=(100, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(80, 35)))

        # Wyświetlanie wierszy tabeli:
        licznik = 0
        for i in sortowane:
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                      color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(85, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][0]), size=(110, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][1]), size=(150, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][2]), size=(140, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][3]), size=(120, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][4]), size=(160, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                           color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][5]), size=(100, 35)))

            tab.add_widget(Button(text="Więcej", size_hint=(None, None), size=(80, 35)))

            licznik += 1


class PoprzednieSesje(Screen):
    text1 = "Strona główna"


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

        bg.add_widget(Label(text=f"Historia wyścigów: ",
                            size_hint=(None, None),
                            pos_hint={"x": 0.09, "y": 0.84},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Numer wyścigu", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwa wyścigu", size=(300, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Data wyścigu", size=(157, 35)))
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
                HistoriaButton(text="Więcej",
                               size_hint=(None, None),
                               size=(120, 35),
                               id=int(dane[licznik][0])
                              ))
            licznik += 1

        cursor.close()
        connection.close()




class Pomoc(Screen):
    text1 = "Strona główna"
    text2 = "W przypadku problemów z aplikacją \n                 prosimy o kontakt:"
    text3 = "Aleksandra Chudzińska"
    text4 = "Mikołaj Stojek"
    text5 = "Anna Zięba"


class TitleBar(Widget):
    pass


class HistoriaWyscigu(Screen):
    text1 = "Strona główna"
    text2 = 'Wróć'

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaHistoria
        bg = self.ids.oknoHistoria

        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        cursor = connection.cursor()


        cursor.execute("SELECT k.imie, k.nazwisko, k.model_samochodu, k.kategoria, w.data_wyscigu, w.nazwa_wyscigu\
                        FROM public.kierowca AS k\
                        JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                        JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu"
                       f"    where w.id_wyscigu = {number} ;")

        dane = cursor.fetchall()

        nazwa_wyscigu = dane[0][5]
        data = dane[0][4]

        bg.add_widget(Label(text=f"Historia wyścigu {nazwa_wyscigu}",
                            size_hint=(None,None),
                            pos_hint={"x":0.45,"y":0.755},
                            font_size="24",
                            color=get_color_from_hex('#000000')))

        bg.add_widget(Label(text=f"Data: {data}",
                            size_hint=(None,None),
                            pos_hint={"x":0.24,"y":0.7},
                            font_size="20",
                            color=get_color_from_hex('#000000')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(170, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(130, 35)))

        licznik = 0
        for i in dane:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik+1}", color=get_color_from_hex('ffffff'),
                           size=(85, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][0]), color=get_color_from_hex('ffffff'),
                           size=(110, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][1]), color=get_color_from_hex('ffffff'),
                           size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][2]), color=get_color_from_hex('ffffff'),
                           size=(170, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text="", color=get_color_from_hex('ffffff'),
                           size=(120, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(dane[licznik][3]), color=get_color_from_hex('ffffff'),
                           size=(130, 35)))

            licznik += 1

        cursor.close()
        connection.close()

class Bramki(Screen):
    def swap(self):
        Manager.transition = SwapTransition()

    def input(self):
        bramka_start = self.ids.start
        bramka_srodek = self.ids.srodek
        bramka_meta = self.ids.meta

        cursor = connection.cursor()
        cursor.execute("select id_bramki, nr_bramki from public.bramka")
        dane = cursor.fetchall()

        input1 = int(bramka_start.text)
        input2 = int(bramka_srodek.text)
        input3 = int(bramka_meta.text)

        cursor.execute("UPDATE public.bramka SET nr_bramki=%s WHERE id_bramki =1; commit",[input1])
        cursor.execute("UPDATE public.bramka SET nr_bramki=%s WHERE id_bramki =2; commit",[input2])
        cursor.execute("UPDATE public.bramka SET nr_bramki=%s WHERE id_bramki =3; commit",[input3])

        cursor.close()
        connection.close()

    def unswap(self):
        Manager.transition = NoTransition()

    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

class Rozpocznij(Screen):
    text1 = "Strona główna"
    text2 = "Nazwa wyścigu:"
    text3 = "Dodaj kierowcę"
    text4 = "Wybierz kierowcę"


    def swap(self):
        Manager.transition = SwapTransition()

    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    error = Popup(title='Wpisz nazwę wyścigu!',
                  title_align='center',
                  title_size=16,
                  content=content,
                  size_hint=(None, None), size=(220, 100),
                  auto_dismiss=False,
                  separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])
    content.bind(on_release=error.dismiss)

    def input(self):
        nazwa_wyscigu = self.ids.wyscig

        if nazwa_wyscigu.text == "":
            self.error.open()
        else:
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

text_input = []
text_id = []

class PolaczRFID(Screen):      # Pusty ekran na który na moment przełączamy się żeby odświeżyć
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    def generuj(self):
        tab = self.ids.tabelaRFID

        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        cursor = connection.cursor()

        cursor.execute("SELECT distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu,  p.rfid\
                                  FROM public.kierowca AS k\
                                  LEFT JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                                  JOIN public.przejazd AS r ON p.id_przypisania = r.id_przypisania")

        daner = cursor.fetchall()
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="ID", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(170, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="RFID", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(130, 35)))
        licznik = 0
        global text_input
        for i in daner:
            text_id.append(daner[licznik][0])
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][0]),
                           color=get_color_from_hex('ffffff'),
                           size=(85, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][1]),
                                      color=get_color_from_hex('ffffff'),
                                      size=(110, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][2]),
                           color=get_color_from_hex('ffffff'),
                           size=(150, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(daner[licznik][3]),
                           color=get_color_from_hex('ffffff'),
                           size=(170, 35)))
            text_input.append(TextInput(size_hint=(None, None), size=(120, 35)))
            tab.add_widget(text_input[licznik])
            tab.add_widget(
                PolaczButton(id=licznik, text="Polacz", size_hint=(None, None), size=(130, 35),
                             on_release=lambda x: self.update()))

            licznik += 1

    def update(self):
        global text_input
        global text_id
        global number
        connection = db.connect(user="postgres",
                                password="postgres",
                                database="lapify")

        text = text_input[number].text

        cursor = connection.cursor()
        cursor.execute("SELECT id_przypisania, id_wyscigu, id_kierowcy, rfid FROM przypisanie ")
        t = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("select id_wyscigu " \
                       "from wyscig " \
                       "where data_wyscigu = (select max(data_wyscigu) from wyscig)")

        b = cursor.fetchall()
        print(b)

        cursor = connection.cursor()
        cursor.execute("INSERT INTO przypisanie (id_przypisania, id_wyscigu, id_kierowcy, rfid) VALUES (%s,%s,%s,%s)",
                       (len(t) + 1, b[0], text_id[number], text))
        # cursor.execute(f"UPDATE public.przypisanie SET rfid = %s WHERE id_kierowcy={text_id[number]} ; commit", [text])
        print(text)
        cursor.close()
        connection.commit()
        connection.close()


class Manager(ScreenManager):

    @staticmethod
    def switch(x):
        global number
        number = x

    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.transition = NoTransition()


class DodajKierowce(Screen):

    def clear_inputs(self, text_inputs):
        for text_input in text_inputs:
            text_input.text = ""

    def unswap(self):
        Manager.transition = NoTransition()

    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    text1 = "Strona główna"
    text2 = "Dodawanie kierowców"
    text3 = "Imię"


    def add_driver(self):
        grid = self.ids.list
        imie = self.ids.name.text
        nazwisko = self.ids.last_name.text
        model = self.ids.model.text
        kategoria = self.ids.category.text

        list = BoxLayout(size_hint_y=None, height=50, pos_hint={'top': .5})
        grid.add_widget(list)

        imie = Label(text=imie, size_hint_x=.2)
        nazwisko = Label(text=nazwisko, size_hint_x=.2)
        model = Label(text=model, size_hint_x=.2)
        kategoria = Label(text=kategoria, size_hint_x=.2)
        empty = Label(text="", size_hint_x=.3)

        list.add_widget(imie)
        list.add_widget(nazwisko)
        list.add_widget(model)
        list.add_widget(kategoria)
        list.add_widget(empty)

        connection = db.connect(
            database="lapify",
            user="postgres",
            password="postgres")

        cursor = connection.cursor()
        cursor.execute("SELECT id_kierowcy, imie, nazwisko, model_samochodu,kategoria FROM kierowca ")
        rows = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("SELECT id_wyscigu FROM wyscig WHERE data_wyscigu = (select max(data_wyscigu) from wyscig) ")
        b = cursor.fetchall()


        cursor = connection.cursor()
        cursor.execute(" INSERT INTO kierowca ( id_kierowcy, imie, nazwisko, model_samochodu, kategoria) VALUES (%s,%s,%s,%s,%s)",
                       (len(rows) + 1, self.ids.name.text, self.ids.last_name.text,self.ids.model.text,
                        self.ids.category.text))

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

