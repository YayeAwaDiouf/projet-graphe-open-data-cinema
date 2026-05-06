import os
import pickle
from itertools import combinations
from collections import defaultdict

import pandas as pd
import networkx as nx
from tqdm import tqdm
from pyvis.network import Network

from src.load_data import load_credits
from src.paths import PROCESSED_DATA_DIR, GRAPHS_DIR, WEB_DIR


def build_actor_graph(movies_period_df, credits_df):
    """
    Construit un graphe acteurs-acteurs pour une période donnée.

    Nœud = acteur
    Arête = deux acteurs ont joué dans le même film
    Poids = nombre de films joués ensemble
    """
    G = nx.Graph()

    credits_map = dict(
        zip(credits_df["movie_id"], credits_df["cast_parsed"])
    )

    for _, row in tqdm(
        movies_period_df.iterrows(),
        total=len(movies_period_df),
        desc="Construction du graphe"
    ):
        movie_id = row["id"]
        movie_title = row["title"]
        cast = credits_map.get(movie_id, [])

        # Ajouter les acteurs comme nœuds
        for actor in cast:
            if not G.has_node(actor):
                G.add_node(actor)

        # Ajouter les liens entre acteurs du même film
        for a1, a2 in combinations(cast, 2):
            if G.has_edge(a1, a2):
                G[a1][a2]["weight"] += 1
                G[a1][a2]["movies"].append(movie_title)
            else:
                G.add_edge(a1, a2, weight=1, movies=[movie_title])

    return G


def inject_legend_into_html(html_path):
    """
    Ajoute une légende propre dans le HTML PyVis.
    """
    legend_html = """
    <div style="
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 410px;
        background: rgba(255, 255, 255, 0.95);
        color: black;
        border: 2px solid #555;
        padding: 14px;
        z-index: 9999;
        font-size: 13px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.35);
        line-height: 1.4;
        font-family: Arial, sans-serif;
    ">
        <h3 style="margin-top:0; margin-bottom:8px;">Lecture du graphe</h3>

        <p><b>Nœud</b> : représente un acteur.</p>
        <p><b>Lien</b> : deux acteurs ont joué ensemble dans au moins un film.</p>
        <p><b>Taille du nœud</b> : dépend du degré de l’acteur.</p>
        <p><b>Épaisseur du lien</b> : nombre de films joués en commun.</p>

        <hr>

        <p><b>Degré</b> : nombre d’acteurs différents avec lesquels un acteur a joué dans la période.</p>
        <p><b>Films visibles</b> : films de la période présents dans le sous-graphe affiché.</p>

        <hr>

        <p><b>Astuce</b> : survolez un acteur ou un lien pour afficher les détails.</p>
        <p style="font-size:12px;">
            Le graphe complet étant très grand, seuls les acteurs les plus connectés sont affichés
            afin de garder une visualisation lisible.
        </p>
    </div>
    """

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("</body>", legend_html + "\n</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def export_graph_visible_files(G, period_label, preview_top_n=150):
    """
    Exporte le graphe dans des formats visibles par l'utilisateur :
    - GraphML pour Gephi
    - CSV des nœuds
    - CSV des arêtes
    - HTML interactif PyVis
    """
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    os.makedirs(WEB_DIR, exist_ok=True)

    # =========================
    # 1. Export GraphML
    # =========================
    graphml_path = os.path.join(GRAPHS_DIR, f"graph_{period_label}.graphml")

    # GraphML n'accepte pas les listes Python directement
    G_graphml = G.copy()
    for u, v, data in G_graphml.edges(data=True):
        if "movies" in data:
            data["movies"] = " | ".join(data["movies"])

    nx.write_graphml(G_graphml, graphml_path)
    print(f"✔ GraphML visible sauvegardé : {graphml_path}")

    # =========================
    # 2. Export CSV nœuds
    # =========================
    nodes_rows = []

    for node in G.nodes():
        nodes_rows.append({
            "actor": node,
            "degree": G.degree(node)
        })

    nodes_df = pd.DataFrame(nodes_rows)
    nodes_path = os.path.join(GRAPHS_DIR, f"nodes_{period_label}.csv")
    nodes_df.to_csv(nodes_path, index=False, encoding="utf-8")
    print(f"✔ CSV nœuds sauvegardé : {nodes_path}")

    # =========================
    # 3. Export CSV arêtes
    # =========================
    edges_rows = []

    for u, v, data in G.edges(data=True):
        edges_rows.append({
            "actor_1": u,
            "actor_2": v,
            "weight": data.get("weight", 1),
            "movies_common": " | ".join(data.get("movies", []))
        })

    edges_df = pd.DataFrame(edges_rows)
    edges_path = os.path.join(GRAPHS_DIR, f"edges_{period_label}.csv")
    edges_df.to_csv(edges_path, index=False, encoding="utf-8")
    print(f"✔ CSV arêtes sauvegardé : {edges_path}")

    # =========================
    # 4. Export HTML interactif PyVis
    # =========================
    # Si preview_top_n = 0, on ne génère pas le HTML preview.
    if preview_top_n == 0:
        print("ℹ HTML preview non généré car preview_top_n = 0")
        return

    html_path = os.path.join(WEB_DIR, f"preview_graph_{period_label}.html")

    top_nodes = sorted(
        G.degree(),
        key=lambda x: x[1],
        reverse=True
    )[:preview_top_n]

    selected_nodes = [n for n, _ in top_nodes]
    G_sub = G.subgraph(selected_nodes).copy()

    # Préparer les films visibles par acteur dans le sous-graphe
    actor_movies_visible = defaultdict(list)
    actor_collaborators_visible = defaultdict(set)

    for u, v, data in G_sub.edges(data=True):
        movies = data.get("movies", [])

        actor_movies_visible[u].extend(movies)
        actor_movies_visible[v].extend(movies)

        actor_collaborators_visible[u].add(v)
        actor_collaborators_visible[v].add(u)

    net = Network(
    height="750px",
    width="100%",
    bgcolor="#111111",
    font_color="white",
    notebook=False,
    directed=False
    )

    # Physique activée : les nœuds restent mobiles/vivants
    net.barnes_hut(
        gravity=-20000,
        central_gravity=0.2,
        spring_length=180,
        spring_strength=0.03,
        damping=0.08,
        overlap=0
    )

    net.set_options("""
    {
    "physics": {
        "enabled": true,
        "stabilization": {
        "enabled": false
        },
        "barnesHut": {
        "gravitationalConstant": -20000,
        "centralGravity": 0.2,
        "springLength": 180,
        "springConstant": 0.03,
        "damping": 0.08,
        "avoidOverlap": 0
        }
    },
    "interaction": {
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "hover": true
    }
    }
    """)

    # Ajouter les nœuds
    for node in G_sub.nodes():
        degree_total = G.degree(node)
        degree_visible = G_sub.degree(node)
        collaborators_visible = len(actor_collaborators_visible.get(node, []))

        films = list(dict.fromkeys(actor_movies_visible.get(node, [])))[:12]
        #films_html = "<br>".join([f"- {film}" for film in films]) if films else "Aucun film visible"

        films_text = "\n".join([f"- {film}" for film in films]) if films else "Aucun film visible"

        title_html = (
            f"Acteur : {node}\n"
            f"Période : {period_label}\n\n"
            f"Degré total période : {degree_total}\n"
            f"Nombre d’acteurs différents avec lesquels cet acteur a joué dans toute la période.\n\n"
            f"Degré visible dans ce graphe : {degree_visible}\n"
            f"Nombre de liens avec les acteurs affichés dans cette visualisation.\n\n"
            f"Collaborateurs visibles : {collaborators_visible}\n\n"
            f"Films visibles dans ce sous-graphe :\n"
            f"{films_text}"
        )

        net.add_node(
            node,
            label=node,
            title=title_html,
            size=8 + degree_total * 0.05
        )

    # Ajouter les arêtes
    for u, v, data in G_sub.edges(data=True):
        movies = data.get("movies", [])
        movies_unique = list(dict.fromkeys(movies))

        movies_text = "\n".join(
            [f"- {film}" for film in movies_unique[:12]]
        ) if movies_unique else "Non renseigné"

        title_html = (
            f"Lien : {u} ↔ {v}\n"
            f"Nombre de films en commun : {data.get('weight', 1)}\n\n"
            f"Films en commun :\n"
            f"{movies_text}"
        )

        net.add_edge(
            u,
            v,
            value=data.get("weight", 1),
            width=max(1, min(8, data.get("weight", 1))),
            title=title_html
        )

    net.write_html(html_path)

    # Ajouter la légende après génération du HTML PyVis
    inject_legend_into_html(html_path)

    print(f"✔ HTML interactif sauvegardé : {html_path}")


def build_graphs_by_period(preview_top_n=150):
    """
    Construit et sauvegarde un graphe par période,
    avec exports visibles pour l'utilisateur.
    """
    os.makedirs(GRAPHS_DIR, exist_ok=True)

    credits = load_credits()

    for file in os.listdir(PROCESSED_DATA_DIR):
        if not file.startswith("movies_"):
            continue

        period_label = file.replace("movies_", "").replace(".csv", "")
        print(f"\n=== Construction graphe période {period_label} ===")

        movies_period = pd.read_csv(
            os.path.join(PROCESSED_DATA_DIR, file)
        )

        G = build_actor_graph(movies_period, credits)

        print(
            f"Graphe {period_label} : "
            f"{G.number_of_nodes()} nœuds, "
            f"{G.number_of_edges()} arêtes"
        )

        # =========================
        # Sauvegarde interne Python
        # =========================
        gpickle_path = os.path.join(
            GRAPHS_DIR, f"graph_{period_label}.gpickle"
        )

        with open(gpickle_path, "wb") as f:
            pickle.dump(G, f)

        print(f"✔ GPickle sauvegardé : {gpickle_path}")

        # =========================
        # Exports visibles utilisateur
        # =========================
        export_graph_visible_files(G, period_label, preview_top_n=preview_top_n)


if __name__ == "__main__":
    build_graphs_by_period()