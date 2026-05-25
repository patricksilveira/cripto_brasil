"""
Generates static JSON data files for the Next.js dashboard.
Reads CSVs from saida_csv/, merges FX rates, outputs to web/public/data/.
"""
import json
import pandas as pd
from pathlib import Path

SRC = Path(__file__).parent.parent / "saida_csv"
OUT = Path(__file__).parent.parent / "web" / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def load_fx():
    df = pd.read_csv(SRC / "usd_brl_monthly.csv")
    df["data"] = pd.to_datetime(df["data"])
    df["ym"] = df["data"].dt.to_period("M")
    return df.set_index("ym")["rate"]


def to_date(row):
    return f"{int(row['ano'])}-{int(row['mes']):02d}-01"


def usd(val, rate):
    if pd.isna(val) or pd.isna(rate):
        return None
    return round(val / rate, 4)


def run():
    fx = load_fx()

    # ── 1. Operations ────────────────────────────────────────────────────────
    ops = pd.read_csv(SRC / "relatorio1_operacoes_por_tipo.csv")
    ops["date"] = ops.apply(to_date, axis=1)
    ops["ym"] = pd.to_datetime(ops["date"]).dt.to_period("M")
    ops["rate"] = ops["ym"].map(fx)

    money_cols = [
        "valor_exterior_pf", "valor_exterior_pj", "valor_exterior_subtotal",
        "valor_sem_ex_pf", "valor_sem_ex_pj", "valor_sem_ex_subtotal",
        "valor_exchanges", "valor_total",
    ]

    ops_out = []
    for _, r in ops.iterrows():
        row = {
            "date": r["date"],
            "year": int(r["ano"]),
            "month": int(r["mes"]),
            "rate": round(r["rate"], 4) if pd.notna(r.get("rate")) else None,
        }
        for c in money_cols:
            row[f"{c}_brl"] = round(r[c], 2) if pd.notna(r[c]) else None
            row[f"{c}_usd"] = usd(r[c], r.get("rate"))
        ops_out.append(row)

    ops_out.sort(key=lambda x: x["date"])
    (OUT / "operations.json").write_text(json.dumps(ops_out, ensure_ascii=False))
    print(f"operations.json — {len(ops_out)} rows")

    # ── 2. Users ─────────────────────────────────────────────────────────────
    users = pd.read_csv(SRC / "relatorio2_cpfs_cnpjs_unicos.csv")
    users["date"] = users.apply(to_date, axis=1)
    users = users.sort_values("date")
    users["total"] = users["cpfs_unicos"] + users["cnpjs_unicos"]
    users["mom_pct"] = users["total"].pct_change() * 100
    users["cpf_mom_pct"] = users["cpfs_unicos"].pct_change() * 100
    users["cnpj_mom_pct"] = users["cnpjs_unicos"].pct_change() * 100

    users_out = []
    for _, r in users.iterrows():
        users_out.append({
            "date": r["date"],
            "year": int(r["ano"]),
            "month": int(r["mes"]),
            "cpfs": int(r["cpfs_unicos"]),
            "cnpjs": int(r["cnpjs_unicos"]),
            "total": int(r["total"]),
            "mom_pct": round(r["mom_pct"], 2) if pd.notna(r["mom_pct"]) else None,
            "cpf_mom_pct": round(r["cpf_mom_pct"], 2) if pd.notna(r["cpf_mom_pct"]) else None,
            "cnpj_mom_pct": round(r["cnpj_mom_pct"], 2) if pd.notna(r["cnpj_mom_pct"]) else None,
        })

    (OUT / "users.json").write_text(json.dumps(users_out, ensure_ascii=False))
    print(f"users.json — {len(users_out)} rows")

    # ── 3. Gender ─────────────────────────────────────────────────────────────
    gen = pd.read_csv(SRC / "relatorio3_genero_operacoes.csv")
    gen["date"] = gen.apply(to_date, axis=1)
    gen = gen.sort_values("date")

    gen_out = []
    for _, r in gen.iterrows():
        gen_out.append({
            "date": r["date"],
            "year": int(r["ano"]),
            "month": int(r["mes"]),
            "pct_num_fem": round(r["perc_num_oper_feminino"], 2),
            "pct_num_masc": round(r["perc_num_oper_masculino"], 2),
            "pct_val_fem": round(r["perc_valor_oper_feminino"], 2),
            "pct_val_masc": round(r["perc_valor_oper_masculino"], 2),
        })

    (OUT / "gender.json").write_text(json.dumps(gen_out, ensure_ascii=False))
    print(f"gender.json — {len(gen_out)} rows")

    # ── 4. Crypto assets ──────────────────────────────────────────────────────
    crypto = pd.read_csv(SRC / "relatorio4_criptoativos_mensal.csv")
    crypto = crypto[crypto["criptoativo"] != "criptoativo"].copy()
    crypto["date"] = crypto.apply(to_date, axis=1)
    crypto["ym"] = pd.to_datetime(crypto["date"]).dt.to_period("M")
    crypto["rate"] = crypto["ym"].map(fx)
    crypto = crypto.sort_values(["criptoativo", "date"])

    crypto_out = []
    for _, r in crypto.iterrows():
        # total values: raw BRL → convert to millions (matching operations scale)
        total_raw = r["valor_total_operacoes"]
        total_m = round(total_raw / 1_000_000, 4) if pd.notna(total_raw) else None
        avg_raw = r["valor_medio_operacao"]
        crypto_out.append({
            "asset": str(r["criptoativo"]),
            "date": r["date"],
            "year": int(r["ano"]),
            "month": int(r["mes"]),
            "num_ops": int(r["num_operacoes"]) if pd.notna(r["num_operacoes"]) else None,
            "total_brl": total_m,
            "total_usd": usd(total_m, r.get("rate")) if total_m is not None else None,
            "avg_brl": round(avg_raw, 2) if pd.notna(avg_raw) else None,
            "avg_usd": usd(avg_raw, r.get("rate")),
        })

    (OUT / "cryptos.json").write_text(json.dumps(crypto_out, ensure_ascii=False))
    print(f"cryptos.json — {len(crypto_out)} rows")

    # ── 5. FX rates ───────────────────────────────────────────────────────────
    fx_out = [{"date": str(p) + "-01", "rate": round(r, 4)} for p, r in fx.items()]
    (OUT / "fx_rates.json").write_text(json.dumps(fx_out, ensure_ascii=False))
    print(f"fx_rates.json — {len(fx_out)} rows")

    print("\nAll done →", OUT.resolve())


if __name__ == "__main__":
    run()
