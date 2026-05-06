import os
import pandas as pd
from src.load_data import load_all
from src.paths import PROCESSED_DATA_DIR


# Définition des périodes (décennies)
PERIODS = {
    "1990_1999": (1990, 1999),
    "2000_2009": (2000, 2009),
    "2010_2019": (2010, 2019),
}


def filter_movies_by_period(movies, start_year, end_year):
    """
    Filtre les films entre start_year et end_year inclus.
    """
    return movies[
        (movies["release_year"] >= start_year)
        & (movies["release_year"] <= end_year)
    ]


def preprocess_by_period():
    """
    Charge les données et sauvegarde un CSV par période.
    """
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    movies, credits = load_all()

    for label, (start, end) in PERIODS.items():
        movies_period = filter_movies_by_period(movies, start, end)

        output_path = os.path.join(
            PROCESSED_DATA_DIR, f"movies_{label}.csv"
        )

        movies_period.to_csv(output_path, index=False)

        print(
            f"Période {label} : {len(movies_period)} films sauvegardés"
        )


if __name__ == "__main__":
    preprocess_by_period()
