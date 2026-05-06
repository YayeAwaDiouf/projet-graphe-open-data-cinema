import os

# Racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Dossiers data
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Dossiers outputs
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
GRAPHS_DIR = os.path.join(OUTPUTS_DIR, "graphs")
VISUALS_DIR = os.path.join(OUTPUTS_DIR, "visuals")
REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
WEB_DIR = os.path.join(OUTPUTS_DIR, "web")

# Fichiers CSV Kaggle
MOVIES_CSV = os.path.join(RAW_DATA_DIR, "tmdb_5000_movies.csv")
CREDITS_CSV = os.path.join(RAW_DATA_DIR, "tmdb_5000_credits.csv")
