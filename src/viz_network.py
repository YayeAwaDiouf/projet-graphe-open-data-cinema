import os
import pickle
from collections import Counter

import networkx as nx
import community as community_louvain
from pyvis.network import Network

from src.paths import GRAPHS_DIR, WEB_DIR


def build_interactive_map_for_period(period, top_n=300):
    """
    Génère une carte HTML interactive du réseau d'acteurs
    pour une période donnée.

    - Les nœuds représentent les acteurs.
    - Les liens représentent les collaborations.
    - Les couleurs représentent les communautés Louvain.
    """

    graph_path = os.path.join(GRAPHS_DIR, f"graph_{period}.gpickle")

    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graphe introuvable : {graph_path}")

    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    print(f"\n=== Carte interactive période {period} ===")
    print("Graphe chargé :", G.number_of_nodes(), "nœuds,", G.number_of_edges(), "arêtes")

    # Plus grande composante connexe
    largest_cc = max(nx.connected_components(G), key=len)
    G_lcc = G.subgraph(largest_cc).copy()

    # Louvain sur la LCC
    print("Détection des communautés Louvain...")
    partition = community_louvain.best_partition(G_lcc)

    # Sous-graphe des acteurs les plus connectés
    top_nodes = sorted(
        G_lcc.degree(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    nodes_subset = [n for n, _ in top_nodes]
    G_sub = G_lcc.subgraph(nodes_subset).copy()

    print("Sous-graphe :", G_sub.number_of_nodes(), "nœuds,", G_sub.number_of_edges(), "arêtes")

    # Créer la carte PyVis
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#111111",
        font_color="white",
        notebook=False
    )

    net.barnes_hut(
        gravity=-30000,
        central_gravity=0.3,
        spring_length=130,
        spring_strength=0.02,
        damping=0.09,
        overlap=0
    )

    # Palette simple
    colors = [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
        "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
        "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000",
        "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080"
    ]

    degree_dict = dict(G_sub.degree())

    # Ajouter les nœuds
    for node in G_sub.nodes():
        comm_id = partition.get(node, -1)
        color = colors[comm_id % len(colors)]

        net.add_node(
            node,
            label=node,
            title=(
                f"Acteur : {node}<br>"
                f"Communauté : {comm_id}<br>"
                f"Degré : {degree_dict.get(node, 0)}"
            ),
            color=color,
            size=8 + degree_dict.get(node, 0) * 0.08
        )

    # Ajouter les arêtes
    for source, target, data in G_sub.edges(data=True):
        weight = data.get("weight", 1)

        net.add_edge(
            source,
            target,
            value=weight,
            title=f"Films en commun : {weight}"
        )

    os.makedirs(WEB_DIR, exist_ok=True)

    output_path = os.path.join(WEB_DIR, f"network_map_{period}.html")
    net.write_html(output_path)

    print(f"✔ Carte interactive générée : {output_path}")
    return output_path


def build_all_interactive_maps():
    """
    Génère les cartes interactives pour toutes les périodes disponibles.
    """
    periods = []

    for file in os.listdir(GRAPHS_DIR):
        if file.startswith("graph_") and file.endswith(".gpickle"):
            period = file.replace("graph_", "").replace(".gpickle", "")
            periods.append(period)

    periods.sort()

    for period in periods:
        build_interactive_map_for_period(period, top_n=300)


if __name__ == "__main__":
    build_all_interactive_maps()