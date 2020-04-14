# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 12:38:41 2020

@author: Aleksandra
"""
import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.popup import Popup
from kivy.factory import Factory
from kivy.config import Config
from kivy.uix.image import Image
import kivy.utils
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput


Config.set('kivy','window_icon','graphics/lapify_logo.png')


class StronaGlowna(Screen):
    pass


class Live(Screen):
    pass


class PoprzednieSesje(Screen):
    pass


class Pomoc(Screen):
    pass


class ScreenManagement(ScreenManager):
    pass


class NowaSesja(Screen):
    pass


class LapifyApp(App):
    def built(self):
        return ScreenManagement()


if __name__ == '__main__':
    LapifyApp().run()
