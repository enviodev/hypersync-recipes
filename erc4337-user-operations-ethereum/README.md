# Every ERC-4337 user operation on Ethereum

From 26 Oct to 15 Nov 2026 (21 full UTC days), **smart accounts on Ethereum sent 661K user operations, about 31.5K a day, from 209K accounts**.

- 468K of them (70.9%) had their gas paid by a paymaster, so the account didn't need ETH to send.
- 321K (48.6%) had their gas paid through [Pimlico's](https://docs.pimlico.io) paymasters.
- In the first 21 days of a wider pull (15 Jul to 4 Aug 2026) the average was 21K a day, so daily user operations are up 50%.
- By EntryPoint version, 475K went through v0.7, 112K through v0.8 and 73K through v0.6.

## Why it's interesting

A user operation is how a smart account sends a transaction, and the paymaster field says who paid the gas. If you're building a wallet or an app with gasless transactions, this one event tells you how many accounts are active, how many of their transactions were sponsored or paid in a token, and which paymaster did it. Point it at your own paymaster or bundler and you've got your own numbers.

## What it pulls

`UserOperationEvent` logs from the three ERC-4337 [EntryPoint contracts](https://github.com/eth-infinitism/account-abstraction) on Ethereum, joined to each block's timestamp. The event is the same on every version.

| EntryPoint | Address |
| --- | --- |
| v0.6 | [`0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789`](https://etherscan.io/address/0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789) |
| v0.7 | [`0x0000000071727De22E5E9d8BAf0edAc6f37da032`](https://etherscan.io/address/0x0000000071727De22E5E9d8BAf0edAc6f37da032) |
| v0.8 | [`0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108`](https://etherscan.io/address/0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108) |

- One event is one user operation. Failed user operations still emit it and are counted. In this window 98.96% succeeded.
- An account is the event's `sender`, counted once across the whole window.
- "Gas paid by a paymaster" means the `paymaster` field isn't the zero address. That covers sponsored transactions and ones where the account pays the paymaster back in a token such as USDC.
- Pimlico's paymasters are the three addresses on Pimlico's [contract addresses](https://docs.pimlico.io/references/paymaster/erc20-paymaster/contract-addresses) page, one per EntryPoint version.

Every number comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                          # the last 21 full UTC days
python3 script.py 2026-10-26 2026-11-15    # the window used above, both dates included
```

Sample output for 26 Oct to 15 Nov 2026.

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

## Change the window or chain

- **Window.** Pass a start and an end date. The script works out a start block from the chain head at 7,200 blocks a day, adds a little slack, and then keeps only events whose block timestamp falls in the window.
- **Chain.** The EntryPoint addresses are the same on most EVM chains. Swap `HS` for the chain's HyperSync URL from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), for example `https://base.hypersync.xyz`, and change `BLOCKS_PER_DAY` to match its block time (43,200 on Base). Check that chain's Pimlico addresses on their page too.

## Check the numbers

Ask any Ethereum RPC for the same logs over a small block range as the comparison. For blocks 26,420,000 to 26,420,999 both HyperSync and `eth_getLogs` return 3,088 events on v0.7, 805 on v0.8 and 363 on v0.6, and 2,039 of the v0.7 events name Pimlico's v0.7 paymaster. This counts the v0.7 events over that range.

```bash
curl -s https://ethereum-rpc.publicnode.com -H 'content-type: application/json' -d '{
  "jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{
    "address":"0x0000000071727De22E5E9d8BAf0edAc6f37da032",
    "topics":["0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"],
    "fromBlock":"0x1932320","toBlock":"0x1932707"}]}' | python3 -c "import sys,json; print(len(json.load(sys.stdin)['result']))"
```

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every
UserOperationEvent from the ERC-4337 EntryPoint contracts v0.6, v0.7 and v0.8
on Ethereum, and counts user operations, accounts and paymaster-paid ones per
day. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Run the same thing on Base. Take the Base HyperSync URL from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks, set
BLOCKS_PER_DAY to 43,200 and keep the standard library only. Add a table of
the 10 paymasters that paid for the most user operations. Run it for the last
2 days first, then check one hour's count for v0.7 against eth_getLogs on a
public Base RPC before you trust the totals.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [ERC-4337 docs](https://docs.erc4337.io) and the [EntryPoint contracts](https://github.com/eth-infinitism/account-abstraction)
- [Pimlico paymaster addresses](https://docs.pimlico.io/references/paymaster/erc20-paymaster/contract-addresses)
- [Envio Discord](https://discord.gg/envio)
