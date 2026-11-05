# Where Polygon's October gas fees came from

Reads every Polygon PoS transaction from October 2026 with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), works out the gas fee each one paid, and ranks the contracts those transactions went to by their share of the month's fees.

These are the numbers behind Envio's post on Polygon's October revenue.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It reads about 148 million transactions, so a full run takes around 25 minutes.

## What it prints

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

October is over, so these numbers don't change.

## How it counts

- October is blocks 94,738,440 to 96,523,828, the first and last blocks with timestamps on 1st to 31st October UTC.
- A transaction's gas fee is `gas_used x effective_gas_price`, which is what the sender paid in POL, base fee and priority fee together.
- Fees are grouped by the transaction's `to` address, the contract the sender called. For Polymarket these are its exchange, deposit wallet and relay contracts.
- Polymarket is every Polygon address in [Polymarket's deployment docs](https://docs.polymarket.com/developers/CTF/deployment-resources) plus its Relay Hub (`0xd216...f494`), which Polygonscan labels "Polymarket: Relay Hub". Other names are Polygonscan labels. Anything without a public label stays unlabelled, including the second biggest destination, `0x84ba...d9a7e`.
- The 22,316,136 POL total, and each of the 31 daily totals, match Polygonscan's daily transaction fee chart to the wei.
- Polygon's own October revenue post says $2.17M without a definition. Polygonscan's daily fees at CoinGecko's daily average POL price come to about $2.18M, so the figure lines up with total gas fees, but this script only measures POL.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Polygon PoS
transaction for a month, with to, gas_used and effective_gas_price. My API token is in the
ENVIO_API_TOKEN environment variable. Rank the destination contracts by the gas fees they paid,
group Polymarket's contracts from https://docs.polymarket.com/developers/CTF/deployment-resources,
and chart the top apps' share of fees day by day.
```
