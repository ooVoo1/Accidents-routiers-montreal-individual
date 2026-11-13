import customtkinter as ctk
import tkinter as tk

from graphes.map_maker import MapMaker

class Carte(ctk.CTkFrame):
    def __init__(self, master, handler, **kwargs):
        super().__init__(master, **kwargs)
        # DataHandler
        self.handler = handler
        # Créer la page de la carte
        self.creer_page_carte()

    def creer_page_carte(self):
        self.map = MapMaker(self,self.handler)
        self.map.place(relx=0.6, rely=0.5, anchor="center", relwidth=0.75, relheight=0.85)