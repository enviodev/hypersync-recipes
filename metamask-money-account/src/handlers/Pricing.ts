import { indexer } from "envio";

const VAULT = "0x1c8a336051d2024e318a229d01f9f6cf96efd316";
const RAY = 10n ** 27n;

// Aave's rayDiv, rounding half up: turns an underlying amount into a scaled balance at a liquidity index
const rayDiv = (a: bigint, index: bigint) => (a * RAY + index / 2n) / index;

// Share price: the accountant emits the new rate on every deposit and update, so the latest event is the price
indexer.onEvent({ contract: "MoneyAccountAccountant", event: "ExchangeRateUpdated" }, async ({ event, context }) => {
  context.SharePrice.set({ id: "monad", rate: event.params.newRate, block: event.block.number });
});

// Aave position: rebuild scaled aMonmUSD balances. Multiply by the latest liquidity index for the balance in mUSD.
async function applyScaled(context: any, user: string, delta: bigint, index: bigint, block: number) {
  const p = await context.AavePosition.getOrCreate({
    id: "monad", vaultScaled: 0n, totalScaled: 0n, liquidityIndex: RAY, block: 0,
  });
  context.AavePosition.set({
    ...p,
    vaultScaled: p.vaultScaled + (user.toLowerCase() === VAULT ? delta : 0n),
    totalScaled: p.totalScaled + delta,
    liquidityIndex: index,
    block,
  });
}

// Mint carries value = amount + interest for a supply, or interest - amount for a withdrawal smaller than the interest
indexer.onEvent({ contract: "AaveMusdAToken", event: "Mint" }, async ({ event, context }) => {
  const { onBehalfOf, value, balanceIncrease, index } = event.params;
  const amount = value - balanceIncrease;
  const scaled = amount >= 0n ? rayDiv(amount, index) : -rayDiv(-amount, index);
  await applyScaled(context, onBehalfOf, scaled, index, event.block.number);
});

// Burn carries value = amount - interest
indexer.onEvent({ contract: "AaveMusdAToken", event: "Burn" }, async ({ event, context }) => {
  const { from, value, balanceIncrease, index } = event.params;
  await applyScaled(context, from, -rayDiv(value + balanceIncrease, index), index, event.block.number);
});

// BalanceTransfer carries the scaled amount moved between two holders, so the total doesn't change
indexer.onEvent({ contract: "AaveMusdAToken", event: "BalanceTransfer" }, async ({ event, context }) => {
  const { from, to, value, index } = event.params;
  const p = await context.AavePosition.getOrCreate({
    id: "monad", vaultScaled: 0n, totalScaled: 0n, liquidityIndex: RAY, block: 0,
  });
  let v = p.vaultScaled;
  if (from.toLowerCase() === VAULT) v -= value;
  if (to.toLowerCase() === VAULT) v += value;
  context.AavePosition.set({ ...p, vaultScaled: v, liquidityIndex: index, block: event.block.number });
});
