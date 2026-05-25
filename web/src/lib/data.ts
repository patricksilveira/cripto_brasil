export type Operation = {
  date: string
  year: number
  month: number
  rate: number | null
  valor_total_brl: number
  valor_total_usd: number | null
  valor_exterior_pf_brl: number
  valor_exterior_pf_usd: number | null
  valor_exterior_pj_brl: number
  valor_exterior_pj_usd: number | null
  valor_exterior_subtotal_brl: number
  valor_exterior_subtotal_usd: number | null
  valor_sem_ex_pf_brl: number
  valor_sem_ex_pf_usd: number | null
  valor_sem_ex_pj_brl: number
  valor_sem_ex_pj_usd: number | null
  valor_sem_ex_subtotal_brl: number
  valor_sem_ex_subtotal_usd: number | null
  valor_exchanges_brl: number
  valor_exchanges_usd: number | null
}

export type UserRecord = {
  date: string
  year: number
  month: number
  cpfs: number
  cnpjs: number
  total: number
  mom_pct: number | null
  cpf_mom_pct: number | null
  cnpj_mom_pct: number | null
}

export type GenderRecord = {
  date: string
  year: number
  month: number
  pct_num_fem: number
  pct_num_masc: number
  pct_val_fem: number
  pct_val_masc: number
}

export type CryptoRecord = {
  asset: string
  date: string
  year: number
  month: number
  num_ops: number | null
  total_brl: number | null
  total_usd: number | null
  avg_brl: number | null
  avg_usd: number | null
}

export type FxRecord = {
  date: string
  rate: number
}

export type DashboardData = {
  operations: Operation[]
  users: UserRecord[]
  gender: GenderRecord[]
  cryptos: CryptoRecord[]
  fxRates: FxRecord[]
}

export function formatCurrency(
  value: number | null | undefined,
  currency: "BRL" | "USD",
  compact = true
): string {
  if (value == null) return "—"
  const symbol = currency === "USD" ? "US$" : "R$"
  // Values are in millions
  const abs = Math.abs(value)
  if (compact) {
    if (abs >= 1000) return `${symbol} ${(value / 1000).toFixed(1)}B`
    if (abs >= 1) return `${symbol} ${value.toFixed(1)}M`
    return `${symbol} ${(value * 1000).toFixed(0)}K`
  }
  return `${symbol} ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}M`
}

export function formatNumber(n: number | null | undefined, compact = true): string {
  if (n == null) return "—"
  if (compact && n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (compact && n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toLocaleString("pt-BR")
}

export function formatDate(dateStr: string): string {
  const [y, m] = dateStr.split("-")
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
  return `${months[parseInt(m) - 1]} ${y}`
}

export function formatRawCurrency(
  value: number | null | undefined,
  currency: "BRL" | "USD",
): string {
  if (value == null) return "—"
  const symbol = currency === "USD" ? "US$" : "R$"
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return `${symbol} ${(value / 1_000_000).toFixed(2)}M`
  if (abs >= 1_000) return `${symbol} ${(value / 1_000).toFixed(1)}K`
  return `${symbol} ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function pct(value: number | null | undefined): string {
  if (value == null) return "—"
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`
}

export function getVal(op: Operation, key: keyof Pick<Operation,
  "valor_total_brl" | "valor_total_usd" |
  "valor_exterior_pf_brl" | "valor_exterior_pf_usd" |
  "valor_exterior_pj_brl" | "valor_exterior_pj_usd" |
  "valor_exterior_subtotal_brl" | "valor_exterior_subtotal_usd" |
  "valor_sem_ex_pf_brl" | "valor_sem_ex_pf_usd" |
  "valor_sem_ex_pj_brl" | "valor_sem_ex_pj_usd" |
  "valor_sem_ex_subtotal_brl" | "valor_sem_ex_subtotal_usd" |
  "valor_exchanges_brl" | "valor_exchanges_usd"
>): number | null {
  return op[key] as number | null
}

export function currencyKey(base: string, currency: "BRL" | "USD"): string {
  return currency === "USD" ? `${base}_usd` : `${base}_brl`
}

export function topAssets(cryptos: CryptoRecord[], n: number, currency: "BRL" | "USD"): string[] {
  const totals: Record<string, number> = {}
  for (const r of cryptos) {
    const v = currency === "USD" ? r.total_usd : r.total_brl
    if (v != null) totals[r.asset] = (totals[r.asset] ?? 0) + v
  }
  return Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([k]) => k)
}
