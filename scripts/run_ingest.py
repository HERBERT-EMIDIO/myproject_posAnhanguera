import duckdb
import pandas as pd
import glob
import os
from datetime import datetime

# Caminhos
base_dir = os.path.dirname(__file__)
db_path = os.path.join(base_dir, 'dados_duckbd.db')
landing_pattern = os.path.join(base_dir, '..', 'landing', '*.csv')

print('DB path:', db_path)
con = duckdb.connect(database=db_path, read_only=False)

# Cria tabela se não existir
con.execute('''
CREATE TABLE IF NOT EXISTS bronze_z0019(
    NATB VARCHAR,
    MAKTX VARCHAR,
    WERKS VARCHAR,
    MAINS VARCHAR,
    LABST VARCHAR,
    nome_arquivo VARCHAR,
    data_ingestao TIMESTAMP
)
''')

files = sorted(glob.glob(landing_pattern))
print('Arquivos encontrados:', files)

for path in files:
    name = os.path.basename(path)
    print('Processando', name)
    df = pd.read_csv(path, sep=';')
    # Normaliza colunas
    if 'NATBR' in df.columns and 'NATB' not in df.columns:
        df = df.rename(columns={'NATBR':'NATB'})
    for c in ['NATB','MAKTX','WERKS','MAINS','LABST']:
        if c not in df.columns:
            df[c] = pd.NA
    df['nome_arquivo'] = name
    df['data_ingestao'] = datetime.now()
    df = df[['NATB','MAKTX','WERKS','MAINS','LABST','nome_arquivo','data_ingestao']]
    con.register('tmp_df', df)
    con.execute("INSERT INTO bronze_z0019 SELECT * FROM tmp_df")
    con.unregister('tmp_df')
    print(f'Inserido {len(df)} linhas de {name}')

print('\nTabelas no DB:')
print(con.execute("SHOW TABLES").fetchdf())
print('\nContagem por arquivo:')
print(con.execute("SELECT nome_arquivo, COUNT(*) AS cnt FROM bronze_z0019 GROUP BY nome_arquivo").fetchdf())
print('\nTotal:', con.execute("SELECT COUNT(*) AS total FROM bronze_z0019").fetchdf()['total'][0])

con.close()