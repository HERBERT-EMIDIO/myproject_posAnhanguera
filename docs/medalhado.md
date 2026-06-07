# Projeto Medalhado — Guia prático (Python + SQL)

Este documento é um guia didático para você aprender e aplicar a arquitetura medallion (Bronze → Silver → Gold) usando Python e SQL. Cada seção explica o objetivo pedagógico e dá comandos práticos para execução em Windows.

**Estrutura do fluxo (visão geral)**
- Bronze: ingestão de dados brutos (raw) — armazenamos cópias idênticas dos arquivos/streams.
- Silver: limpeza e transformação — tipagem, normalização, remoção de duplicatas.
- Gold: modelos analíticos/consumíveis — agregações, métricas e tabelas prontas para BI.

---

## 1) Bronze — captura e armazenagem do dado bruto

Objetivo do professor: garantir que o aluno entenda que Bronze é o ponto de partida — nunca sobrescrever o raw, armazenar versão e metadata.

Exemplo de comandos (Windows PowerShell):

```powershell
# crie e ative um ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# atualize pip e instale pacotes úteis
python -m pip install --upgrade pip
pip install pandas sqlalchemy duckdb jupyterlab
```

Comando para inspeção rápida dos arquivos CSV (PowerShell):

```powershell
Get-ChildItem -Path landing\*.csv | Select-Object Name, Length
Get-Content landing\z0019_1.csv -TotalCount 10
```

Exemplo em DuckDB (criar tabela Bronze lendo CSV cru):

```sql
-- no REPL do duckdb (ou via DuckDB CLI):
CREATE TABLE bronze_z0019 AS
SELECT * FROM read_csv_auto('landing/z0019_1.csv');
```

Exemplo usando Python (salvar raw em parquet/SQLite como cópia):

```python
# scripts/ingest_bronze.py (exemplo)
import pandas as pd
from pathlib import Path

p = Path('landing/z0019_1.csv')
df = pd.read_csv(p)
# gravar cópia em parquet (compressão eficiente)
Path('bronze').mkdir(exist_ok=True)
df.to_parquet('bronze/z0019_1.parquet', index=False)
```

Rodar o script:

```powershell
python scripts/ingest_bronze.py
```

---

## 2) Silver — limpeza, validação e conformidade

Objetivo do professor: transformar o dado em formatos e tipos consistentes, tratar valores faltantes, padronizar campos e deduplicar. Nesta camada já aplicamos regras de negócio simples.

Exemplo de passos e comandos:

```python
# scripts/transform_silver.py
import pandas as pd
from pathlib import Path

# carregar bronze
df = pd.read_parquet('bronze/z0019_1.parquet')

# limpeza básica
df = df.drop_duplicates()
# normalizar nomes (exemplo)
df['nome'] = df['nome'].str.strip().str.title()
# converter tipos
df['data'] = pd.to_datetime(df['data'], errors='coerce')

# exportar silver
Path('silver').mkdir(exist_ok=True)
df.to_parquet('silver/z0019_1_clean.parquet', index=False)
```

Comando para executar:

```powershell
python scripts/transform_silver.py
```

Exemplo SQL em DuckDB para criar tabela Silver a partir de Bronze com transformação:

```sql
CREATE TABLE silver_z0019 AS
SELECT
  id,
  TRIM(UPPER(nome)) AS nome,
  TRY_CAST(data AS DATE) AS data,
  valor
FROM bronze_z0019
WHERE id IS NOT NULL; -- regra de qualidade
```

---

## 3) Gold — modelos e tabelas prontas para consumo

Objetivo do professor: preparar tabelas otimizadas para relatórios e consumo por analistas/BI. Aqui realizamos agregações, juncões entre domínios e calculamos métricas.

Exemplos de consultas e comandos:

```sql
-- Exemplo: agregação mensal
CREATE TABLE gold_metrics_z0019 AS
SELECT
  DATE_TRUNC('month', data) AS mes,
  COUNT(*) AS total_registros,
  SUM(valor) AS soma_valores,
  AVG(valor) AS media_valor
FROM silver_z0019
GROUP BY DATE_TRUNC('month', data);
```

Em Python, gerar CSV final para BI:

```python
# scripts/generate_gold.py
import pandas as pd

df = pd.read_parquet('silver/z0019_1_clean.parquet')
df['mes'] = pd.to_datetime(df['data']).dt.to_period('M')
metrics = df.groupby('mes').agg(total_registros=('id','count'), soma_valores=('valor','sum'))
metrics.to_csv('gold/z0019_monthly_metrics.csv')
```

Executar:

```powershell
python scripts/generate_gold.py
```

---

## Comandos SQL úteis (exemplos)

- Conectar ao SQLite (CLI):

```powershell
sqlite3 dados.db
-- dentro do sqlite3:
.tables
.mode csv
.import landing/z0019_1.csv bronze_z0019
```

- Usar DuckDB a partir do terminal:

```powershell
# criar banco DuckDB e rodar um script SQL
duckdb mydata.duckdb "CREATE TABLE bronze_z0019 AS SELECT * FROM read_csv_auto('landing/z0019_1.csv');"
```

- Consultas de verificação:

```sql
SELECT COUNT(*) FROM bronze_z0019;
SELECT COUNT(DISTINCT id) FROM silver_z0019;
SELECT mes, total_registros FROM gold_metrics_z0019 ORDER BY mes DESC LIMIT 12;
```

---

## Boas práticas de professor para o aluno

- Nunca altere o Bronze diretamente; sempre gere nova versão com timestamp quando necessário.
- Versione esquemas: registre a versão do schema das tabelas (ex.: coluna `__schema_version`).
- Valide qualidade: indicadores simples como `pct_null`, `pct_duplicates` são essenciais.
- Escreva testes de regressão para transformações críticas.

---

## Como rodar tudo em sequência (exemplo simples)

```powershell
# 1. ativar ambiente
.\.venv\Scripts\Activate.ps1

# 2. rodar ingestão bronze
python scripts/ingest_bronze.py

# 3. transformar para silver
python scripts/transform_silver.py

# 4. gerar gold
python scripts/generate_gold.py
```

Se você já tem um script de ingestão no repositório, rode:

```powershell
python scripts/run_ingest.py
```

---

## Recursos e próximos passos sugeridos

- Documente cada transformação com um pequeno arquivo `transform_X.md` explicando por que a regra existe.
- Adicione checks automatizados (unit tests) para transformações importantes.
- Aprenda a usar ferramentas como `dbt` (Data Build Tool) para gerenciar o Silver→Gold com versionamento e testes.

---

Boa sorte nos estudos — se quiser, eu adapto este guia para usar `duckdb`, `sqlite`, `postgres` ou para adicionar exemplos com `dbt`.
