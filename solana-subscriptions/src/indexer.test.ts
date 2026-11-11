import { describe, expect, it } from "vitest";
import { createTestIndexer } from "envio";
import { weekStart } from "./lib/week.js";

describe("weekStart", () => {
  it("rounds to Monday 00:00 UTC", () => {
    // Wed 11 Nov 2026 10:27 UTC -> Mon 9 Nov 2026
    expect(weekStart(Date.UTC(2026, 10, 11, 10, 27) / 1000)).toBe(Date.UTC(2026, 10, 9) / 1000);
    expect(weekStart(Date.UTC(2026, 10, 9) / 1000)).toBe(Date.UTC(2026, 10, 9) / 1000);
  });
});

describe("Solana Subscriptions on mainnet", () => {
  it(
    "decodes a real subscription pull from the program's Codama IDL (slot 452364379)",
    async () => {
      const indexer = createTestIndexer();
      await indexer.process({ chains: { 7565164: { startBlock: 452364379, endBlock: 452364379 } } });
      const pulls = await indexer.Pull.getAll();
      expect(pulls).toHaveLength(1);
      expect(pulls[0]).toMatchObject({
        kind: "Subscription",
        mint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        amount: 29_500_000n,
        receiverAta: "G2wv6MCDcaiqhbP4JqP6RB76utwAhhG4BoZ71r58zgk6",
        txSignature: "A5QkCQMaeexGSDPtLxrupcwnSodXiFvq1noPUDCjQdgVNjCWE4AKLq4JhvZpspNtasN1Dz7WwBJa64rH38EThS4",
      });
      const totals = await indexer.Totals.get("mainnet");
      expect(totals).toMatchObject({ pulls: 1, usdcPulls: 1, usdcPulled: 29_500_000n });
    },
    120_000,
  );
});
