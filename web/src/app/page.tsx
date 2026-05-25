import { promises as fs } from "fs"
import path from "path"
import type { Operation, UserRecord, GenderRecord, CryptoRecord, FxRecord } from "@/lib/data"
import { Dashboard } from "@/components/Dashboard"

async function loadJson<T>(file: string): Promise<T> {
  const filePath = path.join(process.cwd(), "public", "data", file)
  const raw = await fs.readFile(filePath, "utf-8")
  return JSON.parse(raw)
}

export default async function Home() {
  const [operations, users, gender, cryptos, fxRates] = await Promise.all([
    loadJson<Operation[]>("operations.json"),
    loadJson<UserRecord[]>("users.json"),
    loadJson<GenderRecord[]>("gender.json"),
    loadJson<CryptoRecord[]>("cryptos.json"),
    loadJson<FxRecord[]>("fx_rates.json"),
  ])

  return (
    <Dashboard
      operations={operations}
      users={users}
      gender={gender}
      cryptos={cryptos}
      fxRates={fxRates}
    />
  )
}
