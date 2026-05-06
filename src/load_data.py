import pandas as pd
import json
from src.paths import MOVIES_CSV, CREDITS_CSV


def load_movies():
    """
    Charge le CSV des films et parse les colonnes JSON utiles.
    """
    movies = pd.read_csv(MOVIES_CSV)

    # Conversion release_date → année
    movies["release_date"] = pd.to_datetime(
        movies["release_date"], errors="coerce"
    )
    movies["release_year"] = movies["release_date"].dt.year

    # Parse genres (JSON)
    movies["genres_parsed"] = movies["genres"].apply(parse_json_names)
    
    # Parse pays de production (JSON)
    movies["production_countries_parsed"] = movies["production_countries"].apply(parse_json_names)

    return movies


def load_credits():
    """
    Charge le CSV des crédits et parse le casting.
    """
    credits = pd.read_csv(CREDITS_CSV)

    # Parse cast (JSON)
    credits["cast_parsed"] = credits["cast"].apply(parse_json_names)

    return credits


def parse_json_names(json_str):
    """
    Transforme une chaîne JSON du type :
    '[{"id": 28, "name": "Action"}, ...]'
    en liste de noms :
    ['Action', ...]
    """
    if pd.isna(json_str):
        return []

    try:
        data = json.loads(json_str)
        return [elem["name"] for elem in data if "name" in elem]
    except Exception:
        return []


def load_all():
    """
    Charge films + crédits et les retourne.
    """
    movies = load_movies()
    credits = load_credits()
    return movies, credits


if __name__ == "__main__":
    # Test rapide
    movies, credits = load_all()
    print("Films :", movies.shape)
    print("Crédits :", credits.shape)
    print("Exemple genres :", movies.iloc[0]["genres_parsed"])
    print("Exemple cast :", credits.iloc[0]["cast_parsed"][:5])
