import pandas as pd
import streamlit as st

from src.database import DEFAULT_CSV_FILE, load_raw_data


DEFAULT_CLINIC_NAME = "Clinica Central"
DEFAULT_CITY = "Sao Caetano do Sul"
DEFAULT_STATE = "SP"

DAY_NAME_MAP = {
    "Monday": "Segunda-feira",
    "Tuesday": "Terca-feira",
    "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira",
    "Saturday": "Sabado",
    "Sunday": "Domingo",
}

MONTH_NAME_MAP = {
    "January": "Janeiro",
    "February": "Fevereiro",
    "March": "Marco",
    "April": "Abril",
    "May": "Maio",
    "June": "Junho",
    "July": "Julho",
    "August": "Agosto",
    "September": "Setembro",
    "October": "Outubro",
    "November": "Novembro",
    "December": "Dezembro",
}

DAY_ORDER = [
    "Segunda-feira",
    "Terca-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sabado",
    "Domingo",
]

AGE_GROUP_ORDER = ["Criancas (0-18)", "Adultos (19-60)", "Idosos (61+)"]


def classify_age_group(age: int) -> str:
    if age <= 18:
        return "Criancas (0-18)"
    if age <= 60:
        return "Adultos (19-60)"
    return "Idosos (61+)"


def build_surrogate_dimension(df: pd.DataFrame, columns: list[str], sk_name: str) -> pd.DataFrame:
    dimension = (
        df[columns]
        .drop_duplicates()
        .sort_values(columns)
        .reset_index(drop=True)
        .copy()
    )
    dimension.insert(0, sk_name, range(1, len(dimension) + 1))
    return dimension


@st.cache_data(show_spinner=False)
def build_star_schema(csv_path: str = str(DEFAULT_CSV_FILE)) -> dict[str, pd.DataFrame]:
    df = load_raw_data(csv_path).copy()
    df["appointment_date"] = pd.to_datetime(df["appointment_date"], errors="coerce")
    df["scheduled_hour"] = pd.to_numeric(df["scheduled_hour"], errors="coerce").fillna(0).astype(int)
    df["waiting_time_minutes"] = pd.to_numeric(df["waiting_time_minutes"], errors="coerce")
    df["patient_age"] = pd.to_numeric(df["patient_age"], errors="coerce").fillna(0).astype(int)
    df["appointment_status"] = df["appointment_status"].fillna("Desconhecido")
    df["department"] = df["department"].fillna("Nao Informado")
    df["gender"] = df["gender"].fillna("Nao Informado")
    df["appointment_type"] = df["appointment_type"].fillna("Nao Informado")
    df["ethnicity"] = "Nao Informado"
    df["appointment_day"] = df["appointment_date"].dt.normalize()
    df["appointment_time"] = pd.to_datetime(
        df["scheduled_hour"].astype(str).str.zfill(2) + ":00",
        format="%H:%M",
        errors="coerce",
    )
    df["doctor_id"] = "DOC-" + (
        df["department"].astype("category").cat.codes.add(1).astype(str).str.zfill(3)
    )
    df["doctor_specialty"] = df["department"]
    df["clinic_name"] = DEFAULT_CLINIC_NAME
    df["city"] = DEFAULT_CITY
    df["state"] = DEFAULT_STATE
    df["no_show_flag"] = (df["appointment_status"].str.strip().str.lower() == "no-show").astype(int)

    dim_patient = build_surrogate_dimension(
        df,
        ["patient_age", "gender", "ethnicity"],
        "sk_patient",
    )

    date_base = pd.DataFrame({"appointment_date": df["appointment_day"]})
    dim_date = build_surrogate_dimension(date_base, ["appointment_date"], "sk_date")
    dim_date["year"] = dim_date["appointment_date"].dt.year
    dim_date["month"] = dim_date["appointment_date"].dt.month
    dim_date["day"] = dim_date["appointment_date"].dt.day
    dim_date["day_of_week"] = dim_date["appointment_date"].dt.dayofweek
    dim_date["day_name"] = dim_date["appointment_date"].dt.day_name().map(DAY_NAME_MAP)
    dim_date["month_name"] = dim_date["appointment_date"].dt.month_name().map(MONTH_NAME_MAP)
    dim_date["is_weekend"] = dim_date["day_of_week"] >= 5

    time_base = pd.DataFrame({"appointment_time": df["appointment_time"]})
    dim_time = build_surrogate_dimension(time_base, ["appointment_time"], "sk_time")
    dim_time["hour"] = dim_time["appointment_time"].dt.hour
    dim_time["minute"] = dim_time["appointment_time"].dt.minute

    dim_doctor = build_surrogate_dimension(
        df,
        ["doctor_id", "doctor_specialty"],
        "sk_doctor",
    )

    dim_clinic = build_surrogate_dimension(
        df,
        ["clinic_name", "city", "state"],
        "sk_clinic",
    )

    fact_source = df.copy()
    fact_source["sk_appointment"] = range(1, len(fact_source) + 1)

    fact_with_patient = fact_source.merge(
        dim_patient,
        on=["patient_age", "gender", "ethnicity"],
        how="left",
        validate="many_to_one",
    )
    fact_with_date = fact_with_patient.merge(
        dim_date[["sk_date", "appointment_date"]],
        left_on="appointment_day",
        right_on="appointment_date",
        how="left",
        validate="many_to_one",
    )
    fact_with_time = fact_with_date.merge(
        dim_time[["sk_time", "appointment_time"]],
        on="appointment_time",
        how="left",
        validate="many_to_one",
    )
    fact_with_doctor = fact_with_time.merge(
        dim_doctor,
        on=["doctor_id", "doctor_specialty"],
        how="left",
        validate="many_to_one",
    )
    fact_full = fact_with_doctor.merge(
        dim_clinic,
        on=["clinic_name", "city", "state"],
        how="left",
        validate="many_to_one",
    )

    fact_appointments = fact_full[
        [
            "sk_appointment",
            "sk_patient",
            "sk_date",
            "sk_time",
            "sk_doctor",
            "sk_clinic",
            "no_show_flag",
            "waiting_time_minutes",
        ]
    ].rename(columns={"waiting_time_minutes": "wait_time_minutes"})

    if len(fact_appointments) != len(df):
        raise ValueError("A fact table perdeu ou duplicou linhas durante o processo de modelagem.")

    if fact_appointments[["sk_patient", "sk_date", "sk_time", "sk_doctor", "sk_clinic"]].isna().any().any():
        raise ValueError("Foram encontradas chaves surrogate nulas apos a construcao do schema estrela.")

    granular = (
        fact_appointments.merge(dim_patient, on="sk_patient", how="left", validate="many_to_one")
        .merge(dim_date, on="sk_date", how="left", validate="many_to_one")
        .merge(dim_time, on="sk_time", how="left", validate="many_to_one")
        .merge(dim_doctor, on="sk_doctor", how="left", validate="many_to_one")
        .merge(dim_clinic, on="sk_clinic", how="left", validate="many_to_one")
    )

    if len(granular) != len(fact_appointments):
        raise ValueError("A visao granular apresentou inconsistencias apos os joins OLAP.")

    granular["age_group"] = granular["patient_age"].apply(classify_age_group)
    granular["week_period"] = granular["is_weekend"].map({True: "Fim de Semana", False: "Dia Util"})
    granular["appointment_date"] = pd.to_datetime(granular["appointment_date"]).dt.date
    granular["appointment_time"] = pd.to_datetime(granular["appointment_time"], errors="coerce").dt.strftime("%H:%M")

    return {
        "fact_appointments": fact_appointments,
        "dim_patient": dim_patient,
        "dim_date": dim_date,
        "dim_time": dim_time,
        "dim_doctor": dim_doctor,
        "dim_clinic": dim_clinic,
        "granular": granular,
    }
