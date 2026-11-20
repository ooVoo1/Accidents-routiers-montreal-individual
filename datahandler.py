import pandas as pd
import geopandas as gpd

from tkinter import filedialog, messagebox

import os
import sys

class DataHandler():
    """Fait la gestion des fichiers et du DataFrame."""

    def __init__(self):
        self.df = pd.DataFrame() # DataFrame initialement vide.
        self.df_resultats = pd.DataFrame() # Dataframe pour l'exportation des données
        self.graph_resultat = None # Graphique pour l'exportation des données
        self.secteurs = None #Variable pour garder les secteurs en mémoire pour la carte cliquable

    def charger_csv(self):
        """Charger les données."""

        # Demander à l'utilisateur de choisir un fichier CSV.
        chemin = filedialog.askopenfilename(title="Charger fichier CSV", filetypes=[("Fichiers CSV", "*.csv")])

        # Si le cours d'enregistrement est annulé, retoruner rien (ou dans ce cas, False, car on vérifie si le fichier à été chargé).
        if not chemin:
            return False

        # Gestion d'erreurs pour les fichiers qu'on charge.
        try:
            df_temporaire = pd.read_csv(chemin)

            # Vérifier si le fichier est vide
            if df_temporaire.empty:
                raise ValueError("Le fichier CSV est vide.")

            # Liste des colonnes nécessaires au fonctionnement de l'application
            colonnes_obligatoires = ["AN", "DT_ACCDN", "GRAVITE", "NB_MORTS", "NB_BLESSES_GRAVES", "NB_BLESSES_LEGERS", 
            "NB_VICTIMES_TOTAL", "NB_VICTIMES_PIETON", "NB_VICTIMES_MOTO", "NB_VICTIMES_VELO"]

            # Trouver les colonnes manquantes
            colonnes_manquantes = []

            for colonne in colonnes_obligatoires:
                if colonne not in df_temporaire.columns:
                    colonnes_manquantes.append(colonne)

            # Refuser le fichier s'il manque des colonnes
            if colonnes_manquantes:
                raise ValueError("Le fichier CSV ne contient pas toutes les colonnes requises.\n\n"
                "Colonnes manquantes :\n"+ "\n".join(colonnes_manquantes))

            # Accepter le fichier seulement après avoir checké si on as toutes les colonnes
            self.df = df_temporaire
            self.chemin_courante = chemin

            # Réinitialiser les anciens résultats
            self.df_resultats = pd.DataFrame()

            return True

        except Exception as erreur:
            messagebox.showerror("Erreur de chargement",str(erreur))
            return False

    def sauvegarder_fichier(self, file_type):
        """Sauvegarder des fichiers."""

        if file_type == "csv" and self.df_resultats.empty:
            messagebox.showwarning("Alerte", "Aucune donnée à exporter.")
            return

        if file_type == "png" and self.graph_resultat is None:
            messagebox.showwarning("Alerte", "Aucun graphique à exporter.")
            return

        # Extension du fichier en lowercase.
        extension = file_type.lower()

        # Ouvrir l'application de file explorer et demander à l'utilisateur d'écrire le nom du fichier.
        chemin = filedialog.asksaveasfilename(
            title=F"Sauvegarder comme fichier {file_type.upper()}", 
            filetypes=[
                (f"Fichiers {file_type.upper()}", f"*.{extension}")
            ],
            defaultextension=f".{extension}"
        )

        # Si l'utilisateur annule le cours d'enregistrement, retourner rien.
        if not chemin:
            return 

        # Retourner le chemin du fichier.
        return chemin

    def sauvegarder_avec_gestion_erreur(self, save_function, file_type, message):
        """Sauvegarder des fichiers avec la gestion des erreurs."""
        # Gestion d'erreurs.
        try:
            # Acquerir le chemin par la fonction "sauvegarder_fichier"
            path = self.sauvegarder_fichier(file_type)

            # Si le programme a été arreté, retourner rien.
            if not path:
                return

            # Appeler la fonction de sauvegarde d'une classe ou quoi qui ce soit.
            save_function(path)

            # Joli message :)
            print(message)
        except Exception as erreur:
            # Retourner un message d'erreur si quelque chose va mal.
            messagebox.showerror("Erreur", str(erreur))

    def sauvegarder_donnees(self):
        """Sauvegarder des données en fichiers .csv."""

        # Sauvegarder les donnees du dataframe dans un fichier csv.
        self.sauvegarder_avec_gestion_erreur(lambda path: self.df_resultats.to_csv(path, index=False), "csv", "Données enregistrées!")

    def sauvegarder_graphique(self):
        """Sauvegarder un graphique en fichier .png."""

        # Sauvegarder un image du graphique en ficher png.
        self.sauvegarder_avec_gestion_erreur(lambda path: self.graph_resultat.savefig(path), "png", "Graphique enregistrée!")

    def resource_path(self, relative_path):
        try:
            # Dossier temporaire créé par PyInstaller
            base_path = sys._MEIPASS
        except AttributeError:
            # Exécution normale du script Python
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)


    def associer_secteurs(self):
        #Charger le GEOJson si ce n'est pas fait et 
        self.charger_secteurs()
        secteurs = self.secteurs

        #Convertir les coordonnées de toutes les collisions en nombres
        latitudes = pd.to_numeric(self.df["LOC_LAT"], errors="coerce")
        longitudes = pd.to_numeric(self.df["LOC_LONG"], errors="coerce")

        #Juste garder les collisions avec des coordonnées possibles
        valides = latitudes.between(-90, 90) & longitudes.between(-180, 180)

        #Crée une nouvelle colonne dans le dataframe pour assigner les secteurs et remplis cette colonne de NA
        #pour dire qu'aucun secteur n'a été assigné encore
        self.df["SECTEUR"] = pd.NA
        
        #Arrêter l'exécution de la fonction si il n'y a aucune collision avec des coordonnées possibles
        if not valides.any():
            return

        #Mettre les coordonnées sous un format que geopandas peut utiliser
        #On crée un "dataframe géographique" (.GeoDataFrame), sa principale caractéristique est le fait qu'il peut contenir
        #une colonne "geometry" qui contient des objets du type géométriques (points, lignes ou polygones)
        #"index=" détermine quels indices on veut donner aux lignes de notre 
        #nouveau dataframe géographique, dans ce cas on prend seulement les indices "valides" parceque on veut remettre les secteurs
        #trouvés dans notre dataframe normal plus tard. "geometry=" cet argument fournit la colonne "géométrique" du GeoDataFrame
        #(dans notre cas des points) .points_from_xy est utilisé car nous avons des valeurs de longitude et de latitude associée 
        #exactement comme des valeurs de x et y dans un plan cartésien. "crs=" veut dire Coordinate Reference System, on l'utilise 
        #pour indiquer nos données sont sous quel format le code "EPSG:4326" correspond à WGS 84 le format sous lequel mon GEOJson est.
        points = gpd.GeoDataFrame(index=self.df.index[valides], geometry=gpd.points_from_xy(longitudes[valides], latitudes[valides]), crs="EPSG:4326")
      
        #Jointure spatiale (qui donne le dataframe final) entre points et secteurs, c'est plutôt compliqué mais en gros ça
        #associe chaque point au secteur auquel il appartient. "how="left"" indique qu'on veut garder toutes les lignes 
        #du dataframe de gauche, en l'occurence "points". Ceci signifie qu'on garde tout les points même ceux qui ne sont pas 
        # associés à un secteur.  "predicate="within"" est la condition géométrique: on demande à geopandas de trouver pour 
        #chaque collision le polygone (l'arrondissement) auquel elle appartient. 
        resultats = gpd.sjoin(points, secteurs, how="left", predicate="within")

        #Garde un seul secteur pour chaque collision (la jointure spatiale est sujette à créer ce genre de problème)
        #"groupby(level=0)" groupe ensemble toutes les lignes qui ont le même indice et ".first" ne garde que la première
        noms_secteurs = resultats["NOM"].groupby(level=0).first()
        
        #Mettre les secteurs dans notre dataframe original qui est utilisé partout.
        self.df.loc[noms_secteurs.index, "SECTEUR"] = noms_secteurs

    #Fontion qui s'occupe de charger le GEOJson 
    def charger_secteurs(self):
        #Charger le GEOJson contenant les limites administratives de l'île de montréal seulement si ce n'est pas déjà fait
        if self.secteurs is None:
            secteurs = gpd.read_file(self.resource_path("arrondissements_montreal.geojson"))

            #Vérifier que le fichier contient la colonne "NOM" parceque si nous n'avons pas le nom des arrondissements, tout ça sert à rien
            if "NOM" not in secteurs.columns:
                raise ValueError("La colonne NOM est absente du GeoJSON.")

            #Seulement garder les deux colonnes dont a de besoin pour la suite (le nom des secteurs et le polygone qui les 
            #représente dans "geometry") et convertir en "EPSG:4326" (on doit être utiliser le même système partout)
            #Garder les secteurs en mémoire pour que la carte puisse être cliquable sans tout recalculer en tout temps.
            self.secteurs = secteurs[["NOM", "geometry"]].to_crs("EPSG:4326")
