export function IntroTab() {
  return (
    <div className="space-y-8 max-w-4xl">
      {/* Disclaimer */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 px-5 py-4 text-sm text-blue-900">
        <p className="font-semibold mb-1">Data Source</p>
        <p>
          This dashboard uses open data from the{" "}
          <a
            href="https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/criptoativos"
            target="_blank"
            rel="noopener noreferrer"
            className="underline font-medium"
          >
            Receita Federal do Brasil (RFB)
          </a>
          . Data analysis updated in August 2026. USD conversion uses monthly average rates from Bacen.
        </p>
      </div>

      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Updated State of the Crypto Market in Brazil
        </h2>
        <p className="text-muted-foreground text-sm mt-1">Official RFB Report · August 2026</p>
      </div>

      {/* Lead paragraph */}
      <p className="text-base leading-relaxed text-foreground">
        The Brazilian crypto market reached June 2026 as a large, high-velocity, stablecoin-led ecosystem with
        <strong> R$ 559.8 billion</strong> in trailing 12-month reported volume (July 2025 – June 2026) and{" "}
        <strong>R$ 2.012 trillion</strong> in cumulative reported volume since the series began in 2019.
        The last 12 months alone account for <strong>27.8%</strong> of all historical volume in the dataset,
        showing how concentrated recent growth has become.
      </p>

      {/* TL;DR callout */}
      <div className="rounded-xl border border-border bg-zinc-50 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">TL;DR</p>
        <p className="text-sm leading-relaxed">
          Brazil&apos;s market has consolidated into an <strong>institutional and stablecoin-first</strong> structure
          rather than a broad speculative retail surge. After the 2024 purge in low-quality entity counts,
          volume remained near record levels — reaching R$ 58.07 billion in May 2026 and R$ 57.54 billion in June 2026,
          suggesting the market kept the money flow while shedding much of the noisier participation base.
        </p>
      </div>

      <div className="space-y-6">
        {/* Section 1 */}
        <section>
          <h3 className="text-lg font-semibold mb-2">1. Market Volume &amp; Reach</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Total historical reported volume reached <strong className="text-foreground">R$ 2.012 trillion</strong> by
            June 2026. The trailing 12-month period contributed R$ 559.8 billion (27.8% of all-time volume).
            Monthly activity reached record heights in mid-2026: April at R$ 43.52B, May at R$ 58.07B,
            June at R$ 57.54B.
          </p>
        </section>

        {/* Section 2 */}
        <section>
          <h3 className="text-lg font-semibold mb-3">2. Market Share: The Rise of the Dollar</h3>
          <p className="text-sm leading-relaxed text-muted-foreground mb-4">
            Over the trailing 12 months, USDT represented <strong className="text-foreground">74.1%</strong> of all
            reported crypto volume in Brazil. Combined, USDT and USDC made up <strong className="text-foreground">86.4%</strong> of
            reported volume — confirming Brazil operates in practice on dollar-denominated crypto rails.
          </p>
          <div className="rounded-lg border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50">
                  <th className="text-left px-4 py-2 font-medium text-muted-foreground">Asset</th>
                  <th className="text-right px-4 py-2 font-medium text-muted-foreground">12-month share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  { asset: "USDT", share: "74.1%", highlight: true },
                  { asset: "USDC", share: "12.3%", highlight: true },
                  { asset: "BTC", share: "7.3%", highlight: false },
                  { asset: "ETH", share: "2.6%", highlight: false },
                  { asset: "SOL", share: "1.1%", highlight: false },
                ].map(r => (
                  <tr key={r.asset} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2">
                      <span className={`font-mono font-semibold text-xs px-2 py-0.5 rounded ${r.highlight ? "bg-zinc-900 text-white" : "bg-muted text-foreground"}`}>
                        {r.asset}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right font-medium">{r.share}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 3 */}
        <section>
          <h3 className="text-lg font-semibold mb-2">3. The End of the &quot;BET&quot; Era</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Unique active CNPJs peaked at <strong className="text-foreground">421,419</strong> in February 2024
            and stood at <strong className="text-foreground">107,067</strong> by June 2026 — a{" "}
            <strong className="text-foreground">74.6% contraction</strong> from peak. Even with that contraction in
            entity count, transaction value reached historic peaks, implying that higher-volume professional
            participants took a larger share of the market.
          </p>
        </section>

        {/* Section 4 */}
        <section>
          <h3 className="text-lg font-semibold mb-2">4. User Profiles</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Unique CPFs peaked at <strong className="text-foreground">9.21 million</strong> in November 2023
            and ended June 2026 at <strong className="text-foreground">4.67 million</strong>. CNPJs ended at 107,067 —
            far smaller in count but associated with a market whose value remained exceptionally large.
            Corporate and professional flows dominate the volume pie even as retail forms a large active base.
          </p>
        </section>

        {/* Section 5 */}
        <section>
          <h3 className="text-lg font-semibold mb-2">5. What the Data Says</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            The key story is not mass-user expansion in 2026, but <strong className="text-foreground">balance-sheet-scale
            throughput on a narrower and more durable participant base</strong>. Brazil&apos;s market looks
            increasingly like a settlement network centered on synthetic dollars, with BTC preserving a
            secondary role as store of value. The dataset supports a &quot;mature utility market&quot; thesis
            much more than a &quot;retail mania&quot; thesis.
          </p>
        </section>

        {/* Summary metrics */}
        <section className="rounded-xl border border-border bg-muted/30 px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-4">Summary Metrics</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { label: "Total Historical Volume", value: "R$ 2.012 trillion" },
              { label: "Past 12 Months Volume", value: "R$ 559.8 billion (27.8% of all-time)" },
              { label: "Stablecoin Share (USDT + USDC)", value: "86.4%" },
              { label: "BTC / ETH / SOL", value: "7.3% / 2.6% / 1.1%" },
              { label: "Peak Active CNPJs", value: "421,419 (Feb 2024)" },
              { label: "Active CNPJs at Jun 2026", value: "107,067 (−74.6% from peak)" },
              { label: "Peak Active CPFs", value: "9.21 million (Nov 2023)" },
              { label: "Active CPFs at Jun 2026", value: "4.67 million" },
            ].map(m => (
              <div key={m.label} className="flex flex-col gap-0.5">
                <span className="text-xs text-muted-foreground">{m.label}</span>
                <span className="text-sm font-semibold">{m.value}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
