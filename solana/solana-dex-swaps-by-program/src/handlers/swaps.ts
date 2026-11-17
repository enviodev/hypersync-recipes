import { indexer } from "envio";

/** Only these fields are fetched: the call depth and the block time. */
const fields = {
  instruction: ["isInner"],
  block: ["time"],
} as const;

/** Every swap instruction per program, as declared in config.yaml. */
const SWAPS = {
  RaydiumAmmV4: ["swapBaseIn", "swapBaseOut", "swapBaseInV2", "swapBaseOutV2"],
  RaydiumClmm: ["swap", "swapV2", "swapRouterBaseIn"],
  RaydiumCpmm: ["swapBaseInput", "swapBaseOutput"],
  RaydiumLaunchLab: ["buyExactIn", "buyExactOut", "sellExactIn", "sellExactOut"],
  OrcaWhirlpool: ["swap", "swapV2", "twoHopSwap", "twoHopSwapV2"],
  MeteoraDlmm: ["swap", "swap2", "swapExactOut", "swapExactOut2", "swapWithPriceImpact", "swapWithPriceImpact2"],
  MeteoraDammV1: ["swap"],
  MeteoraDammV2: ["swap", "swap2"],
  PumpSwap: ["buy", "sell", "buyExactQuoteIn", "buyV2", "sellV2", "buyExactQuoteInV2", "multiHopSwap"],
  PumpCurve: [
    "buy", "sell", "buyExactSolIn", "buyV2", "sellV2", "buyExactQuoteInV2",
    "buyV3", "sellV3", "buyExactQuoteInV3", "multiHopCurveSwap",
  ],
  Jupiter: [
    "route", "routeV2", "routeWithTokenLedger", "sharedAccountsRoute", "sharedAccountsRouteV2",
    "sharedAccountsRouteWithTokenLedger", "exactOutRoute", "exactOutRouteV2",
    "sharedAccountsExactOutRoute", "sharedAccountsExactOutRouteV2",
    "routeWithAttestation", "sharedAccountsRouteWithAttestation",
  ],
} as const;

const utcDay = (unixSeconds: number) => new Date(unixSeconds * 1000).toISOString().slice(0, 10);

for (const [program, names] of Object.entries(SWAPS)) {
  for (const instruction of names) {
    indexer.onInstruction(
      // The loop widens the literal types, so the pair is asserted back.
      { program, instruction, fields } as never,
      async ({ instruction: ix, context }: any) => {
        const day = utcDay(ix.block.time);
        const id = `${day}-${program}`;
        const row = (await context.DailyVenueSwaps.get(id)) ?? {
          id, day, program, swaps: 0, topLevel: 0, inner: 0,
        };
        context.DailyVenueSwaps.set({
          ...row,
          swaps: row.swaps + 1,
          topLevel: row.topLevel + (ix.isInner ? 0 : 1),
          inner: row.inner + (ix.isInner ? 1 : 0),
        });
      },
    );
  }
}
