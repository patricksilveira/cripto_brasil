"use client"

import { useState, useMemo } from "react"
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import type { CryptoRecord } from "@/lib/data"
import { formatCurrency, formatRawCurrency, formatNumber, formatDate, topAssets } from "@/lib/data"

type Props = {
  cryptos: CryptoRecord[]
  currency: "BRL" | "USD"
}

const COLORS = ["#396AB1","#DA7C30","#3E9651","#CC2529","#6B4C9A","#535154","#922428","#948B3D","#2563EB","#0891B2"]

export function CryptosTab({ cryptos, currency }: Props) {
  const [topN, setTopN] = useState(10)

  const top = useMemo(() => topAssets(cryptos, topN, currency), [cryptos, topN, currency])

  // All-time totals for top assets
  const totals = useMemo(() => {
    const m: Record<string, { totalVol: number; totalOps: number; avgAvg: number; count: number }> = {}
    for (const r of cryptos) {
      if (!top.includes(r.asset)) continue
      if (!m[r.asset]) m[r.asset] = { totalVol: 0, totalOps: 0, avgAvg: 0, count: 0 }
      const v = currency === "USD" ? r.total_usd : r.total_brl
      if (v != null) m[r.asset].totalVol += v
      if (r.num_ops != null) m[r.asset].totalOps += r.num_ops
      const avg = currency === "USD" ? r.avg_usd : r.avg_brl
      if (avg != null) { m[r.asset].avgAvg += avg; m[r.asset].count++ }
    }
    return top.map(asset => ({
      asset,
      totalVol: m[asset]?.totalVol ?? 0,
      totalOps: m[asset]?.totalOps ?? 0,
      avgTicket: m[asset]?.count ? m[asset].avgAvg / m[asset].count : 0,
    }))
  }, [cryptos, top, currency])

  // Bar chart data
  const barData = totals.map(t => ({
    asset: t.asset,
    volume: t.totalVol,
  }))

  // Timeline for top 5
  const top5 = top.slice(0, 5)
  const timelineData = useMemo(() => {
    const dateMap: Record<string, Record<string, number>> = {}
    for (const r of cryptos) {
      if (!top5.includes(r.asset)) continue
      if (!dateMap[r.date]) dateMap[r.date] = {}
      const v = currency === "USD" ? r.total_usd : r.total_brl
      if (v != null) dateMap[r.date][r.asset] = v
    }
    return Object.entries(dateMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, vals]) => ({ date: formatDate(date), ...vals }))
  }, [cryptos, top5, currency])

  return (
    <div className="space-y-6">
      {/* Top N selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">Show top</span>
        {[5, 10, 15, 20].map(n => (
          <button
            key={n}
            onClick={() => setTopN(n)}
            className={`px-3 py-1 text-sm rounded-md border transition-colors ${
              topN === n
                ? "bg-zinc-900 text-white border-zinc-900"
                : "border-border hover:bg-muted"
            }`}
          >
            {n}
          </button>
        ))}
        <span className="text-sm text-muted-foreground">assets by all-time volume</span>
      </div>

      {/* Volume bar chart */}
      <Card>
        <CardHeader>
          <CardTitle>All-Time Volume by Asset</CardTitle>
          <CardDescription>Cumulative {currency} volume across all months</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={barData} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => formatCurrency(v, currency)} />
              <YAxis type="category" dataKey="asset" tick={{ fontSize: 12, fill: "#18181b", fontWeight: 600 }} tickLine={false} axisLine={false} width={55} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 12 }}
                formatter={(v: unknown) => [formatCurrency(v as number, currency, false), "Volume"]}
              />
              <Bar dataKey="volume" radius={[0, 4, 4, 0]}>
                {barData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top 5 timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Top 5 Assets — Monthly Volume</CardTitle>
          <CardDescription>Historical trend of leading crypto assets</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timelineData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} interval={5} />
              <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => formatCurrency(v, currency)} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 11 }} formatter={(v: unknown) => [formatCurrency(v as number, currency, false)]} />
              <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
              {top5.map((asset, i) => (
                <Line key={asset} type="monotone" dataKey={asset} stroke={COLORS[i]} strokeWidth={2} dot={false} activeDot={{ r: 4 }} connectNulls />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Asset Summary Table</CardTitle>
          <CardDescription>Ranked by all-time volume · Avg. Ticket in raw {currency}</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8">#</TableHead>
                <TableHead>Asset</TableHead>
                <TableHead className="text-right">Total Volume</TableHead>
                <TableHead className="text-right">Total Ops</TableHead>
                <TableHead className="text-right">Avg. Ticket</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {totals.map((row, i) => (
                <TableRow key={row.asset}>
                  <TableCell className="text-muted-foreground text-xs">{i + 1}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <Badge variant="secondary" className="font-mono text-xs">{row.asset}</Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(row.totalVol, currency, true)}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{formatNumber(row.totalOps)}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{formatRawCurrency(row.avgTicket, currency)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

