import { indexer } from "envio";

// Elysium Inbox on HyperEVM, from elysium.kinetiq.xyz/docs/contract-addresses
const INBOX = "0xce59f8b65ad41c9dae4c07a0571a39824bd92cff";
// Arbitrum Nitro message kind for a native deposit (L1MessageType_ethDeposit). On Elysium the native token is HYPE.
const NATIVE_DEPOSIT = 12n;

indexer.onEvent({ contract: "Bridge", event: "MessageDelivered" }, async ({ event, context }) => {
  const { kind, sender } = event.params;
  const day = new Date(event.block.timestamp * 1000).toISOString().slice(0, 10);

  const kindId = kind.toString();
  const k = await context.MessageKind.getOrCreate({ id: kindId, messages: 0 });
  context.MessageKind.set({ ...k, messages: k.messages + 1 });

  const totals = await context.Totals.getOrCreate({
    id: "elysium",
    messages: 0,
    hypeDeposits: 0,
    depositors: 0,
    hypeDepositedDirect: 0n,
    lastBlock: 0,
  });

  if (BigInt(kind) !== NATIVE_DEPOSIT) {
    context.Totals.set({ ...totals, messages: totals.messages + 1, lastBlock: event.block.number });
    return;
  }

  const wallet = sender.toLowerCase();
  const existing = await context.Depositor.get(wallet);
  const isNew = existing === undefined;
  context.Depositor.set({
    id: wallet,
    deposits: (existing?.deposits ?? 0) + 1,
    firstDay: existing?.firstDay ?? day,
  });

  const direct = event.transaction.to?.toLowerCase() === INBOX ? event.transaction.value : 0n;

  context.Totals.set({
    ...totals,
    messages: totals.messages + 1,
    hypeDeposits: totals.hypeDeposits + 1,
    depositors: totals.depositors + (isNew ? 1 : 0),
    hypeDepositedDirect: totals.hypeDepositedDirect + direct,
    lastBlock: event.block.number,
  });

  const daily = await context.DailyDeposits.getOrCreate({ id: day, deposits: 0, newDepositors: 0 });
  context.DailyDeposits.set({
    ...daily,
    deposits: daily.deposits + 1,
    newDepositors: daily.newDepositors + (isNew ? 1 : 0),
  });
});
