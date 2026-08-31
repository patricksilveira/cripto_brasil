import pandas as pd
import re
from pathlib import Path

ARQUIVO_XLS = "criptoativos_dados_abertos_20260826.xls"
PASTA_SAIDA = Path("saida_csv")
PASTA_SAIDA.mkdir(exist_ok=True)

# Helper to split "Janeiro de 2022" into two columns: mes_num, ano
def quebrar_mes_ano(col):
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }
    mes_idx = []
    ano = []
    for v in col:
        if isinstance(v, str) and "de" in v.lower():
            partes = [p.strip().lower() for p in v.split("de")]
            mes_str, ano_str = partes[0], partes[1]
            num = meses.get(mes_str, None)
            try:
                ano_val = int(ano_str)
            except ValueError:
                ano_val = None
        else:
            num, ano_val = None, None
        mes_idx.append(num)
        ano.append(ano_val)
    return mes_idx, ano

def arredonda_float_cols(df):
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].round(2)
    return df

def ler_aba_com_cabecalho(xls_path, sheet_name, col_esperada):
    df_raw = pd.read_excel(xls_path, sheet_name=sheet_name, header=None)
    header_idx = 0
    for idx, row in df_raw.iterrows():
        row_vals = [str(x).strip().upper() for x in row.dropna().values]
        if col_esperada.upper() in row_vals:
            header_idx = idx
            break
    return pd.read_excel(xls_path, sheet_name=sheet_name, header=header_idx)

def limpar_relatorio1(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        df.columns[0]: "mes_ano",
        df.columns[1]: "valor_exterior_pf",
        df.columns[2]: "valor_exterior_pj",
        df.columns[3]: "valor_exterior_subtotal",
        df.columns[4]: "valor_sem_ex_pf",
        df.columns[5]: "valor_sem_ex_pj",
        df.columns[6]: "valor_sem_ex_subtotal",
        df.columns[7]: "valor_exchanges",
        df.columns[8]: "valor_total"
    })
    df = df[df["mes_ano"].notna()].copy()
    df["mes_ano"] = df["mes_ano"].astype(str).str.strip()
    mes, ano = quebrar_mes_ano(df["mes_ano"])
    df["mes"] = mes
    df["ano"] = ano
    df = df[df["mes"].notna() & df["ano"].notna()].copy()
    df = arredonda_float_cols(df)
    cols_order = ["mes", "ano"] + [c for c in df.columns if c not in ("mes", "ano", "mes_ano")]
    return df[cols_order]

def limpar_relatorio2(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        df.columns[0]: "mes_ano",
        df.columns[1]: "cpfs_unicos",
        df.columns[2]: "cnpjs_unicos"
    })
    df = df[df["mes_ano"].notna()]
    df = df[df["mes_ano"] != "MÊS/ANO"].copy()
    df["mes_ano"] = df["mes_ano"].astype(str).str.strip()
    mes, ano = quebrar_mes_ano(df["mes_ano"])
    df["mes"] = mes
    df["ano"] = ano
    df = df[df["mes"].notna() & df["ano"].notna()].copy()
    cols_order = ["mes", "ano"] + [c for c in df.columns if c not in ("mes", "ano", "mes_ano")]
    return df[cols_order]

def limpar_relatorio3(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        df.columns[0]: "periodo",
        df.columns[1]: "perc_num_oper_feminino",
        df.columns[2]: "perc_num_oper_masculino",
        df.columns[3]: "perc_valor_oper_feminino",
        df.columns[4]: "perc_valor_oper_masculino"
    })
    df = df[df["periodo"].notna()].copy()
    df["periodo"] = df["periodo"].astype(str).str.strip()
    mes, ano = quebrar_mes_ano(df["periodo"])
    df["mes"] = mes
    df["ano"] = ano
    df = df[df["mes"].notna() & df["ano"].notna()].copy()
    df = arredonda_float_cols(df)
    cols_order = ["mes", "ano"] + [c for c in df.columns if c not in ("mes", "ano", "periodo")]
    return df[cols_order]

def limpar_relatorio4(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "CRIPTOATIVO": "criptoativo",
        "MÊS/ANO": "mes_ano",
        "Nº DE OPERAÇÕES": "num_operacoes",
        "VALOR TOTAL DAS OPERAÇÕES": "valor_total_operacoes",
        "VALOR MÉDIO POR OPERAÇÃO": "valor_medio_operacao"
    })
    df = df.dropna(how="all").copy()
    df["criptoativo"] = df["criptoativo"].astype(str).str.strip()
    df["mes_ano"] = df["mes_ano"].astype(str).str.strip()

    # Convert numeric columns: remove commas and spaces, then convert to float
    for col in ["num_operacoes", "valor_total_operacoes", "valor_medio_operacao"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(",", "").str.replace(" ", "")
            df[col] = pd.to_numeric(df[col], errors='coerce')

    mes, ano = quebrar_mes_ano(df["mes_ano"])
    df["mes"] = mes
    df["ano"] = ano
    df = df[df["mes"].notna() & df["ano"].notna()].copy()
    df = arredonda_float_cols(df)
    cols_order = ["criptoativo", "mes", "ano"] + [c for c in df.columns if c not in ("criptoativo", "mes", "ano", "mes_ano")]
    return df[cols_order]

def main():
    xls = pd.ExcelFile(ARQUIVO_XLS)
    print("Abas encontradas:", xls.sheet_names)

    df1 = ler_aba_com_cabecalho(ARQUIVO_XLS, "Relatorio1", "MÊS/ANO")
    df1_limpo = limpar_relatorio1(df1)
    df1_limpo.to_csv(PASTA_SAIDA / "relatorio1_operacoes_por_tipo.csv", index=False)

    df2 = ler_aba_com_cabecalho(ARQUIVO_XLS, "Relatorio2", "MÊS/ANO")
    df2_limpo = limpar_relatorio2(df2)
    df2_limpo.to_csv(PASTA_SAIDA / "relatorio2_cpfs_cnpjs_unicos.csv", index=False)

    df3 = ler_aba_com_cabecalho(ARQUIVO_XLS, "Relatório3", "PERÍODO")
    df3_limpo = limpar_relatorio3(df3)
    df3_limpo.to_csv(PASTA_SAIDA / "relatorio3_genero_operacoes.csv", index=False)

    df4 = ler_aba_com_cabecalho(ARQUIVO_XLS, "Relatorio4", "CRIPTOATIVO")
    df4_limpo = limpar_relatorio4(df4)
    df4_limpo.to_csv(PASTA_SAIDA / "relatorio4_criptoativos_mensal.csv", index=False)

    print("CSVs gerados em:", PASTA_SAIDA.resolve())

if __name__ == "__main__":
    main()
