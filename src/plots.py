import pandas as pd
import plotly.express as px

from src.dw_model import AGE_GROUP_ORDER


def create_no_show_by_specialty_chart(filtered: pd.DataFrame):
    specialty_rate = (
        filtered.groupby("doctor_specialty", as_index=False)
        .agg(total_agendamentos=("sk_appointment", "count"), taxa_absenteismo=("no_show_flag", "mean"))
        .sort_values("taxa_absenteismo", ascending=False)
    )
    specialty_rate["taxa_absenteismo"] = specialty_rate["taxa_absenteismo"] * 100

    fig = px.bar(
        specialty_rate,
        x="doctor_specialty",
        y="taxa_absenteismo",
        color="taxa_absenteismo",
        color_continuous_scale="Blues",
        text="taxa_absenteismo",
        labels={
            "doctor_specialty": "Especialidade Medica",
            "taxa_absenteismo": "Taxa de Absenteismo (%)",
        },
        title="Taxa de Absenteismo por Especialidade Medica",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-20)
    return fig


def create_wait_time_by_day_chart(filtered: pd.DataFrame):
    wait_by_day = (
        filtered.groupby(["day_name", "day_of_week"], as_index=False)
        .agg(tempo_medio_espera=("wait_time_minutes", "mean"))
        .sort_values("day_of_week")
    )

    fig = px.line(
        wait_by_day,
        x="day_name",
        y="tempo_medio_espera",
        markers=True,
        labels={"day_name": "Dia da Semana", "tempo_medio_espera": "Tempo Medio de Espera (min)"},
        title="Tempo Medio de Espera por Dia da Semana",
    )
    return fig


def create_drilldown_chart(
    filtered: pd.DataFrame,
    selected_specialty: str,
    breakdown_dimension: str,
):
    specialty_df = filtered[filtered["doctor_specialty"] == selected_specialty].copy()
    breakdown_col = "age_group" if breakdown_dimension == "Faixa Etaria" else "gender"
    x_label = "Faixa Etaria" if breakdown_dimension == "Faixa Etaria" else "Genero"

    drilldown = (
        specialty_df.groupby(breakdown_col, as_index=False)
        .agg(total_agendamentos=("sk_appointment", "count"), taxa_absenteismo=("no_show_flag", "mean"))
    )
    drilldown["taxa_absenteismo"] = drilldown["taxa_absenteismo"] * 100

    if breakdown_col == "age_group":
        drilldown[breakdown_col] = pd.Categorical(
            drilldown[breakdown_col],
            categories=AGE_GROUP_ORDER,
            ordered=True,
        )
        drilldown = drilldown.sort_values(breakdown_col)
    else:
        drilldown = drilldown.sort_values("taxa_absenteismo", ascending=False)

    fig = px.bar(
        drilldown,
        x=breakdown_col,
        y="taxa_absenteismo",
        color=breakdown_col,
        text="taxa_absenteismo",
        labels={breakdown_col: x_label, "taxa_absenteismo": "Taxa de Absenteismo (%)"},
        title=f"Detalhamento do Absenteismo em {selected_specialty}",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(showlegend=False)
    return fig
