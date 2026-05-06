# Projet Graphes et Open Data — Réseau d’acteurs TMDB

## Présentation

Ce projet a été réalisé dans le cadre du module Graphes et Open Data.

L’objectif est d’exploiter le dataset open data TMDB 5000 Movie Dataset afin de construire et analyser un réseau d’acteurs de cinéma.

Dans ce projet :

- un nœud représente un acteur ;
- une arête relie deux acteurs lorsqu’ils ont joué ensemble dans au moins un film ;
- le poids d’une arête correspond au nombre de films joués en commun.

Le projet exploite également les années, les genres, les pays de production, les communautés d’acteurs et les films communs afin de proposer une analyse complète du réseau.

## Dataset utilisé

Dataset Kaggle :

https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata

Fichiers nécessaires :

```text
tmdb_5000_movies.csv
tmdb_5000_credits.csv
```

Les fichiers doivent être placés dans :

```text
data/raw/
```

## Version Python

Le projet a été développé et testé avec :

```text
Python 3.12
```

Sous Windows, utiliser :

```bat
py -3.12
```

## Installation

Depuis la racine du projet :

```bat
py -3.12 -m pip install -r requirements.txt
```

## Lancement du menu principal

Depuis la racine du projet :

```bat
py -3.12 -m src.cli_menu
```

Menu disponible :

```text
1 - Prétraiter les données par période
2 - Construire les graphes par période
3 - Détecter les communautés Louvain
4 - Décrire les communautés
5 - Comparer les communautés par genres
6 - Vérifier films / communautés
7 - Recommandation de films
8 - Générer la carte monde interactive
0 - Quitter
```

## Arborescence du projet

```text
projet_graphe_cinema/
│
├── data/
│   ├── raw/
│   │   ├── tmdb_5000_movies.csv
│   │   └── tmdb_5000_credits.csv
│   └── processed/
│
├── outputs/
│   ├── graphs/
│   ├── reports/
│   ├── visuals/
│   └── web/
│
├── src/
│   ├── paths.py
│   ├── load_data.py
│   ├── preprocess.py
│   ├── graph_build.py
│   ├── community.py
│   ├── community_desc.py
│   ├── queries.py
│   ├── film_community_check.py
│   ├── recommend.py
│   ├── viz_world_map.py
│   └── cli_menu.py
│
├── README.md
├── requirements.txt
└── note.txt
```

## Pipeline du projet

### 1. Prétraitement des données

```bat
py -3.12 -m src.preprocess
```

Fichiers générés :

```text
data/processed/movies_1990_1999.csv
data/processed/movies_2000_2009.csv
data/processed/movies_2010_2019.csv
```

### 2. Construction des graphes

```bat
py -3.12 -m src.graph_build
```

Fichiers générés :

```text
outputs/graphs/graph_1990_1999.gpickle
outputs/graphs/graph_2000_2009.gpickle
outputs/graphs/graph_2010_2019.gpickle

outputs/graphs/graph_1990_1999.graphml
outputs/graphs/graph_2000_2009.graphml
outputs/graphs/graph_2010_2019.graphml

outputs/graphs/nodes_1990_1999.csv
outputs/graphs/nodes_2000_2009.csv
outputs/graphs/nodes_2010_2019.csv

outputs/graphs/edges_1990_1999.csv
outputs/graphs/edges_2000_2009.csv
outputs/graphs/edges_2010_2019.csv

outputs/web/preview_graph_1990_1999.html
outputs/web/preview_graph_2000_2009.html
outputs/web/preview_graph_2010_2019.html
```

### 3. Détection des communautés

```bat
py -3.12 -m src.community
```

Fichier généré :

```text
outputs/reports/community_sizes_by_period.csv
```

### 4. Description des communautés

```bat
py -3.12 -m src.community_desc
```

Fichier généré :

```text
outputs/reports/community_description.csv
```

### 5. Comparaison des communautés par genres

```bat
py -3.12 -m src.queries
```

Fichiers générés :

```text
outputs/reports/community_genre_comparison.csv
outputs/visuals/community_genre_comparison_histogram.png
```

### 6. Vérification films / communautés

```bat
py -3.12 -m src.film_community_check
```

Fichier généré :

```text
outputs/reports/movie_community_check.csv
```

Résultat obtenu :

```text
Nombre de films analysés : 4089
Films cohérents avec une communauté : 2552
Films ponts / mixtes : 1537
```

### 7. Recommandation de films

```bat
py -3.12 -m src.recommend
```

Fichiers générés :

```text
outputs/reports/recommend_action_2000_2009.csv
outputs/reports/recommend_drama_2010_2019.csv
```

### 8. Carte monde interactive

```bat
py -3.12 -m src.viz_world_map
```

Fichiers générés :

```text
outputs/web/world_map_1990_1999.html
outputs/web/world_map_2000_2009.html
outputs/web/world_map_2010_2019.html
```

## Visualisations principales

Graphes interactifs :

```text
outputs/web/preview_graph_1990_1999.html
outputs/web/preview_graph_2000_2009.html
outputs/web/preview_graph_2010_2019.html
```

Cartes monde interactives :

```text
outputs/web/world_map_1990_1999.html
outputs/web/world_map_2000_2009.html
outputs/web/world_map_2010_2019.html
```

Histogramme :

```text
outputs/visuals/community_genre_comparison_histogram.png
```

## Auteure

DIOUF Yaye Awa  
DL - Informatique & Gestion  
Graphes et Open Data  
Année universitaire 2025-2026