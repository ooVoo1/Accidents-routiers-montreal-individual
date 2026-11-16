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
        #Créer et placer Boutton pour actualiser avec fonction lambda qui vas chercher l'info des 4 drop down menu pour actualiser la carte
        self.bouton_actualiser = ctk.CTkButton(self,text="Actualiser la carte", compound="left",
        command=lambda: self.map.update_map(self.selection.get(), self.selection_gravite.get(),
        self.colonnes_victimes.get(self.selection_victime.get()), self.colonnes_vehicules.get(self.selection_vehicule.get())), #Ici, il faut aller les chercher les bon noms de colonnes dans les dico d'équivalence
        font=("Arial", 15, "bold"), height=52, width=290, corner_radius=10)
        self.bouton_actualiser.place(relx=0.0175, rely=0.65, anchor="nw", relwidth=0.20, relheight=0.05)

        #Variable qui conserve l'année sélectionnée
        self.selection = ctk.StringVar(value="Toutes les années")
        #Dropdown menu pour choisir l'année
        self.menuDeroulantCarte = ctk.CTkOptionMenu(self.menu_frame, variable=self.selection, values=["Toutes les années"])
        self.menuDeroulantCarte.place(relx=0.05, rely=0.12, anchor="nw", relwidth=0.90)
        #Label du dropdown menu
        self.label_annee = ctk.CTkLabel(self.menu_frame, text="Année", font=("Arial", 14, "bold"), text_color="#24527A")
        self.label_annee.place(relx=0.05, rely=0.055, anchor="nw")

        #Variable qui conserve la gravité sélectionnée
        self.selection_gravite = ctk.StringVar(value="Toutes les gravités")
        #Menu déroulant des gravités
        self.menu_gravite = ctk.CTkOptionMenu(self.menu_frame, variable=self.selection_gravite, values=["Toutes les gravités"])
        self.menu_gravite.place(relx=0.05, rely=0.28, anchor="nw", relwidth=0.90)
        #Label du dropdown menu
        self.label_gravite = ctk.CTkLabel(self.menu_frame, text="Gravité", font=("Arial", 14, "bold"), text_color="#24527A")
        self.label_gravite.place(relx=0.05, rely=0.215, anchor="nw")

        #Variable qui conserve le type de victime sélectionnée
        self.selection_victime = ctk.StringVar(value="Aucun filtre")
        #Menu déroulant des types de victimes
        self.menu_victime = ctk.CTkOptionMenu(self.menu_frame, variable=self.selection_victime, values=["Aucun filtre"])
        self.menu_victime.place(relx=0.05, rely=0.44, anchor="nw", relwidth=0.90)
        #Label du dropdown menu
        self.label_victime = ctk.CTkLabel(self.menu_frame, text="Type de victime", font=("Arial", 14, "bold"), text_color="#24527A")
        self.label_victime.place(relx=0.05, rely=0.375, anchor="nw")

        #Variable qui conserve le type de véhicule sélectionné
        self.selection_vehicule = ctk.StringVar(value="Aucun filtre")
        #Menu des types véhicules impliqués
        self.menu_vehicule = ctk.CTkOptionMenu(self.menu_frame, variable=self.selection_vehicule, values=["Aucun filtre"])
        self.menu_vehicule.place(relx=0.05, rely=0.60, anchor="nw", relwidth=0.90)
        #Label du menu
        self.label_vehicule = ctk.CTkLabel(self.menu_frame, text="Véhicule impliqué", font=("Arial", 14, "bold"), text_color="#24527A")
        self.label_vehicule.place(relx=0.05, rely=0.535, anchor="nw")

        #Bouton pour recentrer la carte
        self.bouton_recentrer = ctk.CTkButton(self, text="Recentrer sur Montréal", command=self.map.recentrer_montreal, width=190, height=38, corner_radius=8)
        self.bouton_recentrer.place(relx=0.96, rely=0.07, anchor="ne")

        #Remplir les dropdown menu si des données sont déjà disponibles
        self.actualiser_dropdowns()

    def actualiser_annee(self):
        #Vérifier si la colonne "AN" existe ou si nous n'avons pas de dataframe
        if self.handler.df is None or "AN" not in self.handler.df.columns:
            return
        #Récupérer les années dans le data frame et mettre dans une liste
        annees = sorted(self.handler.df["AN"].dropna().unique().tolist())
        #Convertir les années en string pour qu'elles rentrent dans le CTkOptionMenu et ajouter l'option de choisir toutes les années
        options_annees = ["Toutes les années"] + [str(annee) for annee in annees]

        #Actualiser les choix du dropdown menu
        self.menuDeroulantCarte.configure(values=options_annees)

        #Réinitialiser la sélection si l'année choisie n'existe plus (Ex.:2019 de déjà sélectionné, puis on loade un CSV avec 2020 à 2025. 2019 vas s'enlever et l'option de base est remise)
        if self.selection.get() not in options_annees:
            self.selection.set("Toutes les années")

    def actualiser_gravite(self):
        #Vérifier si la colonne "GRAVITE" existe ou si nous n'avons pas de dataframe
        if self.handler.df is None or "GRAVITE" not in self.handler.df.columns:
            return
        #Récupérer les gravités dans le data frame et mettre dans une liste en string direct
        gravites = sorted(self.handler.df["GRAVITE"].dropna().astype(str).unique().tolist())
        #Ajouter l'option générale et mettre à jour les choix du menu avec .configure
        options_gravite = ["Toutes les gravités"] + gravites
        self.menu_gravite.configure(values=options_gravite)
        #Vérifier la sélection comme plus haut(actualiser_annee)
        if self.selection_gravite.get() not in options_gravite:
            self.selection_gravite.set("Toutes les gravités")
    
    def actualiser_victimes(self):
        #Dictionnaire d'équivalence pour avoir des belles options dans l'application
        self.colonnes_victimes = {
            "Au moins une victime": "NB_VICTIMES_TOTAL", "Au moins un décès": "NB_MORTS", "Au moins un blessé grave": "NB_BLESSES_GRAVES",
            "Au moins un blessé léger": "NB_BLESSES_LEGERS", "Piéton victime": "NB_VICTIMES_PIETON", "Piéton décédé": "NB_DECES_PIETON", 
            "Piéton blessé": "NB_BLESSES_PIETON", "Motocycliste victime": "NB_VICTIMES_MOTO", "Motocycliste décédé": "NB_DECES_MOTO",
            "Motocycliste blessé": "NB_BLESSES_MOTO", "Cycliste victime": "NB_VICTIMES_VELO", "Cycliste décédé": "NB_DECES_VELO", "Cycliste blessé": "NB_BLESSES_VELO"}
        #Arrêter l'exécution si nous n'avons pas de dataframe
        if self.handler.df is None:
            return
        
        #Juste Garder les colonnes qui sont présente dans le csv (Gestion d'erreur si qqu charge un CSV sous le mauvais format) et ajouter l'option générale
        options = ["Aucun filtre"]
        for nom, colonne in self.colonnes_victimes.items():
            if colonne in self.handler.df.columns:
                options.append(nom)
        #Mettre à jour les choix du menu avec .configure
        self.menu_victime.configure(values=options)
        #Vérifier la sélection comme plus haut(actualiser_annee)
        if self.selection_victime.get() not in options:
            self.selection_victime.set("Aucun filtre")


    def actualiser_vehicules(self):
        #Dictionnaire d'équivalence pour avoir des belles options dans l'application
        self.colonnes_vehicules = {
            "Automobile / camion léger": "nb_automobile_camion_leger", "Camion lourd / tracteur routier": "nb_camionLourd_tractRoutier",
            "Autobus / minibus": "nb_tous_autobus_minibus", "Bicyclette": "nb_bicyclette", "Cyclomoteur": "nb_cyclomoteur",
            "Motocyclette": "nb_motocyclette", "Taxi": "nb_taxi", "Véhicule d'urgence": "nb_urgence", "Motoneige": "nb_motoneige",
            "Véhicule hors route": "nb_VHR", "Outil / équipement": "nb_outil_equipement"}
        #Arrêter l'exécution si nous n'avons pas de dataframe
        if self.handler.df is None:
            return

        #Juste Garder les colonnes qui sont présente dans le csv (Gestion d'erreur si qqu charge un CSV sous le mauvais format) et ajouter l'option générale
        options = ["Aucun filtre"]
        for nom, colonne in self.colonnes_vehicules.items():
            if colonne in self.handler.df.columns:
                options.append(nom)
        #Mettre à jour les choix du menu avec .configure
        self.menu_vehicule.configure(values=options)
        #Vérifier la sélection comme plus haut (actualiser_annee)
        if self.selection_vehicule.get() not in options:
            self.selection_vehicule.set("Aucun filtre")

    #Fonction pour racourcir le code dans le main et dans le constructeur de Carte
    def actualiser_dropdowns(self):
        self.actualiser_annee()
        self.actualiser_gravite()
        self.actualiser_victimes()
        self.actualiser_vehicules()