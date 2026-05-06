import os
import time
from collections import Counter

import pandas as pd

from src.preprocess import preprocess_by_period
from src.graph_build import build_graphs_by_period
from src.community import run_community_analysis
from src.community_desc import describe_communities
from src.queries import compare_communities_by_genre
from src.film_community_check import check_movies_community_membership
from src.recommend import (
    recommend_by_genre,
    recommend_by_actor,
    recommend_by_community,
    save_recommendations_examples
)
from src.viz_world_map import build_world_map, build_all_world_maps
from src.load_data import load_all
from src.paths import REPORTS_DIR


# =========================
# Couleurs terminal
# =========================
class Color:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def title(text):
    print(Color.BOLD + Color.CYAN)
    print("=" * 70)
    print(text)
    print("=" * 70 + Color.END)


def pause():
    input(Color.YELLOW + "\nAppuyez sur Entrée pour revenir au menu..." + Color.END)


def normalize_period(period):
    if period is None or period.strip() == "":
        return None
    return period.strip().replace("-", "_")


def print_result(df):
    if df is None or df.empty:
        print(Color.RED + "\nAucun résultat trouvé." + Color.END)
    else:
        print("\n--- Résultat ---")
        print(df.to_string(index=False))


# =========================
# Genres disponibles
# =========================
def get_available_genres():
    movies, _ = load_all()

    genres = set()
    for genre_list in movies["genres_parsed"]:
        if isinstance(genre_list, list):
            for genre in genre_list:
                genres.add(genre)

    return sorted(genres)


def choose_genre():
    genres = get_available_genres()

    title("GENRES DISPONIBLES")

    for i, genre in enumerate(genres, start=1):
        print(f"{i} - {genre}")

    choice = input("\nChoisis un genre par numéro : ").strip()

    if not choice.isdigit():
        print(Color.RED + "Choix invalide." + Color.END)
        return None

    idx = int(choice)

    if idx < 1 or idx > len(genres):
        print(Color.RED + "Numéro de genre invalide." + Color.END)
        return None

    return genres[idx - 1]


# =========================
# Acteurs disponibles
# =========================
def search_actor():
    _, credits = load_all()

    actor_counter = Counter()

    for cast in credits["cast_parsed"]:
        if isinstance(cast, list):
            actor_counter.update(cast)

    query = input("Recherche acteur (ex: Tom, Hanks, Will...) : ").strip().lower()

    if query == "":
        matches = actor_counter.most_common(20)
    else:
        matches = [
            (actor, count)
            for actor, count in actor_counter.most_common()
            if query in actor.lower()
        ][:20]

    if not matches:
        print(Color.RED + "Acteur ne figure pas dans la base." + Color.END)
        return None

    print("\n--- Acteurs trouvés ---")
    for i, (actor, count) in enumerate(matches, start=1):
        print(f"{i} - {actor} ({count} films dans le dataset)")

    choice = input("\nChoisis un acteur par numéro : ").strip()

    if not choice.isdigit():
        print(Color.RED + "Choix invalide." + Color.END)
        return None

    idx = int(choice)

    if idx < 1 or idx > len(matches):
        print(Color.RED + "Numéro invalide." + Color.END)
        return None

    return matches[idx - 1][0]


# =========================
# Communautés disponibles
# =========================
def choose_community():
    path = os.path.join(REPORTS_DIR, "community_description.csv")

    if not os.path.exists(path):
        print(Color.RED + "Le fichier community_description.csv est introuvable." + Color.END)
        print("Lance d'abord l'option 4 : Décrire les communautés.")
        return None, None

    df = pd.read_csv(path)

    period = input("Période souhaitée (1990_1999, 2000_2009, 2010_2019 ou vide) : ").strip()
    period = normalize_period(period)

    if period:
        df = df[df["period"] == period]

    if df.empty:
        print(Color.RED + "Aucune communauté trouvée pour cette période." + Color.END)
        return None, None

    df = df.sort_values(by=["period", "nb_actors"], ascending=[True, False]).reset_index(drop=True)

    title("COMMUNAUTÉS DISPONIBLES")

    for i, row in df.head(30).iterrows():
        print(
            f"{i + 1} - Période {row['period']} | "
            f"Communauté {row['community_id']} | "
            f"{row['top_genres']} | "
            f"{row['nb_actors']} acteurs | "
            f"{row['nb_films']} films"
        )

    choice = input("\nChoisis une communauté par numéro : ").strip()

    if not choice.isdigit():
        print(Color.RED + "Choix invalide." + Color.END)
        return None, None

    idx = int(choice) - 1

    if idx < 0 or idx >= min(30, len(df)):
        print(Color.RED + "Numéro invalide." + Color.END)
        return None, None

    selected = df.iloc[idx]

    return int(selected["community_id"]), selected["period"]


# =========================
# Recommandation interactive
# =========================
def recommendation_menu():
    while True:
        clear()
        title("RECOMMANDATION DE FILMS")

        print("1 - Recommander par genre")
        print("2 - Recommander par acteur")
        print("3 - Recommander par communauté")
        print("4 - Générer des exemples CSV")
        print("0 - Retour au menu principal")

        choice = input("\nVotre choix : ").strip()

        if choice == "1":
            genre = choose_genre()

            if genre is None:
                pause()
                continue

            period = input("Période (1990_1999, 2000_2009, 2010_2019 ou vide) : ").strip()
            period = normalize_period(period)

            top_n = input("Nombre de recommandations : ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10

            result = recommend_by_genre(genre, period=period, top_n=top_n)
            print_result(result)
            pause()

        elif choice == "2":
            actor = search_actor()

            if actor is None:
                pause()
                continue

            top_n = input("Nombre de recommandations : ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10

            result = recommend_by_actor(actor, top_n=top_n)
            print_result(result)
            pause()

        elif choice == "3":
            community_id, period = choose_community()

            if community_id is None:
                pause()
                continue

            top_n = input("Nombre de recommandations : ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10

            result = recommend_by_community(community_id, period=period, top_n=top_n)
            print_result(result)
            pause()

        elif choice == "4":
            save_recommendations_examples()
            pause()

        elif choice == "0":
            break

        else:
            print(Color.RED + "Choix invalide." + Color.END)
            time.sleep(1)


# =========================
# Carte interactive
# =========================
def world_map_menu():
    while True:
        clear()
        title("CARTE MONDE INTERACTIVE")

        print("1 - Générer la carte pour une période")
        print("2 - Générer les cartes pour toutes les périodes")
        print("0 - Retour au menu principal")

        choice = input("\nVotre choix : ").strip()

        if choice == "1":
            period = input("Période (1990_1999, 2000_2009, 2010_2019) : ").strip()
            period = normalize_period(period)

            top_n = input("Nombre d'acteurs à afficher (ex: 80, 100, 150, 200) : ").strip()
            top_n = int(top_n) if top_n.isdigit() else 150

            build_world_map(period=period, top_n=top_n)
            pause()

        elif choice == "2":
            build_all_world_maps()
            pause()

        elif choice == "0":
            break

        else:
            print(Color.RED + "Choix invalide." + Color.END)
            time.sleep(1)


# =========================
# Menu principal
# =========================
def main_menu():
    while True:
        clear()
        title("PROJET GRAPHES & OPEN DATA — CINÉMA")

        print("1 - Prétraiter les données par période")
        print("2 - Construire les graphes par période")
        print("3 - Détecter les communautés Louvain")
        print("4 - Décrire les communautés")
        print("5 - Comparer les communautés par genres")
        print("6 - Vérifier films / communautés")
        print("7 - Recommandation de films")
        print("8 - Générer la carte monde interactive")
        print("0 - Quitter")

        choice = input("\nVotre choix : ").strip()

        if choice == "1":
            title("Prétraitement des données par période")
            preprocess_by_period()
            pause()

        elif choice == "2":
            title("Construction des graphes par période")

            preview_top_n = input(
                "Nombre d'acteurs à afficher dans le HTML preview "
                "(ex: 100, 150, 200 ; 0 = ne pas générer le HTML) : "
            ).strip()

            preview_top_n = int(preview_top_n) if preview_top_n.isdigit() else 150

            build_graphs_by_period(preview_top_n=preview_top_n)
            pause()

        elif choice == "3":
            title("Détection des communautés Louvain")
            run_community_analysis()
            pause()

        elif choice == "4":
            title("Description des communautés")
            describe_communities()
            pause()

        elif choice == "5":
            title("Comparaison des communautés par genres")
            compare_communities_by_genre()
            pause()

        elif choice == "6":
            title("Vérification films / communautés")
            check_movies_community_membership()
            pause()

        elif choice == "7":
            recommendation_menu()

        elif choice == "8":
            world_map_menu()

        elif choice == "0":
            print(Color.GREEN + "\nFin du programme." + Color.END)
            break

        else:
            print(Color.RED + "Choix invalide." + Color.END)
            time.sleep(1)


if __name__ == "__main__":
    main_menu()