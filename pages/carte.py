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
        #Créer la carte puis la placer dans la page
        self.map = MapMaker(self,self.handler)
        self.map.place(relx=0.6, rely=0.4, anchor="center", relwidth=0.75, relheight=0.70)

        # Encadré des statistiques
        self.stats_frame = ctk.CTkFrame(self, fg_color="white", border_width=1, border_color="#D9DEE5", corner_radius=12)
        self.stats_frame.place(relx=0.0175, rely=0.1, anchor="nw", relwidth=0.20, relheight=0.5)