import { indexer } from "envio";

const ZERO = "0x0000000000000000000000000000000000000000";

indexer.onEvent({ contract: "MoneyAccountVault", event: "Transfer" }, async ({ event, context }) => {
  const from = event.params.from.toLowerCase();
  const to = event.params.to.toLowerCase();
  const amount = event.params.amount;
  const day = new Date(event.block.timestamp * 1000).toISOString().slice(0, 10);
  const isMint = from === ZERO;
  const isBurn = to === ZERO;

  const totals = await context.Totals.getOrCreate({
    id: "monad",
    wallets: 0,
    holders: 0,
    shareSupply: 0n,
    deposits: 0,
    withdrawals: 0,
    lastBlock: 0,
  });
  let { wallets, holders, shareSupply, deposits, withdrawals } = totals;
  let newWallet = false;

  if (!isMint) {
    const h = await context.Holder.get(from);
    const before = h?.balance ?? 0n;
    const after = before - amount;
    if (before > 0n && after <= 0n) holders -= 1;
    context.Holder.set({
      id: from,
      balance: after,
      firstDepositDay: h?.firstDepositDay,
      firstDepositBlock: h?.firstDepositBlock,
      deposits: h?.deposits ?? 0,
    });
  }

  if (!isBurn) {
    const h = await context.Holder.get(to);
    const before = h?.balance ?? 0n;
    const after = before + amount;
    if (before <= 0n && after > 0n) holders += 1;
    newWallet = isMint && h?.firstDepositDay === undefined;
    if (newWallet) wallets += 1;
    context.Holder.set({
      id: to,
      balance: after,
      firstDepositDay: newWallet ? day : h?.firstDepositDay,
      firstDepositBlock: newWallet ? event.block.number : h?.firstDepositBlock,
      deposits: (h?.deposits ?? 0) + (isMint ? 1 : 0),
    });
  }

  if (isMint) {
    shareSupply += amount;
    deposits += 1;
  }
  if (isBurn) {
    shareSupply -= amount;
    withdrawals += 1;
  }
  context.Totals.set({ id: "monad", wallets, holders, shareSupply, deposits, withdrawals, lastBlock: event.block.number });

  if (isMint || isBurn) {
    const d = await context.DailyStat.getOrCreate({ id: day, newWallets: 0, deposits: 0, sharesMinted: 0n, sharesBurned: 0n });
    context.DailyStat.set({
      ...d,
      newWallets: d.newWallets + (newWallet ? 1 : 0),
      deposits: d.deposits + (isMint ? 1 : 0),
      sharesMinted: d.sharesMinted + (isMint ? amount : 0n),
      sharesBurned: d.sharesBurned + (isBurn ? amount : 0n),
    });
  }
});
