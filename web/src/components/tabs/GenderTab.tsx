"use client"

import { useMemo } from "react"
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import type { GenderRecord } from "@/lib/data"
import { formatDate } from "@/lib/data"

type Props = {
  gender: GenderRecord[]
  latestGender: GenderRecord
}

const FEM_COLOR = "#CC2529"
const MASC_COLOR = "#396AB1"

export function GenderTab({ gender, latestGender }: Props) {
  const chartData = useMemo(() =>
    gender.map(g => ({
      date: formatDate(g.date),
      femCount: g.pct_num_fem,
      mascCount: g.pct_num_masc,
      femVal: g.pct_val_fem,
      mascVal: g.pct_val_masc,
    })),
    [gender]
  )

  const pieCount = [
    { name: "Female", value: latestGender.pct_num_fem },
    { name: "Male", value: latestGender.pct_num_masc },
  ]
  const pieVal = [
    { name: "Female", value: latestGender.pct_val_fem },
    { name: "Male", value: latestGender.pct_val_masc },
  ]

  const renderCustomLabel = ({ name, value }: { name?: string; value?: number }) =>
    `${name ?? ""}: ${value ?? 0}%`

  return (
    <div className="space-y-6">
      {/* Latest snapshot */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Female — Ops Count", value: `${latestGender.pct_num_fem}%`, color: FEM_COLOR },
          { label: "Male — Ops Count", value: `${latestGender.pct_num_masc}%`, color: MASC_COLOR },
          { label: "Female — Volume Share", value: `${latestGender.pct_val_fem}%`, color: FEM_COLOR },
          { label: "Male — Volume Share", value: `${latestGender.pct_val_masc}%`, color: MASC_COLOR },
        ].map(s => (
          <Card key={s.label}>
            <CardContent className="p-5">
              <div className="w-2 h-2 rounded-full mb-2" style={{ backgroundColor: s.color }} />
              <p className="text-muted-foreground text-xs uppercase tracking-wide mb-1">{s.label}</p>
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="text-muted-foreground text-xs mt-1">{formatDate(latestGender.date)}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pie charts side by side */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Operations Count Share</CardTitle>
            <CardDescription>Latest month</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <PieChart width={260} height={220}>
              <Pie data={pieCount} cx={130} cy={100} outerRadius={85} dataKey="value" label={renderCustomLabel} labelLine={false}>
                <Cell fill={FEM_COLOR} />
                <Cell fill={MASC_COLOR} />
              </Pie>
              <Tooltip formatter={(v: unknown) => [`${v}%`]} />
            </PieChart>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Volume Value Share</CardTitle>
            <CardDescription>Latest month</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <PieChart width={260} height={220}>
              <Pie data={pieVal} cx={130} cy={100} outerRadius={85} dataKey="value" label={renderCustomLabel} labelLine={false}>
                <Cell fill={FEM_COLOR} />
                <Cell fill={MASC_COLOR} />
              </Pie>
              <Tooltip formatter={(v: unknown) => [`${v}%`]} />
            </PieChart>
          </CardContent>
        </Card>
      </div>

      {/* Stacked 100% bars over time — count */}
      <Card>
        <CardHeader>
          <CardTitle>Operations by Gender Over Time</CardTitle>
          <CardDescription>Percentage of total operation count per month</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} stackOffset="expand" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} interval={5} />
              <YAxis tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 12 }}
                formatter={(v: unknown) => [`${(v as number).toFixed(1)}%`]}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
              <Bar dataKey="femCount" name="Female" stackId="a" fill={FEM_COLOR} />
              <Bar dataKey="mascCount" name="Male" stackId="a" fill={MASC_COLOR} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Trend lines */}
      <Card>
        <CardHeader>
          <CardTitle>Female Participation Trend</CardTitle>
          <CardDescription>% of operations by count and value</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="gFemC" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={FEM_COLOR} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={FEM_COLOR} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gFemV" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#DA7C30" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#DA7C30" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} interval={5} />
              <YAxis tick={{ fontSize: 11, fill: "#71717a" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} domain={[0, 25]} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", fontSize: 12 }} formatter={(v: unknown) => [`${(v as number).toFixed(2)}%`]} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
              <Area type="monotone" dataKey="femCount" name="Female — Count %" stroke={FEM_COLOR} fill="url(#gFemC)" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Area type="monotone" dataKey="femVal" name="Female — Value %" stroke="#DA7C30" fill="url(#gFemV)" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
