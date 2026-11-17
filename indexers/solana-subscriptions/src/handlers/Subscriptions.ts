import { indexer, type Totals, type WeeklyStat } from "envio";
import { weekStart } from "../lib/week.js";

const USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const TOTALS_ID = "mainnet";

const emptyTotals: Totals = {
  id: TOTALS_ID,
  plans: 0,
  subscriptions: 0,
  cancellations: 0,
  allowances: 0,
  pulls: 0,
  usdcPulls: 0,
  usdcPulled: 0n,
  lastSlot: 0,
};

const tx = { transaction: ["signature", "transactionIndex", "success"], block: ["time"] } as const;
const idOf = (i: { block: { slot: number }; transaction: { transactionIndex: number }; path: readonly number[] }) =>
  `${i.block.slot}-${i.transaction.transactionIndex}-${i.path.join(".")}`;

const totals = async (context: any): Promise<Totals> => (await context.Totals.get(TOTALS_ID)) ?? emptyTotals;
const week = async (context: any, ts: number): Promise<WeeklyStat> => {
  const start = weekStart(ts);
  return (
    (await context.WeeklyStat.get(String(start))) ?? {
      id: String(start),
      weekStart: start,
      pulls: 0,
      usdcPulled: 0n,
      subscriptions: 0,
    }
  );
};

indexer.onInstruction(
  { program: "Subscriptions", instruction: "createPlan", fields: { instruction: ["args", "accounts", "path"], ...tx } },
  async ({ instruction, context }) => {
    if (!instruction.transaction.success) return;
    const { args, accounts } = instruction;
    context.Plan.set({
      id: accounts.planPda.address,
      merchant: accounts.merchant.address,
      mint: args.mint,
      amount: args.amount,
      periodHours: args.periodHours,
      subscriptions: 0,
      pulls: 0,
      pulled: 0n,
      createdSlot: instruction.block.slot,
    });
    const t = await totals(context);
    context.Totals.set({ ...t, plans: t.plans + 1, lastSlot: Math.max(t.lastSlot, instruction.block.slot) });
  },
);

indexer.onInstruction(
  { program: "Subscriptions", instruction: "subscribe", fields: { instruction: ["args", "accounts", "path"], ...tx } },
  async ({ instruction, context }) => {
    if (!instruction.transaction.success) return;
    const { subscribeData: d } = instruction.args;
    const a = instruction.accounts;
    const slot = instruction.block.slot;
    context.Subscription.set({
      id: idOf(instruction),
      subscriber: a.subscriber.address,
      plan: a.planPda.address,
      merchant: a.merchant.address,
      txSignature: instruction.transaction.signature,
      slot,
      timestamp: instruction.block.time,
    });
    const plan = (await context.Plan.get(a.planPda.address)) ?? {
      id: a.planPda.address,
      merchant: a.merchant.address,
      mint: d.expectedMint,
      amount: d.expectedAmount,
      periodHours: d.expectedPeriodHours,
      subscriptions: 0,
      pulls: 0,
      pulled: 0n,
      createdSlot: slot,
    };
    context.Plan.set({ ...plan, subscriptions: plan.subscriptions + 1 });
    const w = await week(context, instruction.block.time);
    context.WeeklyStat.set({ ...w, subscriptions: w.subscriptions + 1 });
    const t = await totals(context);
    context.Totals.set({ ...t, subscriptions: t.subscriptions + 1, lastSlot: Math.max(t.lastSlot, slot) });
  },
);

for (const instruction of ["cancelSubscription", "cancelSubscriptionNow"] as const) {
  indexer.onInstruction({ program: "Subscriptions", instruction, fields: tx }, async ({ instruction, context }) => {
    if (!instruction.transaction.success) return;
    const t = await totals(context);
    context.Totals.set({ ...t, cancellations: t.cancellations + 1 });
  });
}

for (const instruction of ["createFixedDelegation", "createRecurringDelegation"] as const) {
  indexer.onInstruction({ program: "Subscriptions", instruction, fields: tx }, async ({ instruction, context }) => {
    if (!instruction.transaction.success) return;
    const t = await totals(context);
    context.Totals.set({ ...t, allowances: t.allowances + 1 });
  });
}

const pulls = [
  ["transferSubscription", "Subscription"],
  ["transferRecurring", "Recurring"],
  ["transferFixed", "Fixed"],
] as const;

for (const [instruction, kind] of pulls) {
  indexer.onInstruction(
    {
      program: "Subscriptions",
      instruction,
      fields: { instruction: ["args", "accounts", "path", "isInner"], ...tx },
    },
    async ({ instruction, context }) => {
      if (!instruction.transaction.success) return;
      const { amount, delegator, mint } = instruction.args.transferData;
      const a: any = instruction.accounts;
      const slot = instruction.block.slot;
      const plan: string | undefined = a.planPda?.address;
      context.Pull.set({
        id: idOf(instruction),
        kind,
        delegator,
        mint,
        amount,
        receiverAta: a.receiverAta.address,
        caller: (a.caller ?? a.delegatee).address,
        plan,
        isInner: instruction.isInner,
        txSignature: instruction.transaction.signature,
        slot,
        timestamp: instruction.block.time,
      });
      const isUsdc = mint === USDC;
      if (plan) {
        const p = await context.Plan.get(plan);
        if (p) context.Plan.set({ ...p, pulls: p.pulls + 1, pulled: p.pulled + amount });
      }
      if (isUsdc) {
        const w = await week(context, instruction.block.time);
        context.WeeklyStat.set({ ...w, pulls: w.pulls + 1, usdcPulled: w.usdcPulled + amount });
      }
      const t = await totals(context);
      context.Totals.set({
        ...t,
        pulls: t.pulls + 1,
        usdcPulls: t.usdcPulls + (isUsdc ? 1 : 0),
        usdcPulled: t.usdcPulled + (isUsdc ? amount : 0n),
        lastSlot: Math.max(t.lastSlot, slot),
      });
      if (!context.isPreload && context.chain.isRealtime) {
        context.log.info(`${kind.padEnd(12)} ${(Number(amount) / 1e6).toFixed(2).padStart(10)} ${isUsdc ? "USDC" : mint.slice(0, 6)}  slot ${slot}`);
      }
    },
  );
}
