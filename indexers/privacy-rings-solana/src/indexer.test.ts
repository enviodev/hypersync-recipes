import { describe, expect, it } from "vitest";
import { createTestIndexer } from "envio";
import { interfaceLegs } from "./lib/interfaceLegs.js";

const hex = (s: string) => Uint8Array.from(Buffer.from(s, "hex"));

describe("interfaceLegs", () => {
  it("reads a real mainnet withdrawal leg (slot 463208369)", () => {
    // tag 0x10 | expiry | tx_viewing_pk | salt | 1 leg: SolWithdrawal
    const data = hex(
      "10ffffffffffffffff04bc3481f6749634a2ecbd1689260989becb55c68b8a808d177c11fba3723f575672c1495fa7d97b8bb8ce8d5af73b45b8010180841e00000000000000",
    );
    expect(interfaceLegs(data)).toEqual({ deposits: 0, withdrawals: 1 });
  });

  it("treats a transact with no legs as a private transfer", () => {
    const data = new Uint8Array(1 + 8 + 33 + 16 + 1);
    data[0] = 0x10;
    expect(interfaceLegs(data)).toEqual({ deposits: 0, withdrawals: 0 });
  });
});

describe("Privacy Rings on mainnet", () => {
  it(
    "indexes registrations, a deposit, a private transfer and a withdrawal from real slots",
    async () => {
      const indexer = createTestIndexer();
      await indexer.process({
        chains: { 7565164: { startBlock: 463205308, endBlock: 463208400 } },
      });
      const totals = await indexer.Totals.get("mainnet");
      expect(totals).toMatchObject({
        registrations: 2,
        deposits: 1,
        privateTransfers: 1,
        withdrawals: 1,
        merges: 0,
      });
    },
    120_000,
  );
});
