# Projeto Medalhão — Arquitetura Medallion com Python

Projeto de pós-graduação demonstrando a implementação da **Arquitetura Medallion** (Bronze → Silver → Gold) para pipeline de dados de estoque de materiais.

## Arquitetura

```text
landing/          ← Arquivos brutos da fonte (CSV do ERP)
data/
  bronze/         ← Cópia fiel do raw em Parquet + metadados de auditoria
  silver/         ← Dados limpos, tipados e deduplicados
  gold/           ← Modelos analíticos (Star Schema) prontos para BI
notebooks/
  01_ingestao_bronze.ipynb       ← Ingestão sem transformação
  02_processamento_silver.ipynb  ← Limpeza, tipagem, deduplicação
  03_transformacao_gold.ipynb    ← Star Schema + KPIs
src/
  utils.py        ← Funções reutilizáveis do pipeline
```

## Por que Medallion?

| Camada     | Princípio                       | Benefício                              |
| ---------- | ------------------------------- | -------------------------------------- |
| **Bronze** | Zero transformação no conteúdo  | Reprocessamento sempre possível        |
| **Silver** | Uma fonte de verdade limpa      | Qualidade garantida para analytics     |
| **Gold**   | Otimizado para consumo          | Consultas rápidas, BI sem SQL complexo |

## Como usar no Google Colab

1. Faça upload do projeto para o Google Drive
2. Em cada notebook, descomente o bloco de montagem do Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
import os
os.chdir('/content/drive/MyDrive/meu-projeto-medalhao')
```

1. Execute os notebooks em ordem: `01` → `02` → `03`

## Dado utilizado

Extrato de estoque simulando saída de ERP (formato SAP):

| Coluna | Tipo  | Descrição                  |
| ------ | ----- | -------------------------- |
| NATB   | int   | Número do material         |
| MAKTX  | str   | Descrição do material      |
| WERKS  | str   | Centro/planta              |
| MAINS  | int   | Tipo de estoque            |
| LABST  | float | Quantidade disponível      |

## Dependências

```text
pandas
pyarrow
numpy
```

Instalar: `pip install pandas pyarrow numpy`

## Stack

- **Python 3.10+**
- **Pandas** — transformações e agregações
- **PyArrow / Parquet** — armazenamento colunar eficiente
- **Google Colab** — execução em nuvem (sem instalação local)
