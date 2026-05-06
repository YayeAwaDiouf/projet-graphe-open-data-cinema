import os
import pandas as pd
import matplotlib.pyplot as plt

from src.paths import REPORTS_DIR


def extract_main_genre(top_genres_value):
    """
    Extrait le genre principal d'une chaîne du type :
    'Drama / Comedy / Action'
    -> 'Drama'
    """
    if pd.isna(top_genres_value):
        return "Inconnu"

    text = str(top_genres_value).strip()

    if text == "":
        return "Inconnu"

    # On prend le premier genre dominant
    return text.split("/")[0].strip()


def compare_communities_by_genre():
    """
    Compare les communautés par genre dominant.

    Source :
    - outputs/reports/community_description.csv

    Génère :
    - outputs/reports/community_genre_comparison.csv
    - outputs/visuals/community_genre_comparison_histogram.png
    """
    input_path = os.path.join(REPORTS_DIR, "community_description.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            "Le fichier community_description.csv est introuvable.\n"
            "Lance d'abord l'option 4 : Décrire les communautés."
        )

    # Dossier visuals déduit automatiquement
    outputs_dir = os.path.dirname(REPORTS_DIR)
    visuals_dir = os.path.join(outputs_dir, "visuals")
    os.makedirs(visuals_dir, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    df = pd.read_csv(input_path)

    # Vérification des colonnes minimales
    required_cols = ["period", "community_id", "top_genres"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(
            f"Colonnes manquantes dans community_description.csv : {missing_cols}"
        )

    # Extraire le genre principal de chaque communauté
    df["main_genre"] = df["top_genres"].apply(extract_main_genre)

    # Tableau de comparaison : combien de communautés par genre principal et par période
    comparison = (
        df.groupby(["period", "main_genre"])
        .size()
        .reset_index(name="nb_communities")
        .sort_values(["period", "nb_communities"], ascending=[True, False])
    )

    # Sauvegarde CSV
    csv_output_path = os.path.join(REPORTS_DIR, "community_genre_comparison.csv")
    comparison.to_csv(csv_output_path, index=False, encoding="utf-8")

    # Préparer les données pour l'histogramme
    pivot = comparison.pivot(
        index="main_genre",
        columns="period",
        values="nb_communities"
    ).fillna(0)

    # Garder les genres les plus représentés pour un visuel plus lisible
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False).head(10)
    pivot = pivot.drop(columns=["total"])

    # Histogramme
    plt.figure(figsize=(12, 7))
    ax = pivot.plot(kind="bar", figsize=(12, 7))

    ax.set_title("Comparaison des communautés par genre dominant")
    ax.set_xlabel("Genre dominant")
    ax.set_ylabel("Nombre de communautés")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    png_output_path = os.path.join(
        visuals_dir,
        "community_genre_comparison_histogram.png"
    )
    plt.savefig(png_output_path, dpi=300, bbox_inches="tight")
    plt.close()

    # Affichage console
    print("\n✔ Comparaison des communautés par genre terminée.")
    print(f"✔ CSV généré : {csv_output_path}")
    print(f"✔ Histogramme généré : {png_output_path}")
    print("\nTu peux les voir ici :")
    print(f"- CSV : {csv_output_path}")
    print(f"- Histogramme : {png_output_path}")

    return comparison


if __name__ == "__main__":
    compare_communities_by_genre()