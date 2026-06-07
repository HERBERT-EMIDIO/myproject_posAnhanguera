"""
utils.py — Funções reutilizáveis para o pipeline Medallion.

Por que centralizar aqui?
  Evita duplicação de lógica nos notebooks. Cada camada importa o que precisa,
  mantendo os notebooks focados na narrativa e não em código boilerplate.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib


# ── Caminhos base ──────────────────────────────────────────────────────────────
# No Colab, monte o Drive e ajuste BASE_PATH para o caminho do seu projeto.
# Ex: BASE_PATH = Path("/content/drive/MyDrive/meu-projeto-medalhao")
BASE_PATH = Path(".")

LANDING = BASE_PATH / "landing"
BRONZE  = BASE_PATH / "data" / "bronze"
SILVER  = BASE_PATH / "data" / "silver"
GOLD    = BASE_PATH / "data" / "gold"


def ensure_dirs():
    """Garante que todas as camadas existam antes de gravar."""
    for d in [BRONZE, SILVER, GOLD]:
        d.mkdir(parents=True, exist_ok=True)


# ── Bronze ─────────────────────────────────────────────────────────────────────

def ingest_csv_to_bronze(filename: str, sep: str = ";") -> pd.DataFrame:
    """
    Lê um CSV da landing zone e salva em Parquet na Bronze.

    Princípio: zero transformação — preservamos o dado exatamente como chegou.
    Adicionamos apenas colunas de auditoria para rastreabilidade.
    """
    src = LANDING / filename
    df = pd.read_csv(src, sep=sep, dtype=str)  # dtype=str preserva tudo como texto

    # Metadados de auditoria — nunca alteram o conteúdo original
    df["_source_file"]  = filename
    df["_ingested_at"]  = datetime.utcnow().isoformat()
    df["_row_hash"]     = df.apply(
        lambda r: hashlib.md5(str(r.values).encode()).hexdigest(), axis=1
    )

    dest = BRONZE / filename.replace(".csv", ".parquet")
    df.to_parquet(dest, index=False)
    print(f"[Bronze] {len(df)} linhas gravadas → {dest}")
    return df


# ── Silver ─────────────────────────────────────────────────────────────────────

def load_bronze(filename_stem: str) -> pd.DataFrame:
    """Carrega um arquivo Parquet da Bronze pelo nome-base (sem extensão)."""
    return pd.read_parquet(BRONZE / f"{filename_stem}.parquet")


def deduplicate(df: pd.DataFrame, subset: list[str] | None = None, keep: str = "last") -> pd.DataFrame:
    """
    Remove duplicatas mantendo a linha mais recente (keep='last').

    Por que 'last'? Em re-ingestões, o registro mais novo tende a ser
    a versão corrigida. Ajuste para 'first' se a regra de negócio exigir.
    """
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep=keep)
    print(f"[Silver] Deduplicação: {before} → {len(df)} linhas ({before - len(df)} removidas)")
    return df


def report_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna um resumo de nulos por coluna (útil para documentar qualidade)."""
    total = len(df)
    summary = pd.DataFrame({
        "nulos":   df.isnull().sum(),
        "pct_null": (df.isnull().sum() / total * 100).round(2),
    })
    return summary[summary["nulos"] > 0]


# ── Gold ───────────────────────────────────────────────────────────────────────

def save_gold(df: pd.DataFrame, name: str, also_csv: bool = True):
    """
    Salva tabela Gold em Parquet (principal) e opcionalmente CSV (para BI/Colab preview).

    Parquet é o formato padrão — comprimido e com schema embutido.
    CSV é gerado como conveniência para ferramentas que não leem Parquet.
    """
    parquet_path = GOLD / f"{name}.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"[Gold] Parquet gravado → {parquet_path}")

    if also_csv:
        csv_path = GOLD / f"{name}.csv"
        df.to_csv(csv_path, index=False, sep=";")
        print(f"[Gold] CSV gravado    → {csv_path}")
