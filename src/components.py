import pandas as pd
import streamlit as st

from src.dw_model import AGE_GROUP_ORDER, DAY_ORDER


def render_sidebar_filters(granular: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros OLAP")

    specialties = sorted(granular["doctor_specialty"].dropna().unique().tolist())
    genders = sorted(granular["gender"].dropna().unique().tolist())
    day_names = [day for day in DAY_ORDER if day in granular["day_name"].dropna().unique().tolist()]

    selected_specialties = st.sidebar.multiselect(
        "Especialidade Medica",
        options=specialties,
        default=specialties,
    )
    selected_genders = st.sidebar.multiselect(
        "Genero do Paciente",
        options=genders,
        default=genders,
    )
    selected_age_groups = st.sidebar.multiselect(
        "Faixa Etaria",
        options=AGE_GROUP_ORDER,
        default=AGE_GROUP_ORDER,
    )
    selected_period = st.sidebar.selectbox(
        "Periodo",
        options=["Todos", "Dia Util", "Fim de Semana"],
        index=0,
    )
    selected_days = st.sidebar.multiselect(
        "Dias da Semana",
        options=day_names,
        default=day_names,
    )

    filtered = granular.copy()
    filtered = filtered[filtered["doctor_specialty"].isin(selected_specialties)]
    filtered = filtered[filtered["gender"].isin(selected_genders)]
    filtered = filtered[filtered["age_group"].isin(selected_age_groups)]
    filtered = filtered[filtered["day_name"].isin(selected_days)]

    if selected_period != "Todos":
        filtered = filtered[filtered["week_period"] == selected_period]

    return filtered


def render_kpi_cards(filtered: pd.DataFrame) -> None:
    total_appointments = int(len(filtered))
    no_show_rate = (filtered["no_show_flag"].sum() / total_appointments * 100) if total_appointments else 0.0
    avg_wait_time = filtered["wait_time_minutes"].mean() if total_appointments else 0.0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Taxa de Absenteismo", f"{no_show_rate:.2f}%")
    kpi2.metric("Tempo Medio de Espera", f"{avg_wait_time:.1f} min")
    kpi3.metric("Total de Consultas Agendadas", f"{total_appointments:,}".replace(",", "."))


def render_star_schema_tables(schema: dict[str, pd.DataFrame]) -> None:
    with st.expander("Visualizar tabelas do Star Schema"):
        st.write("**Fact_Appointments**")
        st.dataframe(schema["fact_appointments"], use_container_width=True, hide_index=True)
        st.write("**Dim_Patient**")
        st.dataframe(schema["dim_patient"], use_container_width=True, hide_index=True)
        st.write("**Dim_Date**")
        st.dataframe(schema["dim_date"], use_container_width=True, hide_index=True)
        st.write("**Dim_Time**")
        st.dataframe(schema["dim_time"], use_container_width=True, hide_index=True)
        st.write("**Dim_Doctor**")
        st.dataframe(schema["dim_doctor"], use_container_width=True, hide_index=True)
        st.write("**Dim_Clinic**")
        st.dataframe(schema["dim_clinic"], use_container_width=True, hide_index=True)


def render_granular_table(filtered: pd.DataFrame) -> None:
    st.subheader("Tabela Granular OLAP")

    columns = [
        "sk_appointment",
        "sk_patient",
        "sk_date",
        "sk_time",
        "sk_doctor",
        "sk_clinic",
        "appointment_date",
        "appointment_time",
        "doctor_specialty",
        "gender",
        "patient_age",
        "age_group",
        "day_name",
        "week_period",
        "no_show_flag",
        "wait_time_minutes",
        "clinic_name",
        "city",
        "state",
    ]

    display_df = filtered[columns].sort_values(
        by=["appointment_date", "appointment_time", "sk_appointment"],
        ascending=True,
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
