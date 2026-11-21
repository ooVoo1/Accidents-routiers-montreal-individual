import customtkinter as ctk
import os

from PIL import Image
from datahandler import DataHandler

class Aide(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Pour que la page remplisse la fenetre
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.handler = DataHandler()

        # Créer la page d'aide.
        self.creer_page_aide()

    def creer_page_aide(self):
        #Zone défilable
        zone_aide = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=0)
        zone_aide.grid(row=0, column=0, sticky="nsew")
        
        #Vitesse du défilement
        zone_aide._parent_canvas.configure(yscrollincrement=4)

        #Conteneur principal
        conteneur = ctk.CTkFrame(zone_aide, fg_color="transparent")
        conteneur.pack(fill="both", padx=60, pady=30)

        #Titre de la page
        titre = ctk.CTkLabel(conteneur, text="Page d'aide RouteSûre", font=("Arial", 30, "bold"), text_color="#133E70")
        titre.pack(pady=(0, 12))
        
        #Texte d'accueil
        introduction = ctk.CTkLabel(conteneur, text="Découvrez comment importer, visualiser et analyser les données des collisions routières de Montréal.", font=("Arial", 15), text_color="#64748B", wraplength=850)
        introduction.pack(pady=(0, 25))

        #Garder les images en mémoire
        self.images_aide = []

        #Fonction pour créer une section de la page
        def ajouter_section(titre, texte, captures=None):
            #Créer section
            section = ctk.CTkFrame(conteneur, fg_color="#EDF5FF", corner_radius=12)
            section.pack(fill="x", pady=10)

            #Titre de la section
            titre_section = ctk.CTkLabel(section, text=titre, font=("Arial", 19, "bold"), text_color="#133E70", anchor="w")
            titre_section.pack(fill="x", padx=25, pady=(18, 8))

            #Ajouter texte d'explication
            texte_section = ctk.CTkLabel(section, text=texte, font=("Arial", 15), text_color="#475569", justify="left", anchor="w", wraplength=900)
            texte_section.pack(fill="x", padx=25, pady=(0, 18))

            #Ajouter des screenshots pour aider plus =)
            if captures:
                for capture in captures:
                    if os.path.exists(self.handler.resource_path("images/" + capture)):
                        image = Image.open(self.handler.resource_path("images/" + capture))

                        # Mettre à la bonne taille
                        largeur = min(image.width, 750)
                        hauteur = int(largeur * image.height / image.width)
                        image_aide = ctk.CTkImage(light_image=image, dark_image=image, size=(largeur, hauteur))
                        self.images_aide.append(image_aide)

                        #Afficher l'image dans la section
                        label_image = ctk.CTkLabel(section, image=image_aide, text="")
                        label_image.pack(pady=(5, 20), padx=20)

        #Ajout des sections
        ajouter_section("1. Charger des données CSV", "Depuis la page d'accueil, cliquez sur « Charger des données CSV ».\n\n"
        "Une fenêtre s'ouvrira pour vous permettre de sélectionner un fichier CSV contenant les données des collisions routières.\n\n"
        "Une fois le fichier chargé, les graphiques disponibles seront automatiquement actualisés.",
        ["chargement1.png", "chargement2.png"])

        ajouter_section("2. Naviguer dans l'application", "Depuis l'accueil, cliquez sur l'une des quatre grandes cartes pour accéder à la page souhaitée.\n\n"
        "Vous pouvez également utiliser, à tout moment, la barre située dans le haut de la fenêtre pour naviguer à travers l'application.",
        ["navigation1.png","navigation2.png"])

        ajouter_section("3. Graphique d'évolution annuelle", "Ce graphique permet de visualiser l'évolution des collisions et des victimes au fil des années.\n\n"
        "Utilisez le menu « Statistique à afficher » pour sélectionner le nombre de collisions, de morts, de blessés ou d'autres catégories de victimes.\n\n"
        "Le graphique et le résumé statistique s'actualiseront selon votre sélection.",
        ["evolution.png"])

        ajouter_section("4. Graphique circulaire", "Le graphique circulaire permet d'observer la répartition des collisions selon leur gravité.\n\n"
        "Sélectionnez une année dans le menu déroulant. Chaque portion représente une catégorie de gravité, exprimée en pourcentage.",
        ["circulaire.png"])

        ajouter_section("5. Graphique à barres", "Le graphique à barres permet d'observer la répartition d'un certain type de victime à travers les mois d'une année.\n\n"
        "Sélectionnez une année et un type de victime dans les menus déroulants. Chaque barre représente le nombre de victime dans un mois de l'année sélectionnée.",
        ["barre.png"])

        ajouter_section("6. Carte interactive","La carte interactive permet de visualiser la répartition géographique des collisions routières sur l'île de Montréal.\n\n"
        "Sélectionnez les filtres que vous souhaitez appliquer aux données parmi l'année, la gravité des collisions, "
        "le type de victime et le type de véhicule impliqué. Cliquez ensuite sur « Actualiser la carte » pour afficher "
        "les collisions correspondant à vos critères. Les statistiques situées sous la carte seront également mises à jour.\n\n"
        "Vous pouvez déplacer la carte et utiliser le zoom pour explorer différentes zones de Montréal. "
        "Pour revenir à la position et au niveau de zoom initiaux, cliquez sur « Recentrer sur Montréal ».",
        ["carte1.png", "carte2.png"])

        ajouter_section("7. Analyse par secteur","Une fois les collisions affichées sur la carte, vous pouvez double-cliquer sur un secteur de Montréal "
        "pour accéder à une analyse plus détaillée de celui-ci.\n\n"
        "Une nouvelle fenêtre s'ouvrira et présentera plusieurs statistiques sur le secteur sélectionné, "
        "notamment le nombre de collisions, le nombre de victimes, le nombre de décès et le pourcentage de collisions impliquant des victimes. "
        "Elle contiendra également une carte thermique (heatmap) illustrant la répartition des collisions selon "
        "les jours de la semaine et les mois de l'année.\n\n"
        "Les résultats présentés tiendront compte des filtres appliqués à la carte interactive.",
        ["secteur1.png", "secteur2.png"])

        ajouter_section("8. Exporter les données en CSV", "L'objectif de cette fonctionnalité est de permettre l'enregistrement des données représentées dans le graphique.\n\n"
        "Vous pouvez utiliser le menu « Fichier », sélectionner l'option « Sauvegarder Données », puis choisir le nom et l'emplacement du fichier CSV.\n\n"
        "La procédure est la même pour exporter les données de la carte interactive. Dans ce cas, toutes les collisions correspondant aux filtres appliqués seront enregistrées dans le fichier CSV.",
        ["export_csv1.png","export_csv2.png"])

        ajouter_section("9. Enregistrer un graphique en PNG", "Une fonctionnalité d'exportation permet de sauvegarder le graphique affiché sous forme d'image PNG.\n\n"
        "Vous pourrez ainsi réutiliser le graphique dans des présentations, des rapports ou d'autres documents. Sélectionner l'option Sauvegarder Graphique, puis choisir le nom et l'emplacement du fichier PNG.",
        ["export_png1.png", "export_png2.png"])

        ajouter_section("10. Enregistrer la carte en PNG", "Vous pouvez également sauvegarder une image de la carte interactive telle qu'elle apparaît à l'écran.\n\n"
        "Pour ce faire, affichez la zone géographique souhaitée et appliquez vos filtres en cliquant sur "
        "« Actualiser la carte ». Ouvrez ensuite le menu « Fichier » et sélectionnez « Sauvegarder carte ». "
        "Choisissez le nom et l'emplacement du fichier PNG.\n\n"
        "L'image enregistrée comprendra la portion visible de la carte ainsi qu'un encadré indiquant "
        "les filtres appliqués, ce qui facilitera son utilisation dans un rapport ou une présentation.",
        ["export_carte1.png", "export_carte2.png", "export_carte3.png"])
