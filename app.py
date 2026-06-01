import streamlit as st
from src.components import (
    render_granular_table,
    render_kpi_cards,
    render_sidebar_filters,
    render_star_schema_tables,
)
from src.database import DEFAULT_CSV_FILE
from src.dw_model import build_star_schema
from src.plots import (
    create_drilldown_chart,
    create_no_show_by_specialty_chart,
    create_wait_time_by_day_chart,
)


st.set_page_config(
    page_title="Dashboard OLAP de Consultas Medicas",
    page_icon=":bar_chart:",
    layout="wide",
)


def render_drilldown_section(filtered):
    st.subheader("Drill-down Analitico")

    specialties = sorted(filtered["doctor_specialty"].dropna().unique().tolist())
    if not specialties:
        st.info("Nenhuma especialidade disponivel para detalhamento com os filtros atuais.")
        return

    selected_specialty = st.selectbox(
        "Selecione uma especialidade para detalhar",
        options=specialties,
    )
    breakdown_dimension = st.radio(
        "Detalhar absenteismo por",
        options=["Faixa Etaria", "Genero"],
        horizontal=True,
    )
    st.plotly_chart(
        create_drilldown_chart(filtered, selected_specialty, breakdown_dimension),
        use_container_width=True,
    )


def main() -> None:
    st.title("Dashboard de Desempenho e Simulacao OLAP")
    st.caption(
        "Analise multidimensional de absenteismo e tempo de espera em consultas medicas com modelagem Star Schema em Pandas."
    )

    schema = build_star_schema(str(DEFAULT_CSV_FILE))
    granular = schema["granular"]
    filtered = render_sidebar_filters(granular)

    if filtered.empty:
        st.warning("Nenhum registro encontrado para a combinacao de filtros selecionada.")
        return

    render_kpi_cards(filtered)

    col_left, col_right = st.columns([1.6, 1.0])
    with col_left:
        st.plotly_chart(create_no_show_by_specialty_chart(filtered), use_container_width=True)
    with col_right:
        st.plotly_chart(create_wait_time_by_day_chart(filtered), use_container_width=True)

    render_drilldown_section(filtered)

    render_star_schema_tables(schema)
    render_granular_table(filtered)


if __name__ == "__main__":
    main()
