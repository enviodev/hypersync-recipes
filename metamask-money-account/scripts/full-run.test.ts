// Runs the handlers over the vault's whole history in memory and writes out/summary.json and out/holders.json.
// Run with `pnpm full-run`. END_BLOCK pins the run so the numbers can be checked against RPC at that block.
import { it } from "vitest";
import { mkdirSync, writeFileSync } from "node:fs";
import { createTestIndexer } from "envio";

const END = Number(process.env.END_BLOCK ?? 122726000);
const RAY = 10n ** 27n;
const units = (v: bigint) => Number(v) / 1e6; // shares, mUSD and aMonmUSD all have 6 decimals

it("full history", async () => {
  const indexer = createTestIndexer();
  await indexer.process({ chains: { 143: { startBlock: 78633433, endBlock: END } } });
  const json = (v: unknown) => JSON.stringify(v, (_, x) => (typeof x === "bigint" ? x.toString() : x), 2);
  const holders = (await indexer.Holder.getAll()).filter((h) => h.balance > 0n);
  const totals = await indexer.Totals.get("monad");
  const price = await indexer.SharePrice.get("monad");
  const aave = await indexer.AavePosition.get("monad");
  const rate = price?.rate ?? 0n;
  const index = aave?.liquidityIndex ?? RAY;
  // Values derived from the indexed events: vault value at the share price, $1+ holders, and the Aave position
  const derived = {
    sharePrice: units(rate),
    sharePriceBlock: price?.block,
    vaultValueMusd: units(((totals?.shareSupply ?? 0n) * rate) / 10n ** 6n),
    holdersAtLeastOneDollar: holders.filter((h) => (h.balance * rate) / 10n ** 6n >= 10n ** 6n).length,
    aaveVaultMusd: units(((aave?.vaultScaled ?? 0n) * index) / RAY),
    aaveReserveMusd: units(((aave?.totalScaled ?? 0n) * index) / RAY),
    aaveIndexBlock: aave?.block,
  };
  mkdirSync("out", { recursive: true });
  writeFileSync("out/summary.json", json({
    endBlock: END,
    totals,
    derived,
    days: (await indexer.DailyStat.getAll()).sort((a, b) => a.id.localeCompare(b.id)),
  }));
  writeFileSync("out/holders.json", json(holders.map((h) => [h.id, h.balance])));
  console.log(json({ endBlock: END, totals, derived }));
}, 3_600_000);
