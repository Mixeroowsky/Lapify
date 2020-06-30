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
from time import sleep
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
import serial
import threading

# Tworzenie własnych labeli oraz przycisków w języku kv
Builder.load_string("""       
<PoleTabeli>:
  size_hint: (None, None)
  size: (110, 35)
  text: ""
  color: hex('#000000')
  bgcolor: hex('#FFFFFF')
  font_name: 'graphics/Roboto-Light'
  canvas.before:
    Color:
      rgba: self.bgcolor
    Rectangle:
      pos: self.pos
      size: self.size
<PolaczButton>:
  background_down: 'graphics/pressed.png'
  on_press: 
    app.root.switch(self.id)
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
<KierowcaButton1>:
  background_down: 'graphics/pressed.png'
  id: 0
  race_id: 0
  on_release: 
    app.root.switch(self.id)
    app.root.race_switch(self.race_id)
    app.root.current = "kierowca1"
<StartButton>:
  background_down: 'graphics/pressed.png'
  on_press: 
    app.root.switch(self.id)
<KontrolnyButton>:
  background_down: 'graphics/pressed.png'
  on_press: 
    app.root.switch(self.id)
<MetaButton>:
  background_down: 'graphics/pressed.png'
  on_press: 
    app.root.switch(self.id) 
<OkrazenieButton>:
  background_down: 'graphics/pressed.png'
  id: 0
  enum_id: 0
  on_release: 
    app.root.inside_switch(self.id)
    app.root.enum_switch(self.enum_id)
    app.root.current = "okrazenie"
<OkrazenieButton1>:
  background_down: 'graphics/pressed.png'
  id: 0
  enum_id: 0
  on_release: 
    app.root.inside_switch(self.id)
    app.root.enum_switch(self.enum_id)
    app.root.current = "okrazenie1"
<PolaczButton>:
  background_down: 'graphics/pressed.png'
  on_release: 
    app.root.switch(self.id)
""")

# Zmienne globalne wykorzystywane do przenoszenia danych pomiędzy oknami aplikacji
number = 0
number_update = 0
inside_number = 0
enum_number = 0
race_number = 0

# Zmienne globalne wykorzystywane przy odczycie danych i wykrywaniu niedziałających bramek
missing_bramka = ""
bramka_error = False
thread_stop = False
ping = []
bramki_wyscigu = []
obecne_pingi = []
pakiet_mety = ""
meta = ""
ser = serial.Serial()

# Tabele wykorzystywane przy wyświetlaniu danych z bazy
dane = []  # Przyda sie potem
okrazenie = []
wyscig = []
sortowane_ok = []

# Połączenie z bazą danych
connection = db.connect(database="lapify", user="postgres", password="postgres")

# Numer portu COM
port_number = ""

# Zmienna określająca czy wyścig został skonfigurowany i obecnie trwa
rozpoczety = False


# Deklaracja własnych labeli oraz przycisków stworzonych w języku kv
class PoleTabeli(Label):  # Kolorowy Label, polecam do tabelek
    bgcolor = ObjectProperty(None)

"""StartButton, KontrolnyButton, MetaButton - klasy przycisków 
z widoku konfiguracji bramek przy przychodzących pakietach."""
class StartButton(Button):
    pass


class KontrolnyButton(Button):
    pass


class MetaButton(Button):
    pass


class PolaczButton(Button):
    id = ObjectProperty(None)


class HistoriaButton(Button):
    id = ObjectProperty(None)


class KierowcaButton(Button):
    id = ObjectProperty(None)


class KierowcaButton1(Button):
    id = ObjectProperty(None)
    race_id = ObjectProperty(None)


class OkrazenieButton(Button):
    id = ObjectProperty(None)
    enum_id = ObjectProperty(None)


class OkrazenieButton1(Button):
    id = ObjectProperty(None)
    enum_id = ObjectProperty(None)


class Startowa(Screen):
    def skip(self, dt):
        self.manager.current = "nowa"

    def on_enter(self, *args):
        Clock.schedule_once(self.skip, 0.1)


class NowaSesja(Screen):
    text1 = "Strona główna"
    text2 = "Rozpocznij nową sesję"

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    # Funkcje pozwalające na zmianę animacji przejścia pomiędzy oknami
    def fade(self):  # Żeby fade był tylko przy okienku Rozpocznij
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    # dane do tabeli
    def generujtabele(self):
        tabela = self.ids.tabelaOstatniaSesja
        ekran = self.ids.p_ostatnia_sesja

        cursor = connection.cursor()

        cursor.execute("SELECT max(id_wyscigu) from wyscig;")
        pobrane = cursor.fetchone()
        last_race = pobrane[0]
        if rozpoczety is True:
            last_race = pobrane[0] - 1
        # pobieranie danych do ostatniej sesji
        data_command = "select  distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu, k.kategoria, (bramka3-bramka1) as okrazenie " \
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
                       f"where w.id_wyscigu={last_race} ; "
        cursor.execute(data_command)

        all_data = cursor.fetchall()

        unikalne_id = []
        unikalny_kierowca = []

        for i in range(0, len(all_data)):
            if all_data[i][0] not in unikalne_id:
                unikalne_id.append(all_data[i][0])
                unikalny_kierowca.append(all_data[i])
                continue
            else:
                for j in range(0, len(unikalny_kierowca)):
                    if all_data[i][0] == unikalny_kierowca[j][0] \
                            and all_data[i][5] < unikalny_kierowca[j][5]:  # 6 kolumna
                        unikalny_kierowca[j] = all_data[i]
                        continue

        okrazenie.clear()
        for a in unikalny_kierowca:
            okrazenie.append((a[0], a[1], a[2], a[3], a[4], a[5]))

        nazwa_wyscigu = f"select w.nazwa_wyscigu, w.data_wyscigu, w.id_wyscigu  \
                         from wyscig w \
                         where w.id_wyscigu={last_race} \
                         order by w.id_wyscigu desc;"

        cursor.execute(nazwa_wyscigu)
        wyscig = cursor.fetchone()

        nazwa_wyscigu = str(wyscig[0])
        data_wyscigu = str(wyscig[1])

        ekran.add_widget(Label(text=f"{str(nazwa_wyscigu)}",
                               size_hint=(None, None),
                               pos_hint={"x": 0.27, "y": 0.8},
                               font_size="30",
                               color=get_color_from_hex('#EF8B00')))

        ekran.add_widget(Label(text=f"{str(data_wyscigu)}",
                               size_hint=(None, None),
                               pos_hint={"x": 0.27, "y": 0.762},
                               font_size="15",
                               color=get_color_from_hex('#EF8B00')))

        sortowanie = sorted(okrazenie, key=lambda data: data[5])  # Lista posortowana wg wartosci

        # Wyświetlanie tytułów tabeli:

        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(70, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(120, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="      Model \nsamochodu", size=(170, 35)))
        tabela.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(125, 35)))
        tabela.add_widget(
            PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="    Czas \nokrążenia", size=(90, 35)))

        #wstawianie danych do tabeli

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
    text3 = "Połącz RFID"
    text4 = "Zakończ wyścig"
    global missing_bramka
    global rozpoczety
    database_live_data = []

    # Funkcja wyłączająca pojawianie się okna błędu komunikacji z bramką
    def reconnect(instance):
        global bramka_error
        bramka_error = False

    # Okno błędu komunikacji z bramką
    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    conn_error_popup = Popup(title_align='center',
                             title_size=16,
                             content=content,
                             size_hint=(None, None), size=(320, 100),
                             auto_dismiss=False,
                             separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])
    content.bind(on_release=conn_error_popup.dismiss)
    content.bind(on_release=reconnect)

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    # Funkcje pozwalające na zmianę animacji przejścia pomiędzy oknami
    def fade(self):  # Żeby fade był tylko przy okienku Rozpocznij
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    # Funkcja pobierająca z bazy dane dotyczące trwającego wyścigu
    def database_get_live(self):
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
                       where wyscig.id_wyscigu=(select max(id_wyscigu) from wyscig)) )a  \
                       on p.id_ok = a.id_ok  \
                       join (select id_ok, czas as bramkaKoniec from przejazd  \
                       where id_bramki = (select max(distinct id_bramki) from przejazd \
                       join przypisanie on przejazd.id_przypisania = przypisanie.id_przypisania \
                       join wyscig on przypisanie.id_wyscigu = wyscig.id_wyscigu \
                       where wyscig.id_wyscigu=(select max(id_wyscigu) from wyscig)) )b  \
                       on b.id_ok = p.id_ok  \
                       join wyscig w  \
                       on r.id_wyscigu = w.id_wyscigu  \
                       where w.id_wyscigu=(select max(id_wyscigu) from wyscig) ; "
        cursor.execute(data_command)
        self.database_live_data.clear()
        self.database_live_data = cursor.fetchall()
        cursor.close()

    # Funkcja wywoływana cyklicznie co 2 sekundy, sprawdza stan połączenia z bramkami oraz odświeża
    # wyniki w tabeli po zakończeniu okrążenia przez kierowcę
    def connection_check(self, *args):
        global pakiet_mety
        if pakiet_mety == meta and bramka_error is False and self.manager.current == "live":
            self.database_get_live()
            self.manager.current = "refresh"
            pakiet_mety = ""
        if bramka_error is True:
            self.conn_error_popup.title = "Bramka " + missing_bramka + " nie odpowiada!"
            self.conn_error_popup.open()

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca zawartość tabel oraz nazwę wyścigu
    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaLive  # Layout tabeli
        background = self.ids.plansza  # Layout Ekranu
        sortowane = []
        cursor = connection.cursor()

        if rozpoczety is True:
            # Timer wywołujący co 2 sekundy funkcję connection_check
            Clock.schedule_interval(self.connection_check, 2)

            # Dane pobrane z bazy
            dane_live = self.database_live_data

            # Poniższy kod odpowiada za wyświetlanie dla każdego kierowcy jedynie najszybszego okrążenia
            unikalne_id = []
            unikalny_kierowca = []

            for i in range(0, len(dane_live)):
                if dane_live[i][0] not in unikalne_id:
                    unikalne_id.append(dane_live[i][0])
                    unikalny_kierowca.append(dane_live[i])
                    continue
                else:
                    for j in range(0, len(unikalny_kierowca)):
                        if dane_live[i][0] == unikalny_kierowca[j][0] \
                                and dane_live[i][4] < unikalny_kierowca[j][4]:
                            unikalny_kierowca[j] = dane_live[i]
                            continue

            # Sortowanie wyników kierowców od najmniejszego czasu okrążenia
            sortowane = sorted(unikalny_kierowca, key=lambda data: data[4])

            # Poniższy kod odpowiada za wyświetlenie nazwy trwającego wyścigu
            nazwa_wyscigu = "select nazwa_wyscigu, data_wyscigu " \
                            "from wyscig " \
                            "where data_wyscigu = (select max(data_wyscigu) from wyscig)"

            cursor.execute(nazwa_wyscigu)
            all_data = cursor.fetchall()
            wyscig.clear()

            for a in all_data:
                wyscig.append((a[0], a[1]))

            nazwa_wyscigu = f"{str(wyscig[len(wyscig) - 1][0])}"

            # Wyświetlanie nazwy wyścigu
            background.add_widget(Label(text=f"Wyścig {nazwa_wyscigu}",
                                        size_hint=(None, None),
                                        pos_hint={"right": 0.45, "y": 0.81},
                                        font_size="30",
                                        color=get_color_from_hex('#EF8B00')))

        # W przypadku gdy globalna zmienna rozpoczety = False
        else:
            background.add_widget(Label(text=f"Brak trwającego wyścigu",
                                        size_hint=(None, None),
                                        pos_hint={"right": 0.45, "y": 0.81},
                                        font_size="30",
                                        color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie tytułów tabeli
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(85, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(110, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(140, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(160, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Status RFID", size=(100, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(80, 35)))

        if rozpoczety is True:
            # Wyświetlanie wierszy tabeli:
            licznik = 0
            for i in sortowane:
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=f"{licznik + 1}", size=(85, 35)))
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][1]),
                                          size=(110, 35)))
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][2]),
                                          size=(150, 35)))
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][3]),
                                          size=(140, 35)))
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][4]),
                                          size=(120, 35)))
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][5]),
                                          size=(160, 35)))
                tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'),
                                          color=get_color_from_hex('ffffff'), text=str(sortowane[licznik][6]),
                                          size=(100, 35)))
                tab.add_widget(KierowcaButton(text="Więcej", size_hint=(None, None), size=(80, 35),
                                              id=int(sortowane[licznik][0])))
                licznik += 1
        cursor.close()

    # Funkcja kończąca wyścig
    def zakoncz_wyscig(self):
        global port_number
        global rozpoczety

        if rozpoczety is True:
            if ser.isOpen:
                ser.close()

            port_number = ""
            rozpoczety = False
            Clock.unschedule(self.connection_check())

            # Rozłączenie w bazie danych wszystkich kierowców z ich RFID
            cursor = connection.cursor()
            cursor.execute("UPDATE przypisanie SET rfid=Null; COMMIT;")
            okrazenie.clear()
            cursor.close()


class WynikiKierowcy(Screen):
    text1 = "Strona główna"
    text2 = "Powrót"

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaKierowca
        background = self.ids.planszaKierowca

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
                       where w.id_wyscigu=(select max(id_wyscigu) from wyscig) \
                       AND k.id_kierowcy = {number};"

        cursor.execute(data_command)

        wyniki = cursor.fetchall()

        # Wyświetlanie nazwy wyścigu
        background.add_widget(Label(text=f"Wyścig {wyniki[0][6]}",
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
                                           id=int(wyniki[licznik][7]), enum_id=licznik + 1))
            licznik += 1
        cursor.close()
        wyniki.clear()

class WynikiKierowcy1(Screen): #wyniki kierowcow z poprzednich sesji
    text1 = "Strona główna"
    text2 = "Powrót"
    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    error = Popup(title='Brak danych!',
                  title_align='center',
                  title_size=16,
                  content=content,
                  size_hint=(None, None), size=(220, 100),
                  auto_dismiss=False,
                  separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])
    content.bind(on_release=error.dismiss)

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaKierowca1
        background = self.ids.planszaKierowca1

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
                       where w.id_wyscigu = {race_number} \
                       AND k.id_kierowcy = {number};"

        cursor.execute(data_command)

        wyniki = cursor.fetchall()



        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text=f"{wyniki[0][1]} {wyniki[0][2]}",
                                  size=(765, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][3]}", size=(765, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][5]}", size=(765, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(765, 3)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Numer okrążenia", size=(200, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Czas okrążenia", size=(465, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))

        licznik = 0
        for i in wyniki:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik + 1}",
                           color=get_color_from_hex('ffffff'),
                           size=(200, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(wyniki[licznik][4]),
                           color=get_color_from_hex('ffffff'),
                           size=(465, 35)))
            tab.add_widget(OkrazenieButton1(text="Szczegóły", size_hint=(None, None), size=(100, 35),
                                           id=int(wyniki[licznik][7]), enum_id=licznik + 1))
            licznik += 1
        cursor.close()
        wyniki.clear()


class SzczegolyOkrazenia(Screen):
    text1 = "Strona główna"
    text2 = "Powrót"

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaOkrazenia
        background = self.ids.planszaOkrazenia

        cursor = connection.cursor()

        cursor.execute(f"SELECT k.imie, k.nazwisko, k.model_samochodu, r.czas, k.kategoria, w.nazwa_wyscigu\
                               FROM public.kierowca AS k\
                               JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                               JOIN public.przejazd AS r ON p.id_przypisania = r.id_przypisania\
                               JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu\
                               WHERE w.id_wyscigu =  (select max(id_wyscigu) from wyscig)\
                               AND r.id_ok = {inside_number};"
                       )

        wyniki = cursor.fetchall()

        czasy = []
        odcinki = []

        licznik = 0
        for i in wyniki:
            czasy.append(wyniki[licznik][3])
            licznik += 1

        for i in range(0, len(czasy) - 1):
            duration = datetime.combine(date.min, czasy[i + 1]) - datetime.combine(date.min, czasy[i])
            odcinki.append(duration)

        # Wyświetlanie nazwy wyścigu
        background.add_widget(Label(text=f"Wyścig {wyniki[0][5]}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.15, "y": 0.8},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        # Wyświetlanie danych kierowcy
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text=f"{wyniki[0][0]} {wyniki[0][1]}",
                                  size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][2]}", size=(952, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][4]}", size=(952, 35)))
        # tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 3)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(151, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'),
                                  text=f"Okrążenie {enum_number}", size=(699, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(100, 35)))
        # tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 1.5)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Odcinek trasy", size=(151, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Czas na odcinku", size=(699, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))

        # Wyświetlanie czasów na odcinkach dla kierowcy
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


#Zakładka Poprzednie Sesje - Historia wyscigów
class SzczegolyOkrazenia1(Screen): #szczegoly okrazen poszczegolnych okrazen
    text1 = "Strona główna"
    text2 = "Powrót"

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        global inside_number
        global enum_number
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaOkrazenia1
        background = self.ids.planszaOkrazenia1

        cursor = connection.cursor()

        cursor.execute(f"SELECT k.imie, k.nazwisko, k.model_samochodu, r.czas, k.kategoria, w.nazwa_wyscigu\
                                   FROM public.kierowca AS k\
                                   JOIN public.przypisanie AS p ON k.id_kierowcy = p.id_kierowcy\
                                   JOIN public.przejazd AS r ON p.id_przypisania = r.id_przypisania\
                                   JOIN public.wyscig AS w ON p.id_wyscigu = w.id_wyscigu\
                                   WHERE w.id_wyscigu = {race_number}\
                                   AND r.id_ok = {inside_number};"
                       )

        wyniki = cursor.fetchall()

        czasy = []
        odcinki = []

        licznik = 0
        for i in wyniki:
            czasy.append(wyniki[licznik][3])
            licznik += 1

        for i in range(0, len(czasy) - 1):
            duration = datetime.combine(date.min, czasy[i + 1]) - datetime.combine(date.min, czasy[i])
            odcinki.append(duration)

        # Wyświetlanie danych kierowcy
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text=f"{wyniki[0][0]} {wyniki[0][1]}",
                                  size=(765, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][2]}", size=(765, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text=f"{wyniki[0][4]}", size=(765, 35)))
        # tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 3)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(100, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'),
                                  text=f"Okrążenie {enum_number}", size=(565, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(100, 35)))
        # tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(952, 1.5)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Odcinek trasy", size=(100, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), color=get_color_from_hex('ffffff'),
                                  text="Czas na odcinku", size=(565, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))

        # Wyświetlanie czasów na odcinkach dla kierowcy
        licznik = 0
        for i in odcinki:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik + 1}",
                           color=get_color_from_hex('ffffff'),
                           size=(100, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(odcinki[licznik]),
                           color=get_color_from_hex('ffffff'),
                           size=(565, 35)))
            tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#505050'), size=(100, 35)))
            licznik += 1
        cursor.close()
        wyniki.clear()


class PoprzednieSesje(Screen):
    text1 = "Strona główna"
    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    error = Popup(title='Dodaj kierowców do wyścigu!',
                  title_align='center',
                  title_size=16,
                  content=content,
                  size_hint=(None, None), size=(220, 100),
                  auto_dismiss=False,
                  separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])
    content.bind(on_release=error.dismiss)
    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaPoprzednie
        background = self.ids.oknoPoprzednie

        cursor = connection.cursor()

        cursor.execute("select id_wyscigu, nazwa_wyscigu, data_wyscigu from wyscig order by id_wyscigu asc")
        dane = cursor.fetchall()

        background.add_widget(Label(text=f"Historia wyścigów: ",
                            size_hint=(None, None),
                            pos_hint={"x": 0.082, "y": 0.835},
                            font_size="30",
                            color=get_color_from_hex('#EF8B00')))

        trwajacy = 0
        if rozpoczety is True:
            trwajacy = 1

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Numer wyścigu", size=(150, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwa wyścigu", size=(300, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Data wyścigu", size=(157, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(120, 35)))
        #wstawianie wartości do tabeli
        licznik = 0
        for i in range(0, (len(dane)-trwajacy)):
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

    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    error = Popup(title='Brak danych!',
                  title_align='center',
                  title_size=16,
                  content=content,
                  size_hint=(None, None), size=(220, 100),
                  auto_dismiss=False,
                  separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])
    content.bind(on_release=error.dismiss)

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        global number
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaHistoria
        background = self.ids.oknoHistoria
        dane = []

        cursor = connection.cursor()

        cursor.execute(f"select distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu,\
                               (bramkaKoniec-bramkaPoczatek) as okrazenie, k.kategoria, w.nazwa_wyscigu, w.data_wyscigu, w.id_wyscigu \
                               from kierowca k \
                               join przypisanie r on k.id_kierowcy = r.id_kierowcy  \
                               join przejazd p on r.id_przypisania = p.id_przypisania \
                               join (select id_ok, czas as bramkaPoczatek from przejazd \
                               where id_bramki = (select min(distinct id_bramki) from przejazd \
                               join przypisanie on przejazd.id_przypisania = przypisanie.id_przypisania \
                               join wyscig on przypisanie.id_wyscigu = wyscig.id_wyscigu \
                               where public.wyscig.id_wyscigu = {number}) )a  \
                               on p.id_ok = a.id_ok \
                               join (select id_ok, czas as bramkaKoniec from przejazd  \
                               where id_bramki = (select max(distinct id_bramki) from przejazd \
                               join przypisanie on przejazd.id_przypisania = przypisanie.id_przypisania \
                               join wyscig on przypisanie.id_wyscigu = wyscig.id_wyscigu \
                               where public.wyscig.id_wyscigu ={number}) )b  \
                               on b.id_ok = p.id_ok  \
                               join wyscig w  on r.id_wyscigu = w.id_wyscigu \
                               where w.id_wyscigu = {number}; ")


        dane.clear()
        dane = cursor.fetchall()

        unikalne_id = []
        unikalny_kierowca = []
        # szukanie najlepszych czasów dla konkretnego kierowcy
        for i in range(0, len(dane)):
            if dane[i][0] not in unikalne_id:
                unikalne_id.append(dane[i][0])
                unikalny_kierowca.append(dane[i])
                continue
            else:
                for j in range(0, len(unikalny_kierowca)):
                    if dane[i][0] == unikalny_kierowca[j][0] \
                            and dane[i][4] < unikalny_kierowca[j][4]:  # 5 kolumna
                        unikalny_kierowca[j] = dane[i]
                        continue

        sortowane = sorted(unikalny_kierowca, key=lambda data: data[4])  # Lista posortowana wg wartosci

        nazwa_wyscigu = dane[0][6]
        data = dane[0][7]

        # Wyświetlanie nazwy oraz daty wyscigu
        background.add_widget(Label(text=f"Historia wyścigu {nazwa_wyscigu} ",
                            size_hint=(None, None),
                            pos_hint={"x": 0.3, "y": 0.75},
                            font_size="30",
                            color=get_color_from_hex('#000000')))

        background.add_widget(Label(text=f"Data: {data}",
                            size_hint=(None, None),
                            pos_hint={"x": 0.22, "y": 0.7},
                            font_size="20",
                            color=get_color_from_hex('#000000')))

        # Wyświetlanie tytułów tabeli:
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Miejsce", size=(70, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Imię", size=(100, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Nazwisko", size=(140, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Model samochodu", size=(135, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Najlepszy czas", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Kategoria", size=(120, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), size=(75, 35)))
        # wstawianie wartości do tabeli
        licznik = 0
        for i in sortowane:
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=f"{licznik + 1}",
                           color=get_color_from_hex('ffffff'),
                           size=(70, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(sortowane[licznik][1]),
                           color=get_color_from_hex('ffffff'),
                           size=(100, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(sortowane[licznik][2]),
                           color=get_color_from_hex('ffffff'),
                           size=(140, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(sortowane[licznik][3]),
                           color=get_color_from_hex('ffffff'),
                           size=(135, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(sortowane[licznik][4]),
                           color=get_color_from_hex('ffffff'),
                           size=(120, 35)))
            tab.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=str(sortowane[licznik][5]),
                           color=get_color_from_hex('ffffff'),
                           size=(120, 35)))
            tab.add_widget(KierowcaButton1(text="Więcej", size_hint=(None, None), size=(75, 35),
                                           id=int(sortowane[licznik][0]),race_id=int(sortowane[licznik][8])))

            licznik += 1

            cursor.close()


# Tworzenie Okna Konfiguracji Bramek
class Bramki(Screen):
    text1 = "Strona główna"
    text2 = "Odśwież"
    wyswietlane = []

    # Funkcje pozwalające na zmianę animacji przejścia pomiędzy oknami
    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    def assign_port(self):
        global port_number
        # Odwołanie do tekstu wpisanego do pola tekstowego z pliku .kv
        port_number = self.ids.port_number.text
        global ser
        print(f"Numer portu: {port_number}")
        try:
            ser = serial.Serial(f'COM{port_number}', baudrate=9600, timeout=1)
        except serial.SerialException as ex:
            print("Error! No such serial port")

    # Funkcja odświeżająca wyświetlane bramki
    def refresh(self, dt):
        self.add_tag_id()

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca tabelę
    def generuj(self, *args):
        # Odwołanie do elementu z pliku .kv
        tab = self.ids.tabelabramki
        tab.clear_widgets()
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Przychodzące pakiety", size=(471, 35)))
        tab.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), text="Przypisz", size=(390, 35)))
        # Automatyczne odświeżanie wyświetlanych bramek co 4 sekundy
        Clock.schedule_interval(self.refresh, 4)

    #Przypisywanie pakietów do Startu, Punktów kontrolnych i Mety
    def add_tag_id(self):
        global number
        global ping

        self.wyswietlane = ping
        #self.wyswietlane.sort()
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tag_id
        tab.clear_widgets()

        for i in range(len(self.wyswietlane)):
            tag_list = BoxLayout(size_hint_y=None, height=40, pos_hint={'top': .5}, size_hint_x=None, width=280)
            tab.add_widget(tag_list)
            tag_list.add_widget(
                PoleTabeli(bgcolor=get_color_from_hex('#505050'), text=self.wyswietlane[i], color=get_color_from_hex('ffffff'),
                           size=(469, 35)))
            tag_list.add_widget(StartButton(text="Start", id=f"{i}", size_hint=(None, None), size=(129, 35),
                                            on_release=lambda x: self.updateStart()))
            tag_list.add_widget(
                KontrolnyButton(text="Punkt kontrolny", id=f"{i}", size_hint=(None, None), size=(129, 35),
                                on_release=lambda x: self.updateKontrolny()))
            tag_list.add_widget(
                MetaButton(text="Meta", id=f"{i}", size_hint=(None, None), size=(129, 35),
                           on_release=lambda x: self.updateMeta()))
        self.wyswietlane.clear()

    # Przypisywanie do pakietu do Startu
    def updateStart(self):
        global number
        bramka_start = number
        print(self.wyswietlane[int(bramka_start)])
        '''        sleep(0.2)
        cursor = connection.cursor()
        cursor.execute(f"UPDATE public.bramka SET nr_bramki = '{self.wyswietlane[int(bramka_start)]}' WHERE id_bramki = 1")

        cursor.close()
        connection.commit()'''

    # Przypisywanie pakietów do Punktów kontrolnych
    def updateKontrolny(self):
        global number
        bramka_checkpoint = number
        print(self.wyswietlane[int(bramka_checkpoint)])
        '''sleep(0.2)
        cursor = connection.cursor()
        cursor.execute(f"UPDATE public.bramka SET nr_bramki = '{self.wyswietlane[int(bramka_checkpoint)]}' WHERE id_bramki = 2")

        cursor.close()
        connection.commit()'''

    # Przypisywanie pakietu do mety
    def updateMeta(self):
        global number
        bramka_meta = number
        print(self.wyswietlane[int(bramka_meta)])
        '''sleep(0.2)
        cursor = connection.cursor()
        cursor.execute(f"UPDATE public.bramka SET nr_bramki = '{self.wyswietlane[int(bramka_meta)]}' WHERE id_bramki = 3 ")

        cursor.close()
        connection.commit()'''

    # Funkcja wywoływana po opuszczeniu okna konfiguracji bramek, zapisuje wybrane bramki oraz
    # wyłącza timer automatycznego odświeżania okna
    def konfiguracja_bramek(self):
        global bramki_wyscigu
        bramki_wyscigu = self.wyswietlane
        Clock.unschedule(self.refresh)


class Rozpocznij(Screen): # wpisywanie nazwy wyscigu
    text1 = "Strona główna"
    text2 = "Nazwa wyścigu:"
    text3 = "Dodawanie nazwy wyścigu"

    content = Button(text='OK',
                     background_down='graphics/pressed.png')

    error = Popup(title='Wpisz nazwę wyścigu!',
                  title_align='center',
                  title_size=16,
                  content=content,
                  size_hint=(None, None), size=(220, 100),
                  auto_dismiss=False,
                  separator_color=[38 / 255., 38 / 255., 38 / 255., 1.])

    content.bind(on_release = error.dismiss)

    def input(self):
        nazwa_wyscigu = self.ids.wyscig
        if nazwa_wyscigu.text == "":
            self.error.open()
        else:
            self.manager.current = "dodaj"
            cursor = connection.cursor()
            cursor.execute("select id_wyscigu, nazwa_wyscigu, data_wyscigu from wyscig")
            rows = cursor.fetchall()
            cursor.execute("insert into wyscig (id_wyscigu, nazwa_wyscigu, data_wyscigu ) values (%s, %s, %s); commit;",
                           (len(rows) + 1, nazwa_wyscigu.text, date.today()))
            cursor.close()

    # Funkcje pozwalające na zmianę animacji przejścia pomiędzy oknami
    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()


text_input = []
text_id = []


class PolaczRFID(Screen): #polaczenie rfid z kierowcami
    text1 = "Strona główna"
    text2 = "Wróć"

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

    # Funkcja wywoływana po przejściu do okienka, wyświetląjąca dane pobrane z bazy danych
    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        tab = self.ids.tabelaRFID

        cursor = connection.cursor()

        cursor.execute("SELECT distinct k.id_kierowcy, k.imie, k.nazwisko, k.model_samochodu\
                                          FROM public.kierowca AS k\
                                          ORDER BY k.id_kierowcy")

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
                PolaczButton(id=licznik, text="Połącz", size_hint=(None, None), size=(130, 35),
                             on_release=lambda x: self.update()))

            licznik += 1

    def update(self):
        global text_input
        global text_id
        global number

        text = text_input[number].text

        cursor = connection.cursor()
        cursor.execute("SELECT id_przypisania, id_wyscigu, id_kierowcy, rfid FROM przypisanie ")
        t = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("select id_wyscigu  \
                       from wyscig  \
                       order by id_wyscigu desc limit 1 ")

        b = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("INSERT INTO przypisanie (id_przypisania, id_wyscigu, id_kierowcy, rfid) VALUES (%s,%s,%s,%s)",
                       (len(t) + 1, b[0], text_id[number], text))
        cursor.close()
        connection.commit()


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

    @staticmethod
    def race_switch(x):
        global race_number
        race_number = x

    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.transition = NoTransition()


class DodajKierowce(Screen):
    text1 = "Strona główna"
    text2 = "Dodawanie kierowców"
    text3 = "Imię"

    def generuj(self):
        # Odwołanie do elementów z pliku .kv
        background = self.ids.oknoDodawanie

        # Wyświetlanie tytułów tabeli:
        background.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), pos_hint={"x": 0.199, "y": 0.78},
                                         text="Imię", size=(150, 25)))
        background.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), pos_hint={"x": 0.317, "y": 0.78},
                                         text="Nazwisko", size=(150, 25)))
        background.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), pos_hint={"x": 0.435, "y": 0.78},
                                         text="Model samochodu", size=(150, 25)))
        background.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), pos_hint={"x": 0.553, "y": 0.78},
                                         text="Kategoria", size=(150, 25)))
        background.add_widget(PoleTabeli(bgcolor=get_color_from_hex('#EF8B00'), pos_hint={"x": 0.671, "y": 0.78},
                                         text="", size=(150, 25)))




    def clear_inputs(self, text_inputs):
        for text_input in text_inputs:
            text_input.text = ""

    # Funkcje pozwalające na zmianę animacji przejścia pomiędzy oknami
    def fade(self):
        Manager.transition = FadeTransition()

    def unfade(self):
        Manager.transition = NoTransition()

    def swap(self):
        Manager.transition = SwapTransition()

    def unswap(self):
        Manager.transition = NoTransition()

    def cofnij(self):
        if rozpoczety is False:
            self.manager.current = "rozpocznij"

    def add_driver(self):
        tab = self.ids.tabelaDodawanie
        imie = self.ids.name.text
        nazwisko = self.ids.last_name.text
        model = self.ids.model.text
        kategoria = self.ids.category.text

        lista = BoxLayout(size_hint_y=None, height=50, pos_hint={'top': .5})
        tab.add_widget(lista)

        imie = Label(text=imie, size_hint_x=.2)
        nazwisko = Label(text=nazwisko, size_hint_x=.2)
        model = Label(text=model, size_hint_x=.2)
        kategoria = Label(text=kategoria, size_hint_x=.2)
        empty = Label(text="", size_hint_x=.3)

        lista.add_widget(imie)
        lista.add_widget(nazwisko)
        lista.add_widget(model)
        lista.add_widget(kategoria)
        lista.add_widget(empty)

        cursor = connection.cursor()
        cursor.execute("SELECT id_kierowcy, imie, nazwisko, model_samochodu,kategoria FROM kierowca ")
        rows = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute("SELECT id_wyscigu FROM wyscig WHERE id_wyscigu = (select max(id_wyscigu) from wyscig) ")
        b = cursor.fetchall()

        cursor = connection.cursor()
        cursor.execute(
            " INSERT INTO kierowca ( id_kierowcy, imie, nazwisko, model_samochodu, kategoria) VALUES (%s,%s,%s,%s,%s)",
            (len(rows) + 1, self.ids.name.text, self.ids.last_name.text, self.ids.model.text,
             self.ids.category.text))

        connection.commit()
        cursor.close()

    def rozpocznij(self):
        global rozpoczety
        global meta
        rozpoczety = True

        cursor = connection.cursor()
        cursor.execute("SELECT nr_bramki FROM bramka WHERE id_bramki = 3 order by id_bramki asc")
        id_mety = cursor.fetchone()
        meta = id_mety[0]


class Refresh(Screen):
    text1 = "Strona główna"
    text2 = "Dodaj kierowcę"
    text3 = "Połącz z RFID"
    text4 = "Zakończ wyścig"

    # Przenoszenie po 0.01 sekundy z powrotem do okna live, w celu odświeżenia zawartości tabeli
    def skip(self, dt):
        self.manager.current = "live"

    def on_enter(self, *args):
        Clock.schedule_once(self.skip, 0.01)


kv = Builder.load_file("design.kv")


class LapifyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        return kv


def clear_ping():
    global ping
    ping.clear()


def packet_receive():
    buffor = ""
    global port_number
    global missing_bramka
    global bramka_error
    global obecne_pingi
    global bramki_wyscigu
    global ping

    while 1:
        #threading.Timer(5, clear_ping).start()
        if port_number == "":
            sleep(1)
        else:
            try:
                data = ser.read()
                if len(data) != 0 and ord(data) >= 32 and ord(data) <= 128:
                    buffor += str(data.decode('utf-8'))
                elif (data == b'\r' or data == b'\n') and len(buffor) == 34:
                    print(buffor)
                    if buffor[12:14] == '01':
                        global ping
                        if buffor[2:10] not in ping:
                            ping.append(buffor[2:10])

                    elif buffor[12:14] == '02':
                        timestamp = buffor[22:30]
                        timestamp = int(timestamp, 16) / 3600000
                        timestamp_hours = int(timestamp)
                        timestamp_minutes = (timestamp * 60) % 60
                        timestamp_seconds = (timestamp * 3600) % 60
                        time = "%d:%02d:%02d" % (timestamp_hours, timestamp_minutes, timestamp_seconds)
                        print(f"Czas odczytany z pakietu: {time}")

                        rfid_tag = str(buffor[14:22])
                        nr_bramki = str(buffor[2:10])

                        cursor = connection.cursor()

                        cursor.execute("SELECT id_przejazdu FROM przejazd;")
                        rows = cursor.fetchall()
                        #print("Rows pobrano!")
                        cursor.execute(f"SELECT id_przypisania from przypisanie \
                                         where rfid = '{rfid_tag}';")
                        id_przypisania = cursor.fetchall()
                        #print("id_przypisania pobrano!")
                        cursor.execute("SELECT id_bramki from bramka"
                                       " where nr_bramki = '%s' ;" % nr_bramki)
                        id_bramki = cursor.fetchall()
                        #print("id_bramki pobrano!")

                        cursor.execute("SELECT id_bramki FROM przejazd ORDER BY id_przejazdu desc LIMIT 1;")
                        ostatnia_bramka = cursor.fetchall()
                        #print("ostatnia bramka pobrano!")

                        cursor.execute("SELECT id_ok FROM przejazd order by id_przejazdu desc limit 1;")
                        next_ok = cursor.fetchall()
                        #print("next_ok pobrano!")

                        if ostatnia_bramka[0][0] == 3:
                            a = next_ok[0][0]
                            a += 1
                            cursor.execute(
                                " INSERT INTO przejazd ( id_przejazdu, id_ok, id_przypisania, id_bramki, czas) VALUES (%s,%s,%s,%s,%s)",
                                (len(rows) + 1, a, id_przypisania[0], id_bramki[0], time))
                            #print("Rozpoczeto nowe okrazenie")

                        else:
                            cursor.execute(
                                " INSERT INTO przejazd ( id_przejazdu, id_ok, id_przypisania, id_bramki, czas) VALUES (%s,%s,%s,%s,%s)",
                                (len(rows) + 1, next_ok[0], id_przypisania[0], id_bramki[0], time))

                        # Wykrywanie czy odczytana bramka jest bramką kończącą okrążenia
                        if nr_bramki == meta:
                            connection.commit()
                            global pakiet_mety
                            pakiet_mety = nr_bramki

                    # Wykrywanie czy wszystkie skonfigurowane bramki odpowiednio działają
                    if rozpoczety is True:
                        if len(obecne_pingi) == len(bramki_wyscigu) + 1:
                            for i in bramki_wyscigu:
                                if i not in obecne_pingi:
                                    missing_bramka = i
                                    bramka_error = True
                            obecne_pingi.clear()
                        else:
                            obecne_pingi.append(buffor[2:10])

                    buffor = ""

            except:
                "Error with data read"
        if thread_stop is True:
            break


def receive_thread():
    thread = threading.Thread(target=packet_receive)
    thread.start()


# Nawiązanie połączenia z bazą danych, uruchomienie dodatkowego wątku oraz aplikacji
# Zatrzymanie wątku oraz zamknięcie połączenia z bazą danych po zakończeniu działania aplikacji
if __name__ == '__main__':
    receive_thread()
    LapifyApp().run()
    thread_stop = True
    connection.close()

