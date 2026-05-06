import os
import pandas as pd

from src.paths import REPORTS_DIR
from src.load_data import load_all


def normalize_period(period):
    """
    Accepte 1990-1999 ou 1990_1999 et retourne 1990_1999.
    """
    if period is None or period == "":
        return None

    return period.strip().replace("-", "_")


def normalize_genre(genre):
    """
    Transforme action -> Action, drama -> Drama, etc.
    """
    return genre.strip().title()


def load_movie_community_check():
    path = os.path.join(REPORTS_DIR, "movie_community_check.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(
            "Le fichier movie_community_check.csv est introuvable. "
            "Lance d'abord : py -3.12 -m src.film_community_check"
        )

    return pd.read_csv(path)


def prepare_movies_with_communities():
    """
    Fusionne les films TMDB avec les résultats communautés.
    """
    movies, credits = load_all()
    check = load_movie_community_check()

    df = movies.merge(
        check,
        left_on="id",
        right_on="movie_id",
        how="inner",
        suffixes=("_movie", "_check")
    )

    return df, movies, credits


def safe_sort(df, columns):
    """
    Trie seulement avec les colonnes qui existent réellement.
    """
    existing_cols = [col for col in columns if col in df.columns]

    if existing_cols:
        return df.sort_values(by=existing_cols, ascending=False)

    return df


def keep_existing_columns(df, columns):
    """
    Retourne seulement les colonnes qui existent pour éviter les KeyError.
    """
    return df[[col for col in columns if col in df.columns]]


def recommend_by_genre(genre, period=None, top_n=10):
    """
    Recommande des films selon un genre.
    Optionnel : filtrer par période.
    """
    genre = normalize_genre(genre)
    period = normalize_period(period)

    df, movies, credits = prepare_movies_with_communities()

    if period:
        df = df[df["period"] == period]

    df = df[
        df["genres_parsed"].apply(
            lambda genres: genre in genres if isinstance(genres, list) else False
        )
    ]

    df = safe_sort(
        df,
        ["vote_average_movie", "vote_average", "popularity_movie", "popularity"]
    )

    return keep_existing_columns(
        df,
        [
            "title_movie",
            "release_year_movie",
            "release_year",
            "genres_parsed",
            "vote_average_movie",
            "vote_average",
            "popularity_movie",
            "popularity",
            "period"
        ]
    ).head(top_n)


def recommend_by_actor(actor_name, top_n=10):
    """
    Recommande les films où apparaît un acteur donné.
    """
    movies, credits = load_all()

    merged = movies.merge(
        credits,
        left_on="id",
        right_on="movie_id",
        how="inner",
        suffixes=("_movie", "_credits")
    )

    actor_name = actor_name.strip()

    df = merged[
        merged["cast_parsed"].apply(
            lambda cast: actor_name in cast if isinstance(cast, list) else False
        )
    ]

    df = safe_sort(
        df,
        ["vote_average", "popularity"]
    )

    return keep_existing_columns(
        df,
        [
            "title_movie",
            "title",
            "release_year",
            "genres_parsed",
            "vote_average",
            "popularity"
        ]
    ).head(top_n)


def recommend_by_community(community_id, period=None, top_n=10):
    """
    Recommande des films associés à une communauté dominante.
    """
    period = normalize_period(period)

    df, movies, credits = prepare_movies_with_communities()

    df = df[df["dominant_community"] == int(community_id)]

    if period:
        df = df[df["period"] == period]

    df = safe_sort(
        df,
        [
            "dominant_community_share",
            "vote_average_movie",
            "vote_average",
            "popularity_movie",
            "popularity"
        ]
    )

    return keep_existing_columns(
        df,
        [
            "title_movie",
            "release_year_movie",
            "release_year",
            "genres_parsed",
            "vote_average_movie",
            "vote_average",
            "popularity_movie",
            "popularity",
            "period",
            "dominant_community",
            "dominant_community_share"
        ]
    ).head(top_n)


def save_recommendations_examples():
    """
    Génère quelques exemples de recommandations pour le rapport.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)

    rec_action = recommend_by_genre("Action", period="2000_2009", top_n=10)
    rec_action.to_csv(
        os.path.join(REPORTS_DIR, "recommend_action_2000_2009.csv"),
        index=False
    )

    rec_drama = recommend_by_genre("Drama", period="2010_2019", top_n=10)
    rec_drama.to_csv(
        os.path.join(REPORTS_DIR, "recommend_drama_2010_2019.csv"),
        index=False
    )

    print("✔ Recommandations générées :")
    print("-", os.path.join(REPORTS_DIR, "recommend_action_2000_2009.csv"))
    print("-", os.path.join(REPORTS_DIR, "recommend_drama_2010_2019.csv"))


if __name__ == "__main__":
    save_recommendations_examples()

    print("\n--- Exemple recommandation acteur : Tom Hanks ---")
    print(recommend_by_actor("Tom Hanks", top_n=5))

    print("\n--- Exemple recommandation genre : Action, période 2000_2009 ---")
    print(recommend_by_genre("Action", period="2000_2009", top_n=5))