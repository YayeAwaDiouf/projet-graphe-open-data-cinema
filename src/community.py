import os
import pickle
from collections import Counter

import networkx as nx
import pandas as pd
import community as community_louvain

from src.paths import GRAPHS_DIR, REPORTS_DIR


def analyze_communities_for_graph(graph_path, label):
    """
    Applique Louvain sur un graphe et retourne des stats.
    """
    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    print(f"\n--- Louvain sur période {label} ---")
    print("Nœuds :", G.number_of_nodes())
    print("Arêtes :", G.number_of_edges())

    # Plus grande composante connexe
    largest_cc = max(nx.connected_components(G), key=len)
    G_lcc = G.subgraph(largest_cc)

    partition = community_louvain.best_partition(G_lcc)

    nb_communities = len(set(partition.values()))
    print("Nombre de communautés :", nb_communities)

    community_sizes = Counter(partition.values())

    # Sauvegarde stats
    rows = []
    for comm_id, size in community_sizes.most_common():
        rows.append({
            "period": label,
            "community_id": comm_id,
            "size": size
        })

    return rows


def run_community_analysis():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    all_rows = []

    for file in os.listdir(GRAPHS_DIR):
        if not (file.startswith("graph_") and file.endswith(".gpickle")):
            continue

        label = file.replace("graph_", "").replace(".gpickle", "")
        graph_path = os.path.join(GRAPHS_DIR, file)

        rows = analyze_communities_for_graph(graph_path, label)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    output_path = os.path.join(REPORTS_DIR, "community_sizes_by_period.csv")
    df.to_csv(output_path, index=False)

    print(f"\n✔ Statistiques sauvegardées : {output_path}")


if __name__ == "__main__":
    run_community_analysis()
