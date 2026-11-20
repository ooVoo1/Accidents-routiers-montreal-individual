
import customtkinter as ctk
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class FenetreSecteur(ctk.CTkToplevel):

    def __init__(self, master, secteur, donnees):
        super().__init__(master)
        #Donner son nom à la fenêtre en fonctipm du secteur que l'on analyse
        self.title(f"Analyse du secteur : {secteur}")
        self.geometry("950x650")
        #La fenêtre ne peut pas être plus petite sinon l'affichage n'est pas beau
        self.minsize(750, 500)

        #Titre écrit en haut de la page
        titre = ctk.CTkLabel(self, text=f"Analyse des collisions — {secteur}", font=("Arial", 23, "bold"))
        titre.pack(pady=(20, 5))

        #Petit texte qui dit que le graphique affiché actuellement est fait à partir des données affichées sur la carte
        explication = ctk.CTkLabel(self, text="Données correspondant aux filtres appliqués à la carte", font=("Arial", 13))
        explication.pack(pady=(0, 15))

        #Calculer les statistiques sur le secteur à afficher au dessus de la heatmap
        #Nombre de collisions
        nb_collisions = len(donnees)
        #Colonne du dataframe sur les victimes
        victimes = pd.to_numeric(donnees["NB_VICTIMES_TOTAL"], errors="coerce").fillna(0)
        #Colonne du dataframe sur les morts
        deces = pd.to_numeric(donnees["NB_MORTS"], errors="coerce").fillna(0)
        #Nombre total de victimes
        nb_victimes = int(victimes.sum())
        #Nombre total de morts
        nb_deces = int(deces.sum())
        #Calculer le pourcentage des collisions avec des victimes
        pourcentage = (victimes.gt(0).sum() / nb_collisions * 100)

        #Créer le texte à afficher pour les statistiques
        resume = (f"Collisions : {nb_collisions:,}     "
            f"Victimes : {nb_victimes:,}     "
            f"Décès : {nb_deces:,}     "
            f"Collisions avec victimes : {pourcentage:.1f} %").replace(",", " ")
        #Mettre à jour l'affichage de nos statistiques
        label_stats = ctk.CTkLabel(self, text=resume, font=("Arial", 15, "bold"), text_color="#24527A")
        label_stats.pack(pady=(0, 15))

        #Convertir les dates des accidents en format datetime pour pouvoir les traiter
        dates = pd.to_datetime(donnees["DT_ACCDN"], errors="coerce")

        #Se faire un dataframe avec les mois et les jours de la semaine pour notre heatmap
        calendrier = pd.DataFrame({"jour": dates.dt.dayofweek, "mois": dates.dt.month}).dropna()

        #Vérifier si nous avons des dates valides pour construire notre graphique, si non ne pas continuer avec la création du graphique
        #Juste affihcer un message dans l'écran à la place
        if calendrier.empty:
            ctk.CTkLabel(self, text="Aucune date valide disponible pour créer la heatmap.").pack(pady=30)
            return

        #Compter les collisions pour chaque combinaison jour/mois avec .crosstab()
        matrice = pd.crosstab(calendrier["jour"], calendrier["mois"])

        #S'assurer d'avoir les 7 jours et les 12 mois on utilise "fill_value=0" pour remplacer les données manquantes
        #Par exemple si aucune collision n'a eu lieu un dimanche de février avec les filtres sélectionnés on veut juste mettre 0 pas valeur manquante
        matrice = matrice.reindex(index=range(7), columns=range(1, 13), fill_value=0)

        #Créer la figure matplotlib pour mettre la heatmap
        self.figure = Figure(figsize=(9, 4.5), dpi=100)
        ax = self.figure.add_subplot(111)

        #Afficher la matrice sous forme de heatmap cmap = colormap (Yellow Orange Red) aspect="auto" s'assure qu'on remplisse bien tout l'espace du graphique
        image = ax.imshow(matrice, cmap="YlOrRd", aspect="auto")

        #Afficher les noms des mois sur l'axe des X
        mois = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
        ax.set_xticks(range(12))
        ax.set_xticklabels(mois)

        #Afficher les jours de la semaine sur l'axe de Y
        jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        ax.set_yticks(range(7))
        ax.set_yticklabels(jours)

        #Ajouter le titre du graphique et le nom des axes
        ax.set_title("Répartition des collisions selon le mois et le jour")
        ax.set_xlabel("Mois")
        ax.set_ylabel("Jour de la semaine")

        #Barème de couleurs
        self.figure.colorbar(image, ax=ax, label="Nombre de collisions")

        self.figure.tight_layout()

        #Ajouter tout ce qu'on a fait sur matplotlib dans la fenêtre Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()

        #Afficher le graphique
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
