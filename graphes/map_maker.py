import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from tkintermapview import TkinterMapView
from PIL import Image, ImageDraw, ImageTk

class MapMaker(ctk.CTkFrame):
    def __init__(self, master, handler):
        super().__init__(master)
        self.handler = handler
        #Créer la carte
        self.carte = TkinterMapView(self, corner_radius=0)
        self.carte.pack(fill="both", expand=True)
        #Créer image de 10x10 pixel full transparente
        image_point = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        #Dessiner le point rouge sur notre image transparente
        ImageDraw.Draw(image_point).ellipse((1, 1, 8, 8), fill="#E24747")
        #Transformer en ImageTk pour pouvoir l'utiliser
        self.marqueur_collision = ImageTk.PhotoImage(image_point)
        #Centrer sur Montréal (Coordonnées exactes trouvée par ChatGPT)
        self.carte.set_position(45.5017, -73.5673)
        self.carte.set_zoom(11)

    
    def update_map(self, annee="Toutes les années", gravite="Toutes les gravités"):
        #Enlever les possibles points sur la carte
        self.carte.delete_all_marker()

        # Vérifier que le CSV est chargé
        if self.handler.df is None or self.handler.df.empty:
            messagebox.showwarning("Aucune donnée", "Veuillez charger un fichier CSV.")
            return
        df = self.handler.df
        #Vérifier que les colonnes obligatoires existent
        colonnes = ["AN", "GRAVITE", "LOC_LAT", "LOC_LONG"]
        if not all(colonne in df.columns for colonne in colonnes):
            messagebox.showerror("Erreur", "Certaines colonnes nécessaires sont absentes du CSV.")
            return

        #Juste garder les lignes du CSV avec la bonne année
        donnees = df
        if annee != "Toutes les années":
            donnees = donnees[donnees["AN"].astype(str) == annee]

        #Juste garder les lignes du CSV avec la bonne gravité
        if gravite != "Toutes les gravités":
            donnees = donnees[donnees["GRAVITE"].astype(str) == gravite]

        #Faire une copie des deux colonnes qui nous intéressent pour pouvoir les convertir en valeurs numériques sans modifier le dataframe de base
        donnees = donnees[["LOC_LAT", "LOC_LONG"]].copy()

        #Convertir les coordonnées en nombres et transformer en NaN les collisions avec une position inconnue pour pouvoir faire dropna après
        donnees["LOC_LAT"] = pd.to_numeric(donnees["LOC_LAT"], errors="coerce")
        donnees["LOC_LONG"] = pd.to_numeric(donnees["LOC_LONG"], errors="coerce")

        #Retirer les coordonnées manquantes ou invalides (Genre pas sur la terre)
        donnees = donnees.dropna(subset=["LOC_LAT", "LOC_LONG"])
        donnees = donnees[donnees["LOC_LAT"].between(-90, 90) & donnees["LOC_LONG"].between(-180, 180)]
        #Nombre de coordonnées
        total = len(donnees)
        if total == 0:
            messagebox.showinfo("Aucun résultat", "Aucune collision à afficher pour ces filtres.")
            return

        #Si il y a plus que 500 points à afficher(c'est presque tout le temps le cas), on en choisis 500 au hasard dans ceux qu'on a
        #(Parceque sinon ça plantait. Essayer d'afficher les 200 000 collisions du CSV...)
        if total > 500:
            donnees = donnees.sample(n=500, random_state=67)

        #Parcours les lignes du dataframe sous forme du tuple (il ne reste que les deux lignes avec les coordonnées)
        #et affiche chaque point comme un marqueur sur la carte
        for latitude, longitude in donnees.itertuples(index=False, name=None):
            self.carte.set_marker(latitude, longitude, icon=self.marqueur_collision, icon_anchor="center")

        print(f"{len(donnees)} collisions affichées sur {total} collisions géolocalisées.")



    def recentrer_montreal(self):
        self.carte.set_position(45.5017, -73.5673)
        self.carte.set_zoom(11)