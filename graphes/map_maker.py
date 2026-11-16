import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from tkintermapview import TkinterMapView
from PIL import Image, ImageDraw, ImageTk, ImageFont

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
        self.carte.set_position(45.54, -73.5673)
        #Garde en mémoire la dernière position pour l'actualisation des points individuels (quand assez zoomé)
        self.derniere_position = self.carte.get_position()
        self.carte.set_zoom(11)
        #Garde en mémoire le dernier couple de filtre utilisé
        self.filtres_actuels = None
        #Garde en mémoire le zoom actuel
        self.dernier_pas = self.pas_pour_zoom()
        #Surveiller pour un changement de zoom
        self.after(400, self.surveiller_zoom)

    def update_map(self, annee="Toutes les années", gravite="Toutes les gravités"):
        #Enlever les possibles points sur la carte
        self.carte.delete_all_marker()
        #Enlève les anciennes images de la mémoire
        self.icones_groupes = []

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
        #Message d'erreur si il n'y a pas de collision à afficher
        if total == 0:
            messagebox.showinfo("Aucun résultat", "Aucune collision à afficher pour ces filtres.")
            return
        #Garder les filtres actuels pour les réutiliser après avoir utilisé le zoom
        self.filtres_actuels = (annee, gravite)

        #Définir la taille des zones selon le zoom actuel (plus le pas est petit plus il y a de zones) si le zoom est assez grand,
        #on régle le pas sur None parcqu'on veut voir les collision de façon individuelle (voir fonction plus bas).
        pas = self.pas_pour_zoom()
        # Si le zoom est assez élevé, afficher les collisions individuelles
        if pas is None:
            self.afficher_points(donnees= donnees)
            return
        #Ici, on créée deux nouvelles colonnes au dataframe qui vont contenir la "zone" horizontale et verticale
        #à laquelle chaque collision appartient on fait une division entière à plancher pour enlever les décimales
        #et après on fait .astype(int) pour enlever le .0 dans XXXX.0 parceque ça n'a aucun rapport de numéroter avec des décimales
        donnees["zone_lat"] = (donnees["LOC_LAT"] // pas).astype(int)
        donnees["zone_lon"] = (donnees["LOC_LONG"] // pas).astype(int)

        #Regrouper les collisions par case. .agg pour faire plusieurs opérations. On fait la moyenne des position en lon et en lat
        #des collisions dans la même case pour placer le point de la case fidélement. À la fin on calcule le nombre de collisions
        #dans la zone pour afficher le nombre sur le point représentatif 
        groupes = donnees.groupby(["zone_lat", "zone_lon"]).agg(latitude=("LOC_LAT", "mean"), longitude=("LOC_LONG", "mean"), nombre=("LOC_LAT", "size")).reset_index()

        #Afficher nos points représentatifs calculés précédemment sur la carte
        for groupe in groupes.itertuples(index=False):
            icone = self.creer_icone_groupe(groupe.nombre)
            self.icones_groupes.append(icone)
            self.carte.set_marker(groupe.latitude, groupe.longitude, icon=icone, icon_anchor="center")

        print(f"{total} collisions représentées dans {len(groupes)} regroupements.")

    def creer_icone_groupe(self, nombre):
        #Choisir la couleur, la taille de l'icone et taille du texte selon le nombre de collisions à afficher
        if nombre < 25:
            couleur = "#0CC021"
            taille_icone = 28
            taille_texte = 11
        elif nombre < 100:
            couleur = "#2878BD"
            taille_icone = 32
            taille_texte = 12
        elif nombre < 500:
            couleur = "#EDF50B"
            taille_icone = 36
            taille_texte = 12
        elif nombre < 1000:
            couleur = "#E1800A"
            taille_icone = 40
            taille_texte = 12
        else:
            couleur = "#E24747"
            taille_icone = 46
            taille_texte = 13

        #Créer une image full transparente
        image = Image.new("RGBA", (taille_icone, taille_icone), (0, 0, 0, 0))
        #Fournit un objet qui permet de dessiner sur l'image
        dessin = ImageDraw.Draw(image)

        #Définir les coordonnées du carré pour que Pillow puisse dessiner le cercle à l'intérieur de ce dernier
        #tout en laissant une légère marge pour que les bords du cercle ne soient pas coupés
        marge = 1
        x1 = marge
        y1 = marge
        x2 = taille_icone - marge - 1
        y2 = taille_icone - marge - 1

        #Dessiner le cercle
        dessin.ellipse((x1, y1, x2, y2), fill=couleur, outline="white", width=2)

        #Charger la police du texte avec gestion d'erreur possible pour l'exécutable
        try:
            police = ImageFont.truetype("arial.ttf", taille_texte)
        except OSError:
            police = ImageFont.load_default()

        #Écrire le nombre de collisions au centre du cercle
        centre = taille_icone // 2
        dessin.text((centre, centre), str(nombre), font=police, fill="black", anchor="mm")

        return ImageTk.PhotoImage(image)

    def pas_pour_zoom(self):
        zoom = round(self.carte.zoom)
        if zoom <= 11:
            return 0.03
        elif zoom == 12:
            return 0.02
        elif zoom == 13:
            return 0.01
        elif zoom == 14:
            return 0.007
        elif zoom == 15:
            return 0.0045
        else:
            #À partir de 16, retourner None comme signal à update_map pour qu'elle affiche les points individuels, sans regroupements
            return None

    def surveiller_zoom(self):
        #Déterminer le bon pas por le zoom actuel
        nouveau_pas = self.pas_pour_zoom()
        #Déterminer la position actuelle de la carte
        position_actuelle = self.carte.get_position()
        #Condition qui regarde si nous sommes bien assez zoomé pour l'affichage individuel puis qui regarde aussi
        #si le centre de la zone affichée a changé
        position_changee = nouveau_pas is None and position_actuelle != self.derniere_position

        #Vérifier si on as changé le zoom ou si on as bougé l'affichage; Si c'est le cas mettre nos variables à jour
        if nouveau_pas != self.dernier_pas or position_changee:
            self.dernier_pas = nouveau_pas
            self.derniere_position = position_actuelle

            #Actualiser seulement si la carte à déjà été chargée
            if self.filtres_actuels is not None:
                #Décomposer tuple pour actualiser la carte
                annee, gravite = self.filtres_actuels
                self.update_map(annee, gravite)

        #Continuer de surveiller
        self.after(400, self.surveiller_zoom)

    
    def afficher_points(self, donnees):
        #Récupérer la taille de la carte
        largeur = self.carte.canvas.winfo_width()
        hauteur = self.carte.canvas.winfo_height()

        #Convertir les deux coins (Haut-gauche et bas-droite) de la section visible de la carte en coordonnées
        nord, ouest = self.carte.convert_canvas_coords_to_decimal_coords(0, 0)
        sud, est = self.carte.convert_canvas_coords_to_decimal_coords(largeur, hauteur)

        #N'afficher que les collisions présentes dans la zone visible pour que mon pc ne décède pas (en gros, à des fins de performances)
        #(sinon on affiche les 200 quelques milles collisions d'un coup...)
        visibles = donnees[donnees["LOC_LAT"].between(sud, nord) & donnees["LOC_LONG"].between(ouest, est)]

        #Si il y a plus de 800 points à afficher dans la zone visible, on en garde que 800 pour conserver des performances minimales
        if len(visibles) > 1500:
            visibles = visibles.sample(n=1500, random_state=67)

        #Afficher les collisions sous forme de petits points rouge
        for latitude, longitude in visibles.itertuples(index=False, name=None):
            self.carte.set_marker(latitude, longitude, icon=self.marqueur_collision, icon_anchor="center")
        print(f"{len(visibles)} collisions individuelles affichées.")

        
    def recentrer_montreal(self):
        self.carte.set_position(45.54, -73.5673)
        self.carte.set_zoom(11)