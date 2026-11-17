// Runs the handlers over the program's whole mainnet history in memory and writes
// out/summary.json. Not part of `pnpm test`: run with `pnpm full-run`.
import { it } from "vitest";
import { mkdirSync, writeFileSync } from "node:fs";
import { createTestIndexer } from "envio";

const END = Number(process.env.END_SLOT ?? 468090000);

it("full history", async () => {
  const indexer = createTestIndexer();
  await indexer.process({ chains: { 7565164: { startBlock: 416950000, endBlock: END } } });
  const json = (v: unknown) => JSON.stringify(v, (_, x) => (typeof x === "bigint" ? x.toString() : x), 2);
  mkdirSync("out", { recursive: true });
  writeFileSync("out/summary.json", json({
    endSlot: END,
    totals: await indexer.Totals.get("mainnet"),
    weeks: (await indexer.WeeklyStat.getAll()).sort((a, b) => a.weekStart - b.weekStart),
    plans: await indexer.Plan.getAll(),
  }));
  writeFileSync("out/pulls.json", json(await indexer.Pull.getAll()));
  writeFileSync("out/subscriptions.json", json(await indexer.Subscription.getAll()));
}, 3_600_000);
