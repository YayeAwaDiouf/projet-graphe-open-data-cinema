import os
import pickle
import math
from collections import Counter, defaultdict

import folium  # type: ignore
import networkx as nx
import community as community_louvain

from src.paths import GRAPHS_DIR, WEB_DIR
from src.load_data import load_all


# Coordonnées approximatives des pays les plus fréquents dans TMDB
COUNTRY_COORDS = {
    "United States of America": (37.0902, -95.7129),
    "United Kingdom": (55.3781, -3.4360),
    "France": (46.2276, 2.2137),
    "Germany": (51.1657, 10.4515),
    "Canada": (56.1304, -106.3468),
    "India": (20.5937, 78.9629),
    "Japan": (36.2048, 138.2529),
    "China": (35.8617, 104.1954),
    "Australia": (-25.2744, 133.7751),
    "Italy": (41.8719, 12.5674),
    "Spain": (40.4637, -3.7492),
    "South Korea": (35.9078, 127.7669),
    "Hong Kong": (22.3193, 114.1694),
    "Mexico": (23.6345, -102.5528),
    "Ireland": (53.4129, -8.2439),
    "Russia": (61.5240, 105.3188),
    "Brazil": (-14.2350, -51.9253),
    "New Zealand": (-40.9006, 174.8860),
    "Belgium": (50.5039, 4.4699),
    "Sweden": (60.1282, 18.6435),
    "Denmark": (56.2639, 9.5018),
    "Norway": (60.4720, 8.4689),
    "Netherlands": (52.1326, 5.2913),
}


COLORS = [
    "red", "blue", "green", "purple", "orange",
    "darkred", "lightred", "beige", "darkblue",
    "darkgreen", "cadetblue", "darkpurple",
    "pink", "lightblue", "lightgreen", "gray",
    "black", "lightgray"
]


def clean_html_list(items, max_items=10):
    """
    Transforme une liste Python en liste HTML courte.
    """
    if not items:
        return "Aucun"

    items = list(dict.fromkeys(items))[:max_items]
    return "<br>".join([f"- {item}" for item in items])


def jitter_position(base_lat, base_lon, index, total, radius=8):
    """
    Décale les acteurs autour du pays pour éviter qu'ils soient tous superposés.
    """
    if total <= 1:
        return base_lat, base_lon

    angle = 2 * math.pi * index / total
    ring = 1 + (index % 5) * 0.25

    lat = base_lat + math.sin(angle) * radius * ring
    lon = base_lon + math.cos(angle) * radius * ring

    return lat, lon


def build_world_map(period="2000_2009", top_n=150, max_edges=250):
    """
    Génère une carte du monde interactive.

    Les acteurs sont positionnés selon le pays de production dominant
    des films dans lesquels ils apparaissent sur la période choisie.

    Les couleurs représentent les communautés Louvain.
    """

    period = period.strip().replace("-", "_")
    graph_path = os.path.join(GRAPHS_DIR, f"graph_{period}.gpickle")

    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graphe introuvable : {graph_path}")

    print(f"\n=== Carte monde période {period} ===")

    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    movies, credits = load_all()

    print("Graphe chargé :", G.number_of_nodes(), "nœuds,", G.number_of_edges(), "arêtes")

    # Plus grande composante connexe
    largest_cc = max(nx.connected_components(G), key=len)
    G_lcc = G.subgraph(largest_cc).copy()

    # Louvain
    print("Calcul des communautés Louvain...")
    partition = community_louvain.best_partition(G_lcc)

    # Top acteurs par degré
    top_nodes = sorted(
        G_lcc.degree(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    actors = [actor for actor, _ in top_nodes]
    G_sub = G_lcc.subgraph(actors).copy()

    print("Sous-graphe affiché :", G_sub.number_of_nodes(), "acteurs,", G_sub.number_of_edges(), "liens")

    # movie_id -> infos film
    movie_info = {}

    for _, row in movies.iterrows():
        movie_id = row["id"]
        movie_info[movie_id] = {
            "title": row["title"],
            "year": row["release_year"],
            "genres": row["genres_parsed"],
            "countries": row["production_countries_parsed"],
        }

    actor_movies = defaultdict(list)
    actor_genres = defaultdict(list)
    actor_countries = defaultdict(list)

    start, end = map(int, period.split("_"))

    # Associer acteurs -> films, genres, pays
    for _, row in credits.iterrows():
        movie_id = row["movie_id"]
        cast = row["cast_parsed"]

        if movie_id not in movie_info:
            continue

        info = movie_info[movie_id]
        year = info["year"]

        if not (start <= year <= end):
            continue

        for actor in cast:
            if actor in actors:
                actor_movies[actor].append(info["title"])
                actor_genres[actor].extend(info["genres"])
                actor_countries[actor].extend(info["countries"])

    # Pays dominant de chaque acteur
    actor_main_country = {}

    for actor in actors:
        countries = actor_countries.get(actor, [])

        if countries:
            main_country = Counter(countries).most_common(1)[0][0]
        else:
            main_country = "United States of America"

        if main_country not in COUNTRY_COORDS:
            main_country = "United States of America"

        actor_main_country[actor] = main_country

    # Regrouper acteurs par pays pour les décaler autour du pays
    country_to_actors = defaultdict(list)

    for actor in actors:
        country_to_actors[actor_main_country[actor]].append(actor)

    actor_position = {}

    for country, actor_list in country_to_actors.items():
        base_lat, base_lon = COUNTRY_COORDS[country]
        total = len(actor_list)

        for idx, actor in enumerate(actor_list):
            actor_position[actor] = jitter_position(base_lat, base_lon, idx, total)

    # Description textuelle des communautés
    community_genres = defaultdict(list)
    community_countries = defaultdict(list)

    for actor in actors:
        comm_id = partition.get(actor, -1)
        community_genres[comm_id].extend(actor_genres.get(actor, []))
        community_countries[comm_id].extend(actor_countries.get(actor, []))

    community_label = {}

    for comm_id in set(partition.get(actor, -1) for actor in actors):
        top_genres = [g for g, _ in Counter(community_genres[comm_id]).most_common(3)]
        top_countries = [c for c, _ in Counter(community_countries[comm_id]).most_common(2)]

        if top_genres:
            label = " / ".join(top_genres)
        else:
            label = "Non caractérisée"

        if top_countries:
            label += " — " + " / ".join(top_countries)

        community_label[comm_id] = label

    # Création de la carte
    m = folium.Map(
        location=[25, -20],
        zoom_start=2,
        tiles="CartoDB dark_matter"
    )

    # Légende
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        width: 380px;
        background-color: white;
        z-index: 9999;
        font-size: 13px;
        padding: 10px;
        border: 2px solid grey;
        color: black;
    ">
    <b>Lecture de la carte</b><br>
    - Un point = un acteur<br>
    - Couleur = communauté Louvain<br>
    - Taille = degré total de l'acteur dans la période<br>
    - Position = pays dominant des films de l'acteur<br>
    - Lien jaune = collaboration affichée sur la carte<br><br>
    <b>Attention :</b><br>
    La carte n'affiche qu'un sous-graphe pour rester lisible.
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # --------------------------------------------------
    # Préparer les degrés et les liens réellement affichés
    # --------------------------------------------------

    # Degré total dans toute la période
    degree_total_dict = dict(G_lcc.degree())

    # Degré dans le sous-graphe Top N
    degree_subgraph_dict = dict(G_sub.degree())

    # Liens du sous-graphe triés par poids
    edges_sorted = sorted(
        G_sub.edges(data=True),
        key=lambda x: x[2].get("weight", 1),
        reverse=True
    )

    # Liens réellement affichés sur la carte
    #displayed_edges = edges_sorted[:max_edges]
    # On affiche tous les liens du sous-graphe.
    # Le sous-graphe reste contrôlé grâce au paramètre top_n.
    displayed_edges = edges_sorted

    # Calcul du nombre de liens réellement dessinés pour chaque acteur
    displayed_degree = defaultdict(int)

    for a1, a2, data in displayed_edges:
        displayed_degree[a1] += 1
        displayed_degree[a2] += 1

    # --------------------------------------------------
    # Ajouter les acteurs
    # --------------------------------------------------
    for actor in actors:
        lat, lon = actor_position[actor]

        degree_total = degree_total_dict.get(actor, 0)
        degree_subgraph = degree_subgraph_dict.get(actor, 0)
        degree_displayed = displayed_degree.get(actor, 0)

        comm_id = partition.get(actor, -1)
        comm_desc = community_label.get(comm_id, "Non caractérisée")

        films = actor_movies.get(actor, [])
        genres = [g for g, _ in Counter(actor_genres.get(actor, [])).most_common(5)]

        popup_html = f"""
        <b>Acteur :</b> {actor}<br>
        <b>Communauté :</b> {comm_id} — {comm_desc}<br><br>

        <b>Degré total période :</b> {degree_total}<br>
        <i>Nombre d'acteurs différents avec lesquels cet acteur a joué dans toute la période.</i><br><br>

        <b>Degré dans le sous-graphe :</b> {degree_subgraph}<br>
        <i>Nombre de liens avec les acteurs sélectionnés dans le Top N.</i><br><br>

        <b>Liens réellement affichés :</b> {degree_displayed}<br>
        <i>Nombre de liens effectivement dessinés sur cette carte après limitation graphique.</i><br><br>

        <b>Pays dominant :</b> {actor_main_country.get(actor, "Inconnu")}<br>
        <b>Genres dominants :</b><br>{clean_html_list(genres, 5)}<br><br>

        <b>Films dans la période :</b><br>{clean_html_list(films, 12)}
        """

        color = COLORS[comm_id % len(COLORS)]

        # Contour blanc si aucun lien n’est effectivement affiché
        border_color = "white" if degree_displayed == 0 else color

        folium.CircleMarker(
            location=[lat, lon],
            radius=max(5, min(16, 4 + degree_total / 20)),
            popup=folium.Popup(popup_html, max_width=450),
            tooltip=actor,
            color=border_color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2
        ).add_to(m)

    # --------------------------------------------------
    # Ajouter uniquement les liens réellement sélectionnés
    # --------------------------------------------------
    for a1, a2, data in displayed_edges:
        pos1 = actor_position.get(a1)
        pos2 = actor_position.get(a2)

        if not pos1 or not pos2:
            continue

        common_movies = sorted(
            set(actor_movies.get(a1, [])) & set(actor_movies.get(a2, []))
        )

        popup_html = f"""
        <b>Lien :</b> {a1} ↔ {a2}<br>
        <b>Nombre de films en commun :</b> {len(common_movies)}<br>
        <b>Films en commun :</b><br>{clean_html_list(common_movies, 8)}
        """

        folium.PolyLine(
            locations=[pos1, pos2],
            weight=max(2, min(7, data.get("weight", 1))),
            color="yellow",
            opacity=0.65,
            popup=folium.Popup(popup_html, max_width=450)
        ).add_to(m)

    os.makedirs(WEB_DIR, exist_ok=True)

    output_path = os.path.join(WEB_DIR, f"world_map_{period}.html")
    m.save(output_path)

    print(f"✔ Carte monde générée : {output_path}")
    return output_path


def build_all_world_maps():
    periods = ["1990_1999", "2000_2009", "2010_2019"]

    for period in periods:
        build_world_map(period=period, top_n=150, max_edges=250)


if __name__ == "__main__":
    build_all_world_maps()