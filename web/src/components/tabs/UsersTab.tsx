"use client"

import { useMemo } from "react"
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, LineChart, Line, ReferenceLine
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import type { UserRecord } from "@/lib/data"
import { formatNumber, formatDate } from "@/lib/data"

type Props = { users: UserRecord[] }

const CPF_COLOR = "#396AB1"
const CNPJ_COLOR = "#CC2529"
const GROWTH_COLOR = "#3E9651"

export function UsersTab({ users }: Props) {
  const chartData = useMemo(() =>
    users.map(u => ({
      date: formatDate(u.date),
      cpf: u.cpfs,
      cnpj: u.cnpjs,
      total: u.total,
      mom: u.mom_pct,
      cpfMom: u.cpf_mom_pct,
      cnpjMom: u.cnpj_mom_pct,
      ratio: u.cnpjs / u.cpfs,
    })),
    [users]
  )

  const latest = users[users.length - 1]
  const first = users[0]
  const totalGrowthX = first.total > 0 ? (latest.total / first.total).toFixed(1) : "—"

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total Users Now", value: formatNumber(latest.total), sub: `${formatDate(latest.date)}` },
          { label: "CPF (Retail)", value: formatNumber(latest.cpfs), sub: `${((latest.cpfs / latest.total) * 100).toFixed(1)}% of total` },
          { label: "CNPJ (Institutional)", value: formatNumber(latest.cnpjs), sub: `${((latest.cnpjs / latest.total) * 100).toFixed(1)}% of total` },
          { label: "Growth since Aug 2019", value: `${totalGrowthX}×`, sub: `From ${formatNumber(first.total)}` },
        ].map(s => (
          <Card key={s.label}>
            <CardContent className="p-5">
              <p className="text-muted-foreground text-xs uppercase tracking-wide mb-1">{s.label}</p>
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="text-muted-foreground text-xs mt-1">{s.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* CPF vs CNPJ over time */}
      <Card>
        <CardHeader>
          <CardTitle>CPF vs. CNPJ Over Time</CardTitle>
          <CardDescription>Unique entity count per month — retail vs. institutional</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="gCpfU" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CPF_COLOR} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={CPF_COLOR} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gCnpjU" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CNPJ_COLOR} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={CNPJ_COLOR} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} interval={5} />
              <YAxis tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => formatNumber(v)} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 12 }}
                formatter={(v: unknown) => [formatNumber(v as number, false)]}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
              <Area type="monotone" dataKey="cpf" name="CPF (Retail)" stroke={CPF_COLOR} fill="url(#gCpfU)" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Area type="monotone" dataKey="cnpj" name="CNPJ (Institutional)" stroke={CNPJ_COLOR} fill="url(#gCnpjU)" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MoM Growth */}
        <Card>
          <CardHeader>
            <CardTitle>Month-over-Month Growth</CardTitle>
            <CardDescription>Total user base % change</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} interval={8} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v.toFixed(0)}%`} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 11 }} formatter={(v: unknown) => [`${(v as number).toFixed(2)}%`, "Growth"]} />
                <ReferenceLine y={0} stroke="#e4e4e7" />
                <Bar
                  dataKey="mom"
                  name="MoM %"
                  radius={[2, 2, 0, 0]}
                  fill={GROWTH_COLOR}
                  // Color negative bars red
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* CNPJ/CPF ratio */}
        <Card>
          <CardHeader>
            <CardTitle>CNPJ / CPF Ratio</CardTitle>
            <CardDescription>Institutional vs. retail concentration over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} interval={8} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v * 100).toFixed(2)}%`} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 11 }} formatter={(v: unknown) => [`${((v as number) * 100).toFixed(3)}%`, "Ratio"]} />
                <Line type="monotone" dataKey="ratio" name="CNPJ/CPF" stroke={CNPJ_COLOR} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
