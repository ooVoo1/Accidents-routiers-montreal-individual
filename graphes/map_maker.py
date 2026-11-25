import customtkinter as ctk
import pandas as pd
from tkinter import messagebox ,filedialog
from tkintermapview import TkinterMapView
from shapely.geometry import Point
from PIL import Image, ImageDraw, ImageTk, ImageFont, ImageGrab
from graphes.heatmap_secteur import FenetreSecteur

class MapMaker(ctk.CTkFrame):
    def __init__(self, master, handler):
        super().__init__(master)
        self.handler = handler
        #Créer la carte
        self.carte = TkinterMapView(self, corner_radius=0)
        self.carte.pack(fill="both", expand=True)
        self.carte.canvas.bind("<Double-Button-1>", self.double_clic_secteur, add="+") #Commande pour que la carte réagisse aux doubles clics
        #Créer image de 10x10 pixels full transparente
        image_point = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        #Dessiner le point rouge sur notre image transparente
        ImageDraw.Draw(image_point).ellipse((1, 1, 8, 8), fill="#E24747")
        #Transformer en ImageTk pour pouvoir l'utiliser
        self.marqueur_collision = ImageTk.PhotoImage(image_point)
        #Centrer sur Montréal (Coordonnées exactes trouvées par ChatGPT)
        self.carte.set_position(45.54, -73.5673)
        #Garde en mémoire la dernière position pour l'actualisation des points individuels (quand assez zoomé)
        self.derniere_position = self.carte.get_position()
        self.carte.set_zoom(11)
        #Garde en mémoire le dernier couple de filtres utilisé
        self.filtres_actuels = None
        #Garde en mémoire les données filtrées de la carte pour la heatmap par secteur
        self.donnees_filtrees = None
        #Garde en mémoire le zoom actuel
        self.dernier_pas = self.pas_pour_zoom()
        #Surveiller pour un changement de zoom
        self.after(400, self.surveiller_zoom)

    def update_map(self, annee="Toutes les années", gravite="Toutes les gravités", colonne_victime=None, colonne_vehicule=None):
        #Enlever les possibles points sur la carte
        self.carte.delete_all_marker()
        #Enlever les anciennes images de la mémoire
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

        #Associer chaque collision à son secteur si ça n'a pas déjà été fait.
        if "SECTEUR" not in df.columns:
            try:
                self.handler.associer_secteurs()
            except Exception as erreur:
                messagebox.showerror("Erreur GeoJSON", str(erreur))
                return

        #Juste garder les lignes du CSV avec la bonne année
        donnees = df
        if annee != "Toutes les années":
            donnees = donnees[donnees["AN"].astype(str) == annee]

        #Juste garder les lignes du CSV avec la bonne gravité
        if gravite != "Toutes les gravités":
            donnees = donnees[donnees["GRAVITE"].astype(str) == gravite]

        #Filtrer pour le type de victime choisie(on transforme les valeurs en chiffre pour comparer avec 0/ .fillna(0) sert à remplacer 
        #les NaN mis par coerce par des 0)
        if colonne_victime is not None:
            donnees = donnees[pd.to_numeric(donnees[colonne_victime], errors="coerce").fillna(0) > 0]

        #Filtrer pour le type de véhicule choisi (voir explication ci-dessus)
        if colonne_vehicule is not None:
            donnees = donnees[pd.to_numeric(donnees[colonne_vehicule], errors="coerce").fillna(0) > 0]

        #Conserver toutes les colonnes des collisions filtrées pour la heatmap par secteur
        self.donnees_filtrees = donnees

        #Mettre à jour les statistiques en bas de l'écran (.master pour faire appel à une fonction de carte.py
        #qui gère l'affichage et donc, par extension l'affichage des statistiques)
        self.master.mettre_a_jour_stats(donnees)

        #Faire une copie des deux colonnes qui nous intéressent pour pouvoir les convertir en valeurs numériques sans modifier le dataframe de base
        donnees = donnees[["LOC_LAT", "LOC_LONG"]].copy()
        #Convertir les coordonnées en nombres et transformer en NaN les collisions avec une position inconnue pour pouvoir faire .dropna() après
        donnees["LOC_LAT"] = pd.to_numeric(donnees["LOC_LAT"], errors="coerce")
        donnees["LOC_LONG"] = pd.to_numeric(donnees["LOC_LONG"], errors="coerce")

        #Retirer les coordonnées manquantes ou invalides (Genre pas sur la terre)
        donnees = donnees.dropna(subset=["LOC_LAT", "LOC_LONG"])
        donnees = donnees[donnees["LOC_LAT"].between(-90, 90) & donnees["LOC_LONG"].between(-180, 180)]

        #Garder les collisions filtrées et géolocalisées pour les statistiques
        self.donnees_filtrees_geo = donnees
        #Nombre de coordonnées
        total = len(donnees)
        #Message d'erreur si il n'y a pas de collision à afficher
        if total == 0:
            #Actualiser les filtres pour que les statistiques n'affichent pas des faussetés et que des collisions qui n'ont 
            #pas raison d'être réapparaissent après avoir zoomé
            self.filtres_actuels = None
            #Réinitialiser le compteur des collisions affichées sinon il ne s'actualise pas tout seul
            self.master.label_valeur_geolocalisees.configure(text="0")
            messagebox.showinfo("Aucun résultat", "Aucune collision à afficher pour ces filtres.")
            return
        #Garder les filtres actuels pour les réutiliser après avoir utilisé le zoom
        self.filtres_actuels = (annee, gravite, colonne_victime, colonne_vehicule)

        #Définir la taille des zones selon le zoom actuel (plus le pas est petit plus il y a de zones) si le zoom est assez grand,
        #on règle le pas sur None parce qu'on veut voir les collision de façon individuelle (voir fonction plus bas).
        pas = self.pas_pour_zoom()
        # Si le zoom est assez élevé, afficher les collisions individuelles
        if pas is None:
            self.afficher_points(donnees= donnees)
            return
        #Mettre à jour la statistique du nombre de collisions visibles
        self.actualiser_nombre_visible()
        #Ici, on crée deux nouvelles colonnes au dataframe qui vont contenir la "zone" horizontale et verticale
        #à laquelle chaque collision appartient on fait une division entière à plancher pour enlever les décimales
        #et après on fait .astype(int) pour enlever le .0 dans XXXX.0 parce que ça n'a aucun rapport de numéroter avec des décimales
        donnees["zone_lat"] = (donnees["LOC_LAT"] // pas).astype(int)
        donnees["zone_lon"] = (donnees["LOC_LONG"] // pas).astype(int)

        #Regrouper les collisions par case. .agg pour faire plusieurs opérations. On fait la moyenne des positions en lon et en lat
        #des collisions dans la même case pour placer le point de la case fidélement. À la fin on calcule le nombre de collisions
        #dans la zone pour afficher le nombre sur le point représentatif 
        groupes = donnees.groupby(["zone_lat", "zone_lon"]).agg(latitude=("LOC_LAT", "mean"), longitude=("LOC_LONG", "mean"), nombre=("LOC_LAT", "size")).reset_index()

        #Afficher nos points représentatifs calculés précédemment sur la carte
        for groupe in groupes.itertuples(index=False):
            icone = self.creer_icone_groupe(groupe.nombre)
            self.icones_groupes.append(icone)
            self.carte.set_marker(groupe.latitude, groupe.longitude, icon=icone, icon_anchor="center")

    #Fonction qui s'occupe de créer l'icône qui va représenter un regroupement de collisions sur la carte.
    #Prend en compte le nombre de collisions pour déterminer l'aspect de l'icône
    def creer_icone_groupe(self, nombre):
        #Choisir la couleur, la taille de l'icône et taille du texte selon le nombre de collisions à afficher
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
    #Fonction qui décide du pas approprié en fonction du zoom actuel (pas plus petit = plus de cases donc plus de points)
    def pas_pour_zoom(self):
        zoom = round(self.carte.zoom)
        if zoom <= 11:
            return 0.033
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
        
    #Fonction qui surveille constaments les interactions avec la carte pour actualiser l'affichage quand nécessaire
    def surveiller_zoom(self):
        #Déterminer le bon pas pour le zoom actuel
        nouveau_pas = self.pas_pour_zoom()
        #Déterminer la position actuelle de la carte
        position_actuelle = self.carte.get_position()
        #Condition qui vérifie si la carte a été déplacée
        position_changee = position_actuelle != self.derniere_position

        #Vérifier si on a changé le zoom ou si le zoom actuel est None (donc affichage de points individuels) et que la position a changé
        #Si c'est le cas mettre nos variables à jour
        if nouveau_pas != self.dernier_pas or (nouveau_pas is None and position_changee):
            self.dernier_pas = nouveau_pas
            self.derniere_position = position_actuelle
            #Actualiser seulement si la carte a déjà été chargée
            if self.filtres_actuels is not None:
                #Décomposer tuple pour actualiser la carte
                annee, gravite, colonne_victime, colonne_vehicule = self.filtres_actuels
                self.update_map(annee, gravite, colonne_victime, colonne_vehicule)
        #Si il y a seulement la position qui a été changée et que le zoom n'est pas assez haut pour afficher les points individuels
        #alors on actualise seulement la statistique du nombre de collisions affichées (juste si il y a des collisions d'affichée)
        elif position_changee:
            self.derniere_position = position_actuelle
            if self.filtres_actuels is not None:
                self.actualiser_nombre_visible()
        #Continuer de surveiller
        self.after(400, self.surveiller_zoom)

    #Fonction qui est appelée pour afficher les points individuels quand le zoom est assez fort
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

        #Si il y a plus de 1500 points à afficher dans la zone visible, on n'en garde que 1500 pour conserver des performances minimales
        if len(visibles) > 1500:
            visibles = visibles.sample(n=1500, random_state=67)

        #Afficher les collisions sous forme de petits points rouges
        for latitude, longitude in visibles.itertuples(index=False, name=None):
            self.carte.set_marker(latitude, longitude, icon=self.marqueur_collision, icon_anchor="center")
        #Mettre à jour la statistique du nombre de collisions affichées avec le vrai nombre de collisions qu'on affiche (1500 au maximum)
        self.master.label_valeur_geolocalisees.configure(text=f"{len(visibles):,}".replace(",", " "))

    #Fonction qui est reliée au bouton "Recentrer sur Montréal"
    def recentrer_montreal(self):
        #On supprime les anciens points/regroupements avant de déplacer la carte comme ça l'application
        #ne les repositionne pas tous après avoir dézoomé avant de les enlever (c'était super long)
        self.carte.delete_all_marker()
        self.icones_groupes = []

        #Revenir au zoom et à la position initiale
        self.carte.set_zoom(11)
        self.carte.set_position(45.54, -73.5673)

        #On met à jour les variables que l'on surveille pour éviter d'actualiser 2 fois
        self.dernier_pas = self.pas_pour_zoom()
        self.derniere_position = self.carte.get_position()

        #Recréer les regroupements de collisions avec les filtres actuels
        if self.filtres_actuels is not None:
            annee, gravite, colonne_victime, colonne_vehicule = self.filtres_actuels
            self.update_map(annee, gravite, colonne_victime, colonne_vehicule)

    #Actualise la statistique du nombre de "Collisions affichées"
    def actualiser_nombre_visible(self):
        #Récupérer la taille de la carte
        largeur = self.carte.canvas.winfo_width()
        hauteur = self.carte.canvas.winfo_height()

        #Convertir les deux coins (Haut-gauche et bas-droite) de la section visible de la carte en coordonnées
        nord, ouest = self.carte.convert_canvas_coords_to_decimal_coords(0, 0)
        sud, est = self.carte.convert_canvas_coords_to_decimal_coords(largeur, hauteur)

        #Garder les collisions comprises dans cette zone (donnees_filtrees_geo défini dans update_map pour cette utilisation)
        donnees = self.donnees_filtrees_geo
        visibles = donnees[donnees["LOC_LAT"].between(sud, nord) & donnees["LOC_LONG"].between(ouest, est)]

        #Finalement, afficher dans les statistiques le nombre de collisions visibles
        nombre = len(visibles)
        self.master.label_valeur_geolocalisees.configure(text=f"{nombre:,}".replace(",", " "))
    
    #Fonction qui sauvegarde la portion de la carte actuellement visible pour l'export en png
    def sauvegarder_carte(self):
        #".winfo_ismapped()" vérifie si un widget est actuellement visible à l'écran (dans notre cas la carte) et on affiche 
        #un message d'erreur si ce n'est pas le cas, parceque l'export fonctionne avec une capture d'écran donc si la carte
        #n'est pas visible, on va capturer... ben pas la carte
        if not self.carte.winfo_ismapped():
            messagebox.showwarning("Carte non visible", "Veuillez afficher la page Carte avant de l'exporter.")
            return

        #Vérifier si des filtres ont déjà été appliqués à la carte parceque si ce n'est pas le cas, notre petit carré
        #semi-transparent qui dit quels filtres sont appliqués sur la carte afficheras quelque chose de pas vrai.
        if self.filtres_actuels is None:
            messagebox.showwarning("Aucune donnée", "Veuillez actualiser la carte avant de l'exporter.")
            return

        #Exécute toutes les opérations en attente sur la carte (sinon si tu captures juste après avoir actualisé la carte et que
        #les points n'ont pas fini de loader tu capture la carte sans tout les points)
        self.carte.update_idletasks()

        #Récupérer la position du coin haut-gauche de la carte
        gauche = self.carte.winfo_rootx()
        haut = self.carte.winfo_rooty()

        #Calculer la position du coin bas-droite de la carte
        droite = gauche + self.carte.winfo_width()
        bas = haut + self.carte.winfo_height()

        try:
            #Prendre un screenshot de la carte à l'aide des coordonnées déterminées plus haut
            capture = ImageGrab.grab(bbox=(gauche, haut, droite, bas))

            #Récupérer les filtres appliqués sur la carte en décomposant le tuple filtres_actuels
            annee, gravite, colonne_victime, colonne_vehicule = self.filtres_actuels

            #Déterminer quel est le filtre de victime appliqué.
            nom_victime = "Aucun filtre"
            for nom, colonne in self.master.colonnes_victimes.items():
                if colonne == colonne_victime:
                    nom_victime = nom
                    break

            #Déterminer quel est le filtre de véhicule appliqué.
            nom_vehicule = "Aucun filtre"
            for nom, colonne in self.master.colonnes_vehicules.items():
                if colonne == colonne_vehicule:
                    nom_vehicule = nom
                    break

            #Créer une liste avec tout ce que l'on veut écrire sur notre petit carré semi-transparent
            filtres = ["Filtres appliqués",
                f"Année : {annee}",
                f"Gravité : {gravite}",
                f"Type de victime : {nom_victime}",
                f"Véhicule impliqué : {nom_vehicule}"]


            #Créer un objet qui vas nous permettre d'écrire sur le screenshot
            dessin = ImageDraw.Draw(capture, "RGBA")

            #Choisir l'écriture à utiliser avec gestion d'erreur possible pour l'exécutable
            try:
                police = ImageFont.truetype("arial.ttf", 17)
            except OSError:
                police = ImageFont.load_default()

            #On trouve quelle taille doit faire l'encadré pour notre plus longue ligne de texte
            largeur_texte = max(dessin.textbbox((0, 0), ligne, font=police)[2] for ligne in filtres)

            largeur_bloc = largeur_texte + 35
            hauteur_bloc = len(filtres) * 25 + 20

            #Placer notre encadré d'écriture en bas à gauche de l'écran
            x = 15
            y = capture.height - hauteur_bloc - 15

            #Dessiner le fameux encadré (parceque pour l'instant on a décidé la taille et placé "rien")
            dessin.rounded_rectangle((x, y, x + largeur_bloc, y + hauteur_bloc), radius=10, fill=(255, 255, 255, 225))

            #Écrire notre texte déterminé plus haut dans notre encadré
            for i, ligne in enumerate(filtres):
                dessin.text((x + 15, y + 10 + i * 25), ligne, font=police, fill="#183F65")


            #Demander ou et sous quel nom enregistrer l'image
            chemin = filedialog.asksaveasfilename(title="Sauvegarder la carte", defaultextension=".png",
            filetypes=[("Images PNG", "*.png")], initialfile="carte_routesure.png")

            #Pour si l'utilisateur annule avant d'enregistrer
            if not chemin:
                return
            #Finalement, enregistrer la capture de la carte
            capture.save(chemin, "PNG")

        except Exception as erreur:
            messagebox.showerror("Erreur d'exportation", str(erreur))

    #Fonction qui reçoit les coordonnées du double-clic de l'utilisateur et qui s'occupe de les associer
    #à un secteur, de filtrer les données pour ce secteur et de créer la fenêtre popup avec la heatmap
    def selectionner_secteur(self, coordonnees):
        #Charger les arrondissements si ce n'est pas déjà fait
        if self.handler.secteurs is None:
            try:
                self.handler.charger_secteurs()
            except Exception as erreur:
                messagebox.showerror("Erreur GeoJSON", str(erreur))
                return


        #Récupérer les coordonnées du clic de la souris
        latitude, longitude = coordonnees

        #Transformer les coordonnées du clic de souris en objet géométrique utilisable pour Shapely (la bibliothèque sur laquelle geopandas est construite)
        point = Point(longitude, latitude)

        #Trouver les secteurs qui correspondent à notre clic (si on clique sur une frontière il peut en avoir plusieurs)
        secteurs = self.handler.secteurs
        correspondances = secteurs[secteurs.geometry.covers(point)]

        #Vérifier si le clic peut être associé à au moins un secteur, si non arrêter l'exécution de la fonction.
        if correspondances.empty:
            return

        #Récupérer le nom du secteur sélectionné
        secteur = correspondances.iloc[0]["NOM"]

        #Vérifier que la carte a déjà été actualisée (sinon pas de données pour le graphique de heatmap)
        if self.donnees_filtrees is None:
            messagebox.showinfo("Aucune donnée", "Veuillez actualiser la carte avant de sélectionner un secteur.")
            return

        #Juste garder les collisions du bon secteur 
        donnees_secteur = self.donnees_filtrees[self.donnees_filtrees["SECTEUR"] == secteur]

        #Vérifier si le secteur en question a des collisions sinon arrêter l'exécution de la fonction
        if donnees_secteur.empty:
            messagebox.showinfo("Aucun résultat", f"Aucune collision ne correspond aux filtres dans {secteur}.")
            return

        #Créer la fenêtre popup qui contient la heatmap du secteur sélectionné.
        self.fenetre_secteur = FenetreSecteur(self, secteur, donnees_secteur)

    #Fonction qui convertit l'objet "event" de Tkinter en coordonnées que selectionner_secteur() peut utiliser
    def double_clic_secteur(self, event):
        #Convertir la position du double-clic en coordonnées géographiques
        coordonnees = self.carte.convert_canvas_coords_to_decimal_coords(event.x, event.y)

        #Appeler notre fonction existante pour identifier le secteur
        self.selectionner_secteur(coordonnees)

    #Fonction qui est utilisée pour trier et simplifier le jeu de données de la carte pour l'exportation
    def obtenir_donnees_export(self):
        #Vérifier que la carte a déjà été actualisée avec des résultats pour ne pas rien exporter sinon retourner un dataframe vide 
        #pour ne pas que l'application plante
        if self.filtres_actuels is None or self.donnees_filtrees is None:
            return pd.DataFrame()
        donnees = self.donnees_filtrees.copy()
        #Trouver les colonnes qui peuvent potentiellement ne servir à rien
        colonnes_inutiles = [col for col in donnees.columns if col.startswith("nb_")]

        #Supprimer les colonnes de véhicules qui contiennent juste des 0 (elles ne donnent pas d'information utile)
        for colonne in colonnes_inutiles:
            if (donnees[colonne].fillna(0) == 0).all():
                donnees = donnees.drop(columns=[colonne])

        #Supprimer les colonnes qui ne contiennent aucune donnée
        donnees = donnees.dropna(axis=1, how="all")

        return donnees