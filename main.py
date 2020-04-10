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


class LapifyApp(App):
    def built(self):
        return ScreenManagement()


if __name__ == '__main__':
    LapifyApp().run()
