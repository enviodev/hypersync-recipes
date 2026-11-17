# Ethereum approval cleanups

In the 30 days from 13 Oct to 11 Nov 2026 (UTC), **wallets on Ethereum revoked 155K ERC-20 approvals, and 117K of those were real cleanups by 33.6K wallets**. The other 37.7K were resets, where the wallet approved the same spender again within the hour, and almost half of those (18.4K) were USDT. The spender people cleaned up most was Uniswap's Permit2, with 16.9K.

| 30 days to 11 Nov 2026 | |
| --- | --- |
| Revokes | 155,216 by 47,519 wallets |
| Resets | 37,719 (18,429 USDT) |
| Cleanups | 117,497 by 33,611 wallets |
| Grants | 1,346,381 (450,384 unlimited) |
| Revokes per 100 grants | 11.5 |

## Why it's interesting

Counting `approve(spender, 0)` calls overstates how often people clean up. Some tokens, USDT the best known, make you set an allowance to zero before you can change it, so a lot of revokes are just the first half of a new approval. This script pairs every revoke with any re-approval that follows, so what's left is people removing access they no longer want.

[Revoke.cash](https://revoke.cash) does this kind of work for its users on more than 100 networks, and its [Dependency Spotlight on Envio](https://revoke.cash/blog/2025/dependency-spotlight-envio) explains how it uses HyperSync to read a wallet's full approval history.

## What it pulls

All of it comes from HyperSync.

- Every transaction whose input starts with the `approve(address,uint256)` selector `0x095ea7b3`, joined to its logs (`join_mode: JoinAll`) and block timestamps.
- The ERC-20 `Approval` log in each of those transactions (topic0 `0x8c5be1e5...b925`).

A transaction counts when it succeeded, was sent straight to the token, and the token emitted a matching `Approval` event with exactly three topics and the same owner, spender and amount as the call. The three-topic rule drops ERC-721 approvals, which share the selector. Amount zero is a revoke, anything above zero is a grant, and amounts at or above 2^255 count as unlimited.

A revoke is a reset when the same owner grants the same spender on the same token within 3,600 seconds afterwards, by block timestamp. Everything else is a cleanup. A revoke in the last hour of the window whose re-approval lands after midnight counts as a cleanup, so the cleanup figure is a touch high at the edge.

Only direct calls from a wallet count. Revokes done inside a smart wallet batch, a multicall or a router aren't in these numbers, so treat them as a floor.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                        # the last 30 full UTC days
END_DAY=2026-11-12 python3 script.py     # the 30 days before 12 Nov 2026, as above
DAYS=7 python3 script.py                 # a shorter window
```

A 30-day run scans about 1.5M transactions and takes around five minutes. Sample output with `END_DAY=2026-11-12`.

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

The first spender, `0x000000000022d473030f116ddee9f6b43ac78ba3`, is [Uniswap's Permit2](https://etherscan.io/address/0x000000000022d473030f116ddee9f6b43ac78ba3). With `END_DAY` set the window is fixed, so a rerun gives the same counts.

## Change the window or chain

- **Window.** `DAYS` sets the length and `END_DAY` the day after the last one, both in UTC. The script finds the first block at or after each midnight by binary search on block timestamps.
- **Reset rule.** `RESET_WINDOW` is the 3,600 seconds a re-approval has to land in.
- **Chain.** `CHAINS` maps a name to a chain ID, and the script calls `https://<chain id>.hypersync.xyz`. Add another chain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), for example `"Base": 8453`, and set `CHAIN=Base` to run only that one. `USDT` is the Ethereum address, so update it for the reset breakdown on other chains. `check.py` has its own `CHAINS` and public `RPC` list to extend.

## Check the numbers

`check.py` checks a run three ways. Run `DUMP=dump.json python3 script.py`, then `python3 check.py dump.json`.

1. **Log-side recount, with HyperSync.** It starts from `Approval` events instead of transactions, joins each to its transaction, and recounts the first, middle and last day. On 12 Nov 2026 it gave revokes of 10,080 vs 10,080 (13 Oct), 4,108 vs 4,110 (28 Oct) and 5,932 vs 5,933 (11 Nov). Grants come out 0.3% to 0.4% higher on the log side, because it doesn't require the event amount to match the call.
2. **Public RPC spot check, as the comparison.** It fetches 20 random revokes and 20 random grants with `eth_getTransactionByHash` and `eth_getTransactionReceipt` from public Ethereum nodes, and confirms each one succeeded, called `approve` on the token with the same spender and amount, and emitted the matching `Approval` event. 40 of 40 matched.
3. **Public RPC reset check, as the comparison.** It takes 20 random resets, fetches the revoke and its re-approval from a public node, and compares their block timestamps. 20 of 20 were re-approved within the hour.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py, check.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every approve()
transaction on Ethereum with its Approval event, then splits revokes into
resets and real cleanups. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add Base (chain ID 8453) to CHAINS and print the same summary for both chains,
with the USDT address set per chain. Add Base to CHAINS and RPC in check.py too.
Keep the standard library only. Run it with DAYS=3 and DUMP=dump.json, then run
check.py on the dump and confirm the log-side recount matches for both chains.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Revoke.cash on Envio](https://revoke.cash/blog/2025/dependency-spotlight-envio)
- [Envio Discord](https://discord.gg/envio)
