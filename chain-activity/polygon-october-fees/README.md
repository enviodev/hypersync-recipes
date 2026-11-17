# Where Polygon's October gas fees came from

In October 2026, **148M Polygon PoS transactions paid 22.3M POL in gas fees, and transactions to Polymarket's contracts paid 11.1M POL of it (49.5%)**. The single biggest destination was Polymarket's CTF Exchange V2, at 7.0M POL from 32.4M transactions.

| October 2026 | Fees paid | Share |
| --- | --- | --- |
| Polymarket, 20 contracts | 11,050,818 POL | 49.52% |
| QuickSwap V2 Router | 519,039 POL | 2.33% |
| Circle USDC and USDC.e | 314,015 POL | 1.41% |
| All transactions | 22,316,136 POL | |

## Why it's interesting

Chain fee totals are easy to find. Knowing which apps paid them is harder, because it means reading every transaction's gas used and price. HyperSync hands back exactly those fields for a whole month of transactions, so you can rank any chain's contracts by the fees their users paid.

## What it pulls

All of it comes from HyperSync.

- Every Polygon PoS transaction in October 2026, blocks 94,738,440 to 96,523,828, with `to`, `gas_used` and `effective_gas_price`.
- Every block in that range, with `timestamp`, `gas_used` and `base_fee_per_gas`, to split fees into the base fee part and the priority fee part and to group them by day.

A transaction's fee is `gas_used x effective_gas_price`, which is what the sender paid in POL. Fees are grouped by the transaction's `to` address, the contract the sender called.

Polymarket is five core contracts hardcoded in the script, plus every address listed on [Polymarket's deployment docs](https://docs.polymarket.com/developers/CTF/deployment-resources), which the script reads when it runs. The five include its Relay Hub (`0xd216153c06e857cd7f72665e0af1d7d82172f494`), which [Polygonscan](https://polygonscan.com/address/0xd216153c06e857cd7f72665e0af1d7d82172f494) labels "Polymarket: Relay Hub". Other names are Polygonscan labels. Anything without a public label stays unlabelled, including the second biggest destination, `0x84ba896235059fe27727eaa2695a9f99220d9a7e`.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It reads about 148M transactions, so a full run takes around 25 minutes. It also writes `polygon_october_fees.json` with the top 200 destinations and the daily totals. Sample output, with the top 25 cut to three.

```
Polygon PoS, October 2026: 148,206,817 transactions paid 22,316,136 POL in gas fees
  base fee part 13,288,433 POL, priority fee part 9,027,702 POL
Top destinations by share of fees
  0xe111180000d2663c0091e4f400237545b87b996b Polymarket CTF Exchange V2          6,975,073 POL  31.26%   32,447,050 txs
  0x84ba896235059fe27727eaa2695a9f99220d9a7e                                     2,444,447 POL  10.95%    4,407,118 txs
  0xe2222d279d744050d28e00520010520000310f59 Polymarket Neg Risk CTF Exchange V2    2,037,707 POL   9.13%   10,277,038 txs
  ...
By app
  Polymarket, 20 contracts     11,050,818 POL  49.52%
  QuickSwap V2 Router                 519,039 POL   2.33%
  Circle USDC and USDC.e              314,015 POL   1.41%
```

October is over, so these numbers won't change.

## Change the window or chain

- **Window.** `START` and `END` are the first block of 1 October and of 1 November (UTC), with `END` not included. For another month, find the first block at or after each midnight and set them. The "October 2026" label in the first printed line is fixed text, so update it too.
- **Chain.** Swap `URL` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and replace `POLYMARKET` and `LABELS` with that chain's contracts. Fees are in the chain's gas token.

## Check the numbers

As a comparison, the 22,316,136 POL total and each of the 31 daily totals in `polygon_october_fees.json` match [Polygonscan's daily transaction fee chart](https://polygonscan.com/chart/transactionfee) to the wei.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Polygon PoS
transaction in October 2026 and ranks destination contracts by the gas fees
their transactions paid. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Make the month a command line argument (for example 2026-09), finding the first
block of the month and of the next one by binary search on block timestamps,
and print Polymarket's share of fees per day. Keep the standard library only.
Run it for 2026-10 and check that the total still comes to 22,316,136 POL.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Raw HTTP query examples](https://docs.envio.dev/docs/HyperSync/hypersync-curl-examples), the same plain requests this script makes
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Polymarket contract addresses](https://docs.polymarket.com/developers/CTF/deployment-resources)
- [Envio Discord](https://discord.gg/envio)
