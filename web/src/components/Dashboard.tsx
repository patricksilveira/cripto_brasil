"use client"

import { useState, useMemo } from "react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { Operation, UserRecord, GenderRecord, CryptoRecord, FxRecord } from "@/lib/data"
import { formatCurrency, formatNumber, formatDate } from "@/lib/data"
import { OverviewTab } from "@/components/tabs/OverviewTab"
import { UsersTab } from "@/components/tabs/UsersTab"
import { GenderTab } from "@/components/tabs/GenderTab"
import { CryptosTab } from "@/components/tabs/CryptosTab"

type Props = {
  operations: Operation[]
  users: UserRecord[]
  gender: GenderRecord[]
  cryptos: CryptoRecord[]
  fxRates: FxRecord[]
}

export function Dashboard({ operations, users, gender, cryptos, fxRates }: Props) {
  const [currency, setCurrency] = useState<"BRL" | "USD">("BRL")

  const latest = operations[operations.length - 1]
  const prev = operations[operations.length - 2]
  const latestUsers = users[users.length - 1]
  const latestGender = gender[gender.length - 1]

  const totalVolumeCurrent = currency === "USD" ? latest.valor_total_usd : latest.valor_total_brl
  const totalVolumePrev = currency === "USD" ? prev?.valor_total_usd : prev?.valor_total_brl
  const volumeChange = totalVolumeCurrent && totalVolumePrev
    ? ((totalVolumeCurrent - totalVolumePrev) / totalVolumePrev) * 100
    : null

  const kpis = useMemo(() => [
    {
      label: "Total Volume",
      sublabel: `${formatDate(latest.date)}`,
      value: formatCurrency(totalVolumeCurrent, currency),
      change: volumeChange,
      note: "millions BRL (RFB)",
    },
    {
      label: "Unique Users",
      sublabel: `${formatDate(latest.date)}`,
      value: formatNumber(latestUsers.total),
      change: latestUsers.mom_pct,
      note: "CPF + CNPJ",
    },
    {
      label: "Retail (CPF)",
      sublabel: `${formatDate(latest.date)}`,
      value: formatNumber(latestUsers.cpfs),
      change: latestUsers.cpf_mom_pct,
      note: "Individual traders",
    },
    {
      label: "Institutional (CNPJ)",
      sublabel: `${formatDate(latest.date)}`,
      value: formatNumber(latestUsers.cnpjs),
      change: latestUsers.cnpj_mom_pct,
      note: "Companies / funds",
    },
  ], [currency, latest, latestUsers, totalVolumeCurrent, volumeChange])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-md bg-zinc-900 flex items-center justify-center">
              <span className="text-white text-xs font-bold">₿</span>
            </div>
            <div>
              <span className="font-semibold text-sm text-foreground">CriptoBrasil</span>
              <span className="text-muted-foreground text-xs ml-2 hidden sm:inline">Receita Federal Open Data</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="text-xs hidden sm:flex">
              Updated {formatDate(latest.date)}
            </Badge>
            <div className="flex rounded-md border border-border overflow-hidden">
              <Button
                variant={currency === "BRL" ? "default" : "ghost"}
                size="sm"
                className="rounded-none h-8 px-3 text-xs"
                onClick={() => setCurrency("BRL")}
              >
                BRL
              </Button>
              <Button
                variant={currency === "USD" ? "default" : "ghost"}
                size="sm"
                className="rounded-none h-8 px-3 text-xs border-l border-border"
                onClick={() => setCurrency("USD")}
              >
                USD
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Brazil Crypto Market
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Monthly data from the Federal Revenue Service (RFB) · {operations.length} months of history · Aug 2019 – {formatDate(latest.date)}
          </p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map((k) => (
            <div
              key={k.label}
              className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-2"
            >
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{k.label}</p>
              <p className="text-2xl font-bold text-foreground leading-none">{k.value}</p>
              <div className="flex items-center gap-2">
                {k.change != null && (
                  <span className={`text-xs font-medium ${k.change >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                    {k.change >= 0 ? "↑" : "↓"} {Math.abs(k.change).toFixed(1)}% MoM
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground">{k.note}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="h-10">
            <TabsTrigger value="overview" className="text-sm">Overview</TabsTrigger>
            <TabsTrigger value="users" className="text-sm">Users</TabsTrigger>
            <TabsTrigger value="gender" className="text-sm">Gender</TabsTrigger>
            <TabsTrigger value="cryptos" className="text-sm">Cryptos</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab operations={operations} users={users} currency={currency} />
          </TabsContent>
          <TabsContent value="users">
            <UsersTab users={users} />
          </TabsContent>
          <TabsContent value="gender">
            <GenderTab gender={gender} latestGender={latestGender} />
          </TabsContent>
          <TabsContent value="cryptos">
            <CryptosTab cryptos={cryptos} currency={currency} />
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <footer className="border-t border-border pt-6 pb-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground max-w-lg">
              Data sourced from <strong>Receita Federal do Brasil (RFB)</strong> open data on crypto asset operations.
              USD conversion uses monthly average rates from <strong>Bacen</strong> (Banco Central do Brasil).
              Values in millions of BRL unless otherwise noted. Not financial advice.
            </p>
            <p className="text-xs text-muted-foreground whitespace-nowrap">
              Last data: {formatDate(latest.date)}
            </p>
          </div>
        </footer>
      </main>
    </div>
  )
}
