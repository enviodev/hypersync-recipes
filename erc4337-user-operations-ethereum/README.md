# Every ERC-4337 user operation on Ethereum

Reads every `UserOperationEvent` from the three ERC-4337 EntryPoint contracts on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview) and prints user operations per day, the accounts behind them, how many had their gas paid by a paymaster and how many of those went through Pimlico's paymasters.

These are the numbers behind Envio's post on smart accounts on Ethereum.

## The finding

From 26 Oct to 15 Nov 2026 (21 full UTC days), smart accounts on Ethereum sent 660,754 user operations, about 31,464 a day, from 209,311 accounts.

- 468,339 of them (70.9%) had their gas paid by a paymaster, so the account didn't need ETH to send.
- 321,048 (48.6%) had their gas paid through [Pimlico's](https://docs.pimlico.io) paymasters.
- In the first 21 days of the wider pull (15 Jul to 4 Aug 2026) the average was 20,972 a day, so daily user operations are up 50%.
- By EntryPoint: 475,375 on v0.7, 112,077 on v0.8 and 73,302 on v0.6.

## Why it matters

A user operation is how a smart account sends a transaction. The paymaster field says who paid the gas. If you're building a wallet or an app with gasless transactions, this one event tells you how many accounts are active, how many of their transactions were sponsored or paid in a token, and which paymaster did it. You can run the same pull for your own paymaster or bundler address.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

That covers the last 21 full UTC days. Pass a start and end date to pick the window. The post used:

```bash
python3 script.py 2026-10-26 2026-11-15
```

## What it prints

```
ERC-4337 on Ethereum, 26 Oct to 15 Nov 2026 UTC (21 days)
User operations 660,754  (31,464 a day)  from 209,311 accounts
By EntryPoint: {'v0.7': 475375, 'v0.8': 112077, 'v0.6': 73302}
Gas paid by a paymaster: 468,339 (70.9%)
Through Pimlico's paymasters: 321,048 (48.6%)

day         user ops  accounts  paymaster  pimlico
2026-10-26    32,320    18,962     23,861   15,370
2026-10-27    33,189    19,540     23,143   15,213
2026-10-28    32,934    19,073     22,955   15,278
2026-10-29    31,500    18,527     22,093   14,400
2026-10-30    32,923    19,326     23,241   16,037
...
```

## How it counts

- One `UserOperationEvent` is one user operation. The event is the same on EntryPoint v0.6 (`0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789`), v0.7 (`0x0000000071727De22E5E9d8BAf0edAc6f37da032`) and v0.8 (`0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108`).
- An account is the event's `sender`. Accounts are counted once across the whole window.
- "Gas paid by a paymaster" means the event's `paymaster` field isn't the zero address. That covers both sponsored transactions and ones where the account pays the paymaster back in a token such as USDC.
- Pimlico's paymasters are the three addresses on Pimlico's [contract addresses](https://docs.pimlico.io/references/paymaster/erc20-paymaster/contract-addresses) page, one per EntryPoint version.
- Failed user operations still emit the event and are counted. In this window 98.96% succeeded.

## Check the numbers yourself

Ask any Ethereum RPC for the same logs over a small block range and compare. For blocks 26420000 to 26420999 both HyperSync and `eth_getLogs` return 3,088 events on v0.7, 805 on v0.8 and 363 on v0.6, and 2,039 of the v0.7 events name Pimlico's v0.7 paymaster.

```bash
curl -s https://ethereum-rpc.publicnode.com -H 'content-type: application/json' -d '{
  "jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{
    "address":"0x0000000071727De22E5E9d8BAf0edAc6f37da032",
    "topics":["0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"],
    "fromBlock":"0x1932320","toBlock":"0x1932707"}]}' | python3 -c "import sys,json; print(len(json.load(sys.stdin)['result']))"
```

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
UserOperationEvent from the ERC-4337 EntryPoint contracts on Ethereum (v0.6
0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789, v0.7 0x0000000071727De22E5E9d8BAf0edAc6f37da032,
v0.8 0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108). My API token is in the ENVIO_API_TOKEN
environment variable. Start from script.py in
https://github.com/enviodev/hypersync-recipes/tree/main/erc4337-user-operations-ethereum.
For the last 30 days, chart user operations per day split by paymaster address, and list
the 20 accounts that sent the most. Then do the same on Base (https://base.hypersync.xyz).
Check one day's count against eth_getLogs on a public RPC before you trust the totals.
```

## Sources

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview) and [supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [ERC-4337 docs](https://docs.erc4337.io) and the [EntryPoint contracts](https://github.com/eth-infinitism/account-abstraction)
- [Pimlico paymaster addresses](https://docs.pimlico.io/references/paymaster/erc20-paymaster/contract-addresses)
- [Envio Discord](https://discord.gg/envio)
