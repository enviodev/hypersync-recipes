import { indexer, type SvmOnInstructionHandlerArgs, type Totals } from "envio";
import { interfaceLegs } from "../lib/interfaceLegs.js";

const fields = {
  instruction: ["data", "path", "isInner"],
  transaction: ["signature", "transactionIndex", "success"],
  block: ["time"],
} as const;

type PoolInstruction =
  | "deposit"
  | "transact"
  | "mergeTransact"
  | "ringDeposit"
  | "ringTransact"
  | "ringMergeTransact"
  | "ringAuthorityTransact";

type Kind = "Deposit" | "Withdrawal" | "PrivateTransfer" | "Merge";

const TOTALS_ID = "mainnet";
const emptyTotals: Totals = {
  id: TOTALS_ID,
  registrations: 0,
  deposits: 0,
  withdrawals: 0,
  privateTransfers: 0,
  merges: 0,
  lastSlot: 0,
};

const bump = (t: Totals, kind: Kind, slot: number): Totals => ({
  ...t,
  deposits: t.deposits + (kind === "Deposit" ? 1 : 0),
  withdrawals: t.withdrawals + (kind === "Withdrawal" ? 1 : 0),
  privateTransfers: t.privateTransfers + (kind === "PrivateTransfer" ? 1 : 0),
  merges: t.merges + (kind === "Merge" ? 1 : 0),
  lastSlot: Math.max(t.lastSlot, slot),
});

const poolHandler =
  (classify: (data: Uint8Array) => { kind: Kind; depositLegs: number; withdrawalLegs: number }) =>
  async ({ instruction, context }: SvmOnInstructionHandlerArgs<typeof fields, "ShieldedPool", PoolInstruction>) => {
    if (!instruction.transaction.success) return;
    const { kind, depositLegs, withdrawalLegs } = classify(instruction.data);
    const slot = instruction.block.slot;
    context.PoolAction.set({
      id: `${slot}-${instruction.transaction.transactionIndex}-${instruction.path.join(".")}`,
      kind,
      instruction: instruction.instructionName,
      depositLegs,
      withdrawalLegs,
      isInner: instruction.isInner,
      txSignature: instruction.transaction.signature,
      slot,
      timestamp: instruction.block.time,
    });
    const totals = (await context.Totals.get(TOTALS_ID)) ?? emptyTotals;
    context.Totals.set(bump(totals, kind, slot));
    if (!context.isPreload && context.chain.isRealtime) {
      context.log.info(`${kind} · slot ${slot}`);
    }
  };

const proven = (data: Uint8Array) => {
  const { deposits, withdrawals } = interfaceLegs(data);
  const kind: Kind = withdrawals > 0 ? "Withdrawal" : deposits > 0 ? "Deposit" : "PrivateTransfer";
  return { kind, depositLegs: deposits, withdrawalLegs: withdrawals };
};
const deposit = () => ({ kind: "Deposit" as Kind, depositLegs: 1, withdrawalLegs: 0 });
const merge = () => ({ kind: "Merge" as Kind, depositLegs: 0, withdrawalLegs: 0 });

for (const instruction of ["transact", "ringTransact", "ringAuthorityTransact"] as const) {
  indexer.onInstruction({ program: "ShieldedPool", instruction, fields }, poolHandler(proven));
}
for (const instruction of ["deposit", "ringDeposit"] as const) {
  indexer.onInstruction({ program: "ShieldedPool", instruction, fields }, poolHandler(deposit));
}
for (const instruction of ["mergeTransact", "ringMergeTransact"] as const) {
  indexer.onInstruction({ program: "ShieldedPool", instruction, fields }, poolHandler(merge));
}

indexer.onInstruction(
  {
    program: "UserRegistry",
    instruction: "register",
    fields: { instruction: ["accounts", "path"], transaction: ["signature", "transactionIndex", "success"], block: ["time"] },
  },
  async ({ instruction, context }) => {
    if (!instruction.transaction.success) return;
    const slot = instruction.block.slot;
    context.Registration.set({
      id: `${slot}-${instruction.transaction.transactionIndex}-${instruction.path.join(".")}`,
      userRecord: instruction.accounts.userRecord.address,
      txSignature: instruction.transaction.signature,
      slot,
      timestamp: instruction.block.time,
    });
    const totals = (await context.Totals.get(TOTALS_ID)) ?? emptyTotals;
    context.Totals.set({ ...totals, registrations: totals.registrations + 1, lastSlot: Math.max(totals.lastSlot, slot) });
    if (!context.isPreload && context.chain.isRealtime) {
      context.log.info(`Registration · slot ${slot}`);
    }
  },
);
