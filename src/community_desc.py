import os
import pickle
from collections import Counter, defaultdict

import pandas as pd
import networkx as nx
import community as community_louvain

from src.paths import GRAPHS_DIR, REPORTS_DIR, RAW_DATA_DIR
from src.load_data import load_all


def describe_communities():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Charger les CSV complets
    movies, credits = load_all()

    # movie_id -> genres
    movie_genres = dict(zip(movies["id"], movies["genres_parsed"]))

    # movie_id -> cast
    movie_cast = dict(zip(credits["movie_id"], credits["cast_parsed"]))

    rows = []

    for file in os.listdir(GRAPHS_DIR):
        if not (file.startswith("graph_") and file.endswith(".gpickle")):
            continue

        period = file.replace("graph_", "").replace(".gpickle", "")
        print(f"\n=== Description communautés période {period} ===")

        with open(os.path.join(GRAPHS_DIR, file), "rb") as f:
            G = pickle.load(f)

        # LCC
        largest_cc = max(nx.connected_components(G), key=len)
        G_lcc = G.subgraph(largest_cc)

        partition = community_louvain.best_partition(G_lcc)

        # communauté -> acteurs
        comm_actors = defaultdict(list)
        for actor, comm_id in partition.items():
            comm_actors[comm_id].append(actor)

        for comm_id, actors in comm_actors.items():
            # Films liés à la communauté
            films = []
            genres = []

            for movie_id, cast in movie_cast.items():
                # Si au moins un acteur du film est dans la communauté
                if any(actor in actors for actor in cast):
                    films.append(movie_id)
                    genres.extend(movie_genres.get(movie_id, []))

            top_genres = Counter(genres).most_common(3)

            rows.append({
                "period": period,
                "community_id": comm_id,
                "nb_actors": len(actors),
                "nb_films": len(set(films)),
                "top_genres": ", ".join([g for g, _ in top_genres]),
            })

    df = pd.DataFrame(rows)
    output_path = os.path.join(REPORTS_DIR, "community_description.csv")
    df.to_csv(output_path, index=False)

    print(f"\n✔ Description sauvegardée : {output_path}")


if __name__ == "__main__":
    describe_communities()
