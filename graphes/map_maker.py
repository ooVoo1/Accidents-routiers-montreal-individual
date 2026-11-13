import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from tkintermapview import TkinterMapView

class MapMaker(ctk.CTkFrame):
    def __init__(self, master, handler):
        super().__init__(master)
        self.handler = handler
        #Créer la carte
        self.carte = TkinterMapView(self, corner_radius=0)
        self.carte.pack(fill="both", expand=True)
        # Centrer sur Montréal (Coordonnées exactes trouvée par ChatGPT)
        self.carte.set_position(45.5017, -73.5673)
        self.carte.set_zoom(11)
    def update_map(self):
        print("Focntionne ")