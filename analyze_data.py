import pandas as pd

try:
    df1 = pd.read_csv('saida_csv/relatorio1_operacoes_por_tipo.csv')
    df1['data'] = pd.to_datetime(df1['ano'].astype(str) + "-" + df1['mes'].astype(str).str.zfill(2) + "-01")
    df1 = df1.sort_values('data')
    historical_volume = df1['valor_total'].sum()
    print("Historical Volume:", historical_volume)
    
    last_year = df1['data'].dt.year.max()
    print("Latest Year:", last_year)

    last_12_m = df1.tail(12)
    v_12m = last_12_m['valor_total'].sum()
    print("12 Month Volume:", v_12m)
    
    df4 = pd.read_csv('saida_csv/relatorio4_criptoativos_mensal.csv')
    df4['data'] = pd.to_datetime(df4['ano'].astype(str) + "-" + df4['mes'].astype(str).str.zfill(2) + "-01")
    df4_last12 = df4[df4['data'] >= df1['data'].max() - pd.DateOffset(months=11)]
    crypto_vol = df4_last12.groupby('criptoativo')['valor_total_operacoes'].sum().sort_values(ascending=False).head(5)
    print("\nCrypto Volumes Last 12m:")
    print(crypto_vol)
    total_crypto_12m = df4_last12['valor_total_operacoes'].sum()
    print("Total Crypto Last 12m:", total_crypto_12m)
    if total_crypto_12m > 0:
        for c, v in crypto_vol.items():
            print(f"{c}: {v/total_crypto_12m*100:.2f}%")
            
    df2 = pd.read_csv('saida_csv/relatorio2_cpfs_cnpjs_unicos.csv')
    df2['data'] = pd.to_datetime(df2['ano'].astype(str) + "-" + df2['mes'].astype(str).str.zfill(2) + "-01")
    df2 = df2.sort_values('data')
    print("\nMax CPFS:", df2['cpfs_unicos'].max())
    print("Max CNPJs:", df2['cnpjs_unicos'].max())
    latest_users = df2.iloc[-1]
    print(f"Latest Month ({latest_users['data']}) Users -> CPFs: {latest_users['cpfs_unicos']}, CNPJs: {latest_users['cnpjs_unicos']}")
    
    avg_usdt_ticket = df4[df4['criptoativo'] == 'Tether']['valor_medio_operacao'].tail(1).values[0] if not df4[df4['criptoativo'] == 'Tether'].empty else 0
    print("Latest USDT Average Ticket:", avg_usdt_ticket)
    avg_btc_ticket = df4[df4['criptoativo'] == 'Bitcoin']['valor_medio_operacao'].tail(1).values[0] if not df4[df4['criptoativo'] == 'Bitcoin'].empty else 0
    print("Latest BTC Average Ticket:", avg_btc_ticket)
except Exception as e:
    print("Error:", e)
