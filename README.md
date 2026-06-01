# Dashboard OLAP de Consultas Medicas

Aplicacao Streamlit para analise de absenteismo (No-Show) e tempo de espera em consultas medicas, utilizando modelagem Star Schema em Pandas.

## Estrutura do projeto

```text
meu-projeto-streamlit/
|
|- .streamlit/
|  \- config.toml
|
|- data/
|  \- healthcare_appointment_no_show_wait_time.csv
|
|- src/
|  |- __init__.py
|  |- database.py
|  |- dw_model.py
|  |- components.py
|  \- plots.py
|
|- app.py
|- requirements.txt
\- README.md
```

## Responsabilidades dos modulos

- `src/database.py`: carregamento do CSV e cache de leitura.
- `src/dw_model.py`: pipeline de ETL, criacao da fato, dimensoes e visao granular.
- `src/components.py`: filtros OLAP, KPIs e renderizacao de tabelas.
- `src/plots.py`: geracao isolada dos graficos Plotly.
- `app.py`: ponto de entrada da aplicacao e orquestracao dos modulos.

## Como executar

1. Instale as dependencias:

```bash
pip install -r requirements.txt
```

2. Execute a aplicacao:

```bash
streamlit run app.py
```

## Extensibilidade

A separacao em modulos facilita futuras evolucoes, como:

- inclusao de camada de Machine Learning em novos arquivos dentro de `src/`;
- criacao de servicos para previsao de no-show;
- testes unitarios por modulo;
- substituicao do CSV por banco relacional ou data lake sem alterar a camada visual.
