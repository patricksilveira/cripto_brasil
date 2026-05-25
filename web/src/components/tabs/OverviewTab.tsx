"use client"

import { useMemo } from "react"
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import type { Operation, UserRecord } from "@/lib/data"
import { formatCurrency, formatNumber, formatDate } from "@/lib/data"

type Props = {
  operations: Operation[]
  users: UserRecord[]
  currency: "BRL" | "USD"
}

const CHART_COLORS = {
  total: "#396AB1",
  exchanges: "#3E9651",
  foreign: "#DA7C30",
  domestic: "#6B4C9A",
  cpf: "#396AB1",
  cnpj: "#CC2529",
}

export function OverviewTab({ operations, currency, users }: Props) {
  const volKey = currency === "USD" ? "valor_total_usd" : "valor_total_brl"
  const exchKey = currency === "USD" ? "valor_exchanges_usd" : "valor_exchanges_brl"
  const foreignKey = currency === "USD" ? "valor_exterior_subtotal_usd" : "valor_exterior_subtotal_brl"
  const domesticKey = currency === "USD" ? "valor_sem_ex_subtotal_usd" : "valor_sem_ex_subtotal_brl"
  const symbol = currency === "USD" ? "US$" : "R$"

  const volumeData = useMemo(() =>
    operations.map(op => ({
      date: formatDate(op.date),
      rawDate: op.date,
      total: op[volKey as keyof Operation] as number | null,
      exchanges: op[exchKey as keyof Operation] as number | null,
      foreign: op[foreignKey as keyof Operation] as number | null,
      domestic: op[domesticKey as keyof Operation] as number | null,
    })),
    [operations, volKey, exchKey, foreignKey, domesticKey]
  )

  // YoY chart: group by month, compare years
  const yoyData = useMemo(() => {
    const byYear: Record<number, Record<number, number>> = {}
    for (const op of operations) {
      const v = op[volKey as keyof Operation] as number | null
      if (v == null) continue
      if (!byYear[op.year]) byYear[op.year] = {}
      byYear[op.year][op.month] = v
    }
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return months.map((m, i) => {
      const row: Record<string, unknown> = { month: m }
      for (const [yr, vals] of Object.entries(byYear)) {
        if (vals[i + 1] != null) row[yr] = vals[i + 1]
      }
      return row
    })
  }, [operations, volKey])

  const years = useMemo(() =>
    [...new Set(operations.map(o => o.year))].sort(),
    [operations]
  )

  const yearColors = ["#e4e4e7","#a1a1aa","#71717a","#52525b","#3f3f46","#396AB1","#3E9651"]

  // User growth combo
  const userChartData = useMemo(() =>
    users.map(u => ({
      date: formatDate(u.date),
      cpf: u.cpfs,
      cnpj: u.cnpjs,
      total: u.total,
    })),
    [users]
  )

  const latestOp = operations[operations.length - 1]
  const prevOp = operations[operations.length - 2]
  const latestTotal = latestOp[volKey as keyof Operation] as number | null
  const prevTotal = prevOp?.[volKey as keyof Operation] as number | null
  const pctChange = latestTotal && prevTotal
    ? ((latestTotal - prevTotal) / prevTotal) * 100 : null

  const foreignPct = latestOp.valor_exterior_subtotal_brl && latestOp.valor_total_brl
    ? (latestOp.valor_exterior_subtotal_brl / latestOp.valor_total_brl) * 100 : null

  return (
    <div className="space-y-6">
      {/* Summary row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-zinc-950 text-white border-0">
          <CardContent className="p-5">
            <p className="text-zinc-400 text-xs uppercase tracking-wide mb-1">Latest Volume</p>
            <p className="text-3xl font-bold">{formatCurrency(latestTotal, currency)}</p>
            {pctChange != null && (
              <p className={`text-sm mt-1 ${pctChange >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {pctChange >= 0 ? "▲" : "▼"} {Math.abs(pctChange).toFixed(1)}% vs prev. month
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-muted-foreground text-xs uppercase tracking-wide mb-1">Cross-border share</p>
            <p className="text-3xl font-bold">{foreignPct != null ? foreignPct.toFixed(1) + "%" : "—"}</p>
            <p className="text-muted-foreground text-sm mt-1">of total volume is foreign</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-muted-foreground text-xs uppercase tracking-wide mb-1">Data range</p>
            <p className="text-3xl font-bold">{operations.length} mo</p>
            <p className="text-muted-foreground text-sm mt-1">
              {formatDate(operations[0].date)} → {formatDate(latestOp.date)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Volume over time */}
      <Card>
        <CardHeader>
          <CardTitle>Total Volume Over Time</CardTitle>
          <CardDescription>Monthly total transaction volume in {currency} (millions)</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={volumeData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.total} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={CHART_COLORS.total} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#71717a" }}
                tickLine={false}
                axisLine={false}
                interval={5}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#71717a" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${symbol}${(v / 1000).toFixed(0)}B`}
              />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 12 }}
                formatter={(v: unknown) => [formatCurrency(v as number, currency, false), "Volume"]}
              />
              <Area
                type="monotone"
                dataKey="total"
                stroke={CHART_COLORS.total}
                strokeWidth={2.5}
                fill="url(#colorTotal)"
                dot={false}
                activeDot={{ r: 4 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Volume breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Volume Breakdown</CardTitle>
            <CardDescription>Domestic vs. Foreign vs. Exchanges (millions)</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={volumeData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                <defs>
                  <linearGradient id="gForeign" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.foreign} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.foreign} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gExch" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.exchanges} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.exchanges} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gDom" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.domestic} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.domestic} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} interval={8} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v/1000).toFixed(0)}B`} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 11 }} formatter={(v: unknown) => [formatCurrency(v as number, currency, false)]} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                <Area type="monotone" dataKey="exchanges" name="Exchanges" stroke={CHART_COLORS.exchanges} fill="url(#gExch)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="domestic" name="Domestic" stroke={CHART_COLORS.domestic} fill="url(#gDom)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="foreign" name="Foreign" stroke={CHART_COLORS.foreign} fill="url(#gForeign)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* YoY seasonality */}
        <Card>
          <CardHeader>
            <CardTitle>Year-over-Year Seasonality</CardTitle>
            <CardDescription>Monthly volume by year</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={yoyData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v/1000).toFixed(0)}B`} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 11 }} formatter={(v: unknown) => [formatCurrency(v as number, currency, false)]} />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                {years.map((yr, i) => (
                  <Bar key={yr} dataKey={String(yr)} name={String(yr)} fill={yearColors[i % yearColors.length]} radius={[2, 2, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* User adoption */}
      <Card>
        <CardHeader>
          <CardTitle>User Adoption</CardTitle>
          <CardDescription>Unique CPF (retail) and CNPJ (institutional) entities per month</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={userChartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="gCpf" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.cpf} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={CHART_COLORS.cpf} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} interval={5} />
              <YAxis tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => formatNumber(v)} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 12 }} formatter={(v: unknown) => [formatNumber(v as number, false)]} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
              <Area type="monotone" dataKey="cpf" name="CPF (Retail)" stroke={CHART_COLORS.cpf} fill="url(#gCpf)" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Area type="monotone" dataKey="cnpj" name="CNPJ (Institutional)" stroke={CHART_COLORS.cnpj} fill="none" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
