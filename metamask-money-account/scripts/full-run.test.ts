// Runs the handler over the vault's whole history in memory and writes out/summary.json.
// Run with `pnpm full-run`. END_BLOCK pins the run so the numbers can be checked against RPC at that block.
import { it } from "vitest";
import { mkdirSync, writeFileSync } from "node:fs";
import { createTestIndexer } from "envio";

const END = Number(process.env.END_BLOCK ?? 122726000);

it("full history", async () => {
  const indexer = createTestIndexer();
  await indexer.process({ chains: { 143: { startBlock: 78633433, endBlock: END } } });
  const json = (v: unknown) => JSON.stringify(v, (_, x) => (typeof x === "bigint" ? x.toString() : x), 2);
  const holders = await indexer.Holder.getAll();
  mkdirSync("out", { recursive: true });
  writeFileSync("out/summary.json", json({
    endBlock: END,
    totals: await indexer.Totals.get("monad"),
    days: (await indexer.DailyStat.getAll()).sort((a, b) => a.id.localeCompare(b.id)),
  }));
  writeFileSync("out/holders.json", json(holders.filter((h) => h.balance > 0n).map((h) => [h.id, h.balance])));
}, 3_600_000);
