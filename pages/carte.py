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

        #Encadré des dropdown menu
        self.menu_frame = ctk.CTkFrame(self, fg_color="#EAF4FC", border_width=1, border_color="#B8D6EA", corner_radius=12)
        self.menu_frame.place(relx=0.0175, rely=0.08, anchor="nw", relwidth=0.20, relheight=0.57)
        #Créer et placer Boutton pour actualiser
        self.bouton_actualiser = ctk.CTkButton(self,text="Actualiser la carte", compound="left",
        command=lambda: self.map.update_map(self.selection.get(), self.selection_gravite.get()),
        font=("Arial", 15, "bold"), height=52, width=290, corner_radius=10)
        self.bouton_actualiser.place(relx=0.0175, rely=0.65, anchor="nw", relwidth=0.20, relheight=0.05)

        # Variable qui conserve l'année sélectionnée
        self.selection = ctk.StringVar(value="Toutes les années")
        # Dropdown menu pour choisir l'année
        self.menuDeroulantCarte = ctk.CTkOptionMenu(self.menu_frame, variable=self.selection, values=["Toutes les années"])
        self.menuDeroulantCarte.place(relx=0.05, rely=0.12, anchor="nw", relwidth=0.90)
        #Label du dropdown menu
        self.label_annee = ctk.CTkLabel(self.menu_frame, text="Année", font=("Arial", 14, "bold"), text_color="#24527A")
        self.label_annee.place(relx=0.05, rely=0.055, anchor="nw")

        # Variable qui conserve la gravité sélectionnée
        self.selection_gravite = ctk.StringVar(value="Toutes les gravités")
        # Menu déroulant des gravités
        self.menu_gravite = ctk.CTkOptionMenu(self.menu_frame, variable=self.selection_gravite, values=["Toutes les gravités"])
        self.menu_gravite.place(relx=0.05, rely=0.28, anchor="nw", relwidth=0.90)
        # Label du dropdown menu
        self.label_gravite = ctk.CTkLabel(self.menu_frame, text="Gravité", font=("Arial", 14, "bold"), text_color="#24527A")
        self.label_gravite.place(relx=0.05, rely=0.215, anchor="nw")

        # Bouton pour recentrer la carte
        self.bouton_recentrer = ctk.CTkButton(self, text="Recentrer sur Montréal", command=self.map.recentrer_montreal, width=190, height=38, corner_radius=8)
        self.bouton_recentrer.place(relx=0.96, rely=0.07, anchor="ne")

        # Remplir les dropdown menu si des données sont déjà disponibles
        self.actualiser_annee()
        self.actualiser_gravite()

    def actualiser_annee(self):
        # Vérifier si la colonne "AN" existe ou si nous n'avons pas de dataframe
        if self.handler.df is None or "AN" not in self.handler.df.columns:
            return
        # Récupérer les années dans le data frame et mettre dans une liste
        annees = sorted(self.handler.df["AN"].dropna().unique().tolist())
        # Convertir les années en string pour qu'elles rentrent dans le CTkOptionMenu et ajouter l'option de choisir toutes les années
        options_annees = ["Toutes les années"] + [str(annee) for annee in annees]

        # Actualiser les choix du dropdown menu
        self.menuDeroulantCarte.configure(values=options_annees)

        # Réinitialiser la sélection si l'année choisie n'existe plus (Ex.:2019 de déjà sélectionné, puis on loade un CSV avec 2020 à 2025. 2019 vas s'enlever et l'option de base est remise)
        if self.selection.get() not in options_annees:
            self.selection.set("Toutes les années")

    def actualiser_gravite(self):
        # Vérifier si la colonne "GRAVITE" existe ou si nous n'avons pas de dataframe
        if self.handler.df is None or "GRAVITE" not in self.handler.df.columns:
            return
        # Récupérer les gravités dans le data frame et mettre dans une liste en string direct
        gravites = sorted(self.handler.df["GRAVITE"].dropna().astype(str).unique().tolist())
        #Ajouter l'option générale
        options_gravite = ["Toutes les gravités"] + gravites
        self.menu_gravite.configure(values=options_gravite)
        #Vérifier la sélection comme plus haut
        if self.selection_gravite.get() not in options_gravite:
            self.selection_gravite.set("Toutes les gravités")