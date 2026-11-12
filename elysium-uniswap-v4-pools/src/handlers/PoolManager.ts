import { indexer } from "envio";

const NATIVE = "0x0000000000000000000000000000000000000000";

indexer.onEvent({ contract: "PoolManager", event: "Initialize" }, async ({ event, context }) => {
  const { id, currency0, currency1, fee, tickSpacing, hooks } = event.params;
  const ts = event.block.timestamp;
  const day = new Date(ts * 1000).toISOString().slice(0, 10);
  const pairedWithHype = currency0.toLowerCase() === NATIVE;
  const hasHook = hooks.toLowerCase() !== NATIVE;

  context.Pool.set({
    id,
    currency0,
    currency1,
    pairedWithHype,
    fee: Number(fee),
    tickSpacing: Number(tickSpacing),
    hooks,
    day,
    blockNumber: event.block.number,
    timestamp: ts,
  });

  const totals = await context.Totals.getOrCreate({
    id: "elysium",
    pools: 0,
    poolsPairedWithHype: 0,
    poolsWithHooks: 0,
    lastBlock: 0,
  });
  context.Totals.set({
    ...totals,
    pools: totals.pools + 1,
    poolsPairedWithHype: totals.poolsPairedWithHype + (pairedWithHype ? 1 : 0),
    poolsWithHooks: totals.poolsWithHooks + (hasHook ? 1 : 0),
    lastBlock: event.block.number,
  });

  const daily = await context.DailyPools.getOrCreate({ id: day, pools: 0 });
  context.DailyPools.set({ ...daily, pools: daily.pools + 1 });

  const hook = await context.HookPools.getOrCreate({ id: hooks.toLowerCase(), pools: 0 });
  context.HookPools.set({ ...hook, pools: hook.pools + 1 });
});
