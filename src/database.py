from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CSV_FILE = DATA_DIR / "healthcare_appointment_no_show_wait_time.csv"


@st.cache_data(show_spinner=False)
def load_raw_data(csv_path: str | Path = DEFAULT_CSV_FILE) -> pd.DataFrame:
    file_path = Path(csv_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de dados nao encontrado em: {file_path}")

    return pd.read_csv(file_path)
