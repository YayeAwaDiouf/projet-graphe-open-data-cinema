import os
import pickle
from collections import Counter

import pandas as pd
import networkx as nx
import community as community_louvain

from src.paths import GRAPHS_DIR, PROCESSED_DATA_DIR, REPORTS_DIR
from src.load_data import load_all


def check_movies_community_membership():
    """
    Pour chaque période :
    - charge le graphe de la période
    - détecte les communautés Louvain
    - regarde, film par film, à quelles communautés appartiennent les acteurs
    - identifie la communauté dominante du film
    """

    os.makedirs(REPORTS_DIR, exist_ok=True)

    movies_all, credits = load_all()

    # movie_id -> cast
    movie_cast = dict(zip(credits["movie_id"], credits["cast_parsed"]))

    rows = []

    for graph_file in os.listdir(GRAPHS_DIR):
        if not (graph_file.startswith("graph_") and graph_file.endswith(".gpickle")):
            continue

        period = graph_file.replace("graph_", "").replace(".gpickle", "")
        print(f"\n=== Vérification films / communautés : {period} ===")

        graph_path = os.path.join(GRAPHS_DIR, graph_file)

        with open(graph_path, "rb") as f:
            G = pickle.load(f)

        # Plus grande composante connexe
        largest_cc = max(nx.connected_components(G), key=len)
        G_lcc = G.subgraph(largest_cc).copy()

        # Louvain
        partition = community_louvain.best_partition(G_lcc)

        # Charger les films de la période
        movies_period_path = os.path.join(
            PROCESSED_DATA_DIR,
            f"movies_{period}.csv"
        )

        movies_period = pd.read_csv(movies_period_path)

        for _, movie in movies_period.iterrows():
            movie_id = movie["id"]
            title = movie["title"]
            year = movie.get("release_year", None)

            cast = movie_cast.get(movie_id, [])

            # On garde seulement les acteurs présents dans la partition Louvain
            actor_communities = [
                partition[actor]
                for actor in cast
                if actor in partition
            ]

            if len(actor_communities) == 0:
                continue

            community_counts = Counter(actor_communities)
            dominant_community, dominant_count = community_counts.most_common(1)[0]

            nb_actors_in_graph = len(actor_communities)
            dominant_share = dominant_count / nb_actors_in_graph

            # Film cohérent si au moins 60% des acteurs appartiennent à la même communauté
            is_coherent = dominant_share >= 0.60

            rows.append({
                "period": period,
                "movie_id": movie_id,
                "title": title,
                "release_year": year,
                "nb_cast_total": len(cast),
                "nb_cast_in_graph": nb_actors_in_graph,
                "nb_communities_in_movie": len(community_counts),
                "dominant_community": dominant_community,
                "dominant_community_count": dominant_count,
                "dominant_community_share": round(dominant_share, 3),
                "is_coherent_with_community": is_coherent,
                "communities_distribution": dict(community_counts)
            })

    df = pd.DataFrame(rows)

    output_path = os.path.join(REPORTS_DIR, "movie_community_check.csv")
    df.to_csv(output_path, index=False)

    print(f"\n✔ Vérification sauvegardée : {output_path}")

    # Petit résumé terminal
    print("\n--- Résumé ---")
    print("Nombre de films analysés :", len(df))
    print("Films cohérents avec une communauté :", df["is_coherent_with_community"].sum())
    print("Films ponts / mixtes :", len(df) - df["is_coherent_with_community"].sum())


if __name__ == "__main__":
    check_movies_community_membership()