# Base smart accounts and gas-covered transactions

Over the seven days to the afternoon of 18 Nov 2026 (UTC), **564K smart accounts sent a transaction through ERC-4337 on Base, and 214K of them had at least one transaction where a paymaster covered the gas**. Across the week that is 3.27M user operations, with about 100K to 115K different accounts active on a typical day, and 203K accounts had every one of their operations covered.

| 24 hours from the afternoon (UTC) of | Accounts | With a gas-covered transaction |
| --- | --- | --- |
| Wed 11 Nov | 100,213 | 38,434 |
| Thu 12 Nov | 115,677 | 54,976 |
| Fri 13 Nov | 105,453 | 49,092 |
| Sat 14 Nov | 108,559 | 53,413 |
| Sun 15 Nov | 102,455 | 43,841 |
| Mon 16 Nov | 105,521 | 39,751 |
| Tue 17 Nov | 104,264 | 39,048 |

## Why it's interesting

Smart accounts are the part of ERC-4337 that people actually use. A smart account can have its gas paid by an app through a paymaster, so a new user can act without holding ETH first. Counting accounts, not transactions, shows how many people that reaches. A handful of automated accounts send thousands of operations a day on Base, which would swamp a transaction count but add almost nothing to an account count.

## What it pulls

All of it comes from HyperSync.

- Every `UserOperationEvent` log from the three EntryPoint contracts, `0x5ff137d4...` (0.6), `0x0000000071727de2...` (0.7) and `0x4337084d...` (0.8), on the chain you pick. The topic is `0x49628fd1...`.
- `topic2` is the smart account (the sender) and `topic3` is the paymaster. A zero paymaster means the account paid its own gas.
- Block timestamps, to find the start of each 24-hour window by binary search.

An account counts once however many operations it sent. "Gas covered" means the operation named a paymaster.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
CHAIN=base DAYS=7 python3 script.py
```

A week on Base is about 3M logs and takes a few minutes. `DAYS=1` is a quick check.

## Change the window or chain

- **Chain.** Set `CHAIN` to any EVM network on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks). All three EntryPoints sit at the same addresses on every chain that has them.
- **Window.** `DAYS` sets how many 24-hour windows to count back from now.

## Check the numbers

Pick a block range and ask any Base RPC for `eth_getLogs` on the three EntryPoint addresses with the `UserOperationEvent` topic. The number of logs, the number with a non-zero `topic3` and the number of distinct `topic2` values should match HyperSync for the same blocks. We checked blocks 59,100,000 to 59,100,999 on 18 Nov and got 1,259 operations, 738 gas-covered and 503 accounts from both.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every ERC-4337
UserOperationEvent from the three EntryPoint contracts, then counts smart
accounts and how many had a paymaster cover their gas. My HyperSync token is
in the ENVIO_API_TOKEN environment variable.

Add a count of distinct paymasters per day and the share of operations that
each of the top five paymasters sponsored. Keep the standard library only.
Run it with CHAIN=base DAYS=2 and check the account counts match a run
without your change.
```

This repo ships Envio's agent skills in `.claude/skills/`, so a coding agent picks up the HyperSync docs and patterns automatically.

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [ERC-4337 specification](https://eips.ethereum.org/EIPS/eip-4337)
- [Base docs](https://docs.base.org)
- [Envio Discord](https://discord.gg/envio)
