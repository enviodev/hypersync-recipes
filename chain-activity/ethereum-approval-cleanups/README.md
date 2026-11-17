# Ethereum approval cleanups

Counts every ERC-20 approval that wallets revoked on Ethereum over the last 30 days with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then splits the revokes into real cleanups and resets.

A reset is a revoke that the same wallet follows with a fresh approval to the same spender, on the same token, within an hour. USDT is the classic case, because it makes you set an allowance to zero before you can change it. Take the resets out and what is left is people cleaning up approvals they no longer want.

These are the numbers behind Envio's post on approval cleanups.

Revoke.cash uses HyperSync for this. [Revoke.cash](https://revoke.cash) helps people review and revoke token approvals on more than 100 networks, and their [Dependency Spotlight on Envio](https://revoke.cash/blog/2025/dependency-spotlight-envio) explains that they look at a user's entire transaction history to work out the current state of their approvals, and use HyperSync to query it.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The scripts have no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It scans about 1.5M transactions and takes around five minutes. `DAYS=7 python script.py` gives a shorter window, and `END_DAY=2026-11-12` pins the end date so you can reproduce the run below.

## What it prints

```
Direct ERC-20 approve() calls, 13 Oct to 11 Nov 2026 UTC (30 days)

Ethereum  blocks 26,179,842 to 26,395,133  (1,539,467 approve() txs scanned in 327s)
  revokes    155,216  by 47,519 wallets on 10,541 tokens
  grants   1,346,381  by 570,961 wallets (450,384 unlimited)
    resets      37,719  (re-approved within an hour, 18,429 of them USDT)
    cleanups   117,497  by 33,611 wallets
    most cleaned-up spenders  0x000000000022d473030f116ddee9f6b43ac78ba3 (16,905), 0x40aa958dd87fc8305b97f2ba922cddca374bcd7f (11,621), 0xb300000b72deaeb607a12d5f54773d1c19c7028d (6,185)
  revokes per 100 grants  11.5
  day          revokes  cleanups    grants
  2026-10-13    10,080     8,203    51,846
  2026-10-14     5,738     4,621    49,617
  ...
  2026-11-10     6,509     5,263    44,600
  2026-11-11     5,933     4,733    45,925
```

That run was on 12th November 2026 with `END_DAY=2026-11-12`. The most cleaned-up spender, `0x000000000022d473030f116ddee9f6b43ac78ba3`, is Uniswap's Permit2.

## How it counts

- The window is 30 whole UTC days. The script finds the first block at or after each midnight by binary search on HyperSync block timestamps, so no block time is assumed.
- It asks HyperSync for every transaction whose input starts with the `approve(address,uint256)` selector `0x095ea7b3`, joined to its logs (`join_mode: JoinAll`) and block timestamps.
- A transaction counts when it succeeded, was sent straight to the token, and the token emitted a matching ERC-20 `Approval` event (topic0 `0x8c5be1e5…b925`, exactly three topics, so ERC-721 approvals with the same selector are dropped) with the same owner, spender and amount as the call.
- Amount zero is a revoke. Anything above zero is a grant, and amounts at or above 2^255 count as unlimited.
- A revoke is a reset when the same owner grants the same spender on the same token within 3,600 seconds afterwards, by block timestamp. Everything else is a cleanup. A reset in the last hour of the window whose re-approval lands after midnight is counted as a cleanup, so the cleanup figure is a hair high at the edge.
- Only direct calls from a wallet count. Revokes done inside a smart wallet batch, a multicall or a router are not in these numbers, so treat them as a floor.

## Checks

`check.py` checks the numbers three ways. Run `DUMP=dump.json python script.py`, then `python check.py dump.json`.

1. A log-side recount starts from `Approval` events instead of transactions, joins each to its transaction, and recounts three sample days. On 12th November 2026 it gave revokes of 10,080 vs 10,080 (13 Oct), 4,108 vs 4,110 (28 Oct) and 5,932 vs 5,933 (11 Nov). Grants come out 0.3% to 0.4% higher on the log side, because it does not require the event amount to match the call, which the main script does.
2. A public RPC spot check fetches 20 random revokes and 20 random grants with `eth_getTransactionByHash` and `eth_getTransactionReceipt` from public Ethereum nodes, and confirms each one succeeded, called `approve` on the token with the same spender and amount, and emitted the matching `Approval` event. 40 of 40 matched.
3. A public RPC reset check takes 20 random resets, fetches the revoke and its re-approval from a public node, and compares their block timestamps. 20 of 20 were re-approved within the hour.

A second full run of `script.py` gave identical revoke, grant and wallet counts.
