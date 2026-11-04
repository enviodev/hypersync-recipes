# SPCXc on Aave v4 on Base

Reads every SPCXc transfer and every supply, withdraw and borrow on the Aave v4 tokenized stocks market on Base with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints SPCXc holders and supply, what each listed stock has supplied as collateral, how much USDC is borrowed, and how SPCXc has been used since Aave listed it.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

The SPCXc transfer replay covers more than a million events, so a run takes a few minutes.

## What it prints

```
SPCXc 0xb2000000000000000000007b9fcbd005511acbd5 at block 53,521,593
  totalSupply (eth_call)       20,819.56761682
  minted - burned (Transfers)  20,819.56761682  matches
  holders with a nonzero balance: 9,014 (from 1,171,410 Transfer events)
...
  8 stocks listed: AAPLc, AMZNc, GOOGLc, METAc, MSFTc, NVDAc, TSLAc, SPCXc
  stock collateral supplied: $14,268,047 at Aave oracle prices
  USDC supplied: 6,696,658, USDC borrowed (debt incl. interest): 5,991,344

SPCXc on the market, reserve 8, listed 31 Oct 2026 15:17 UTC (block 53,335,255)
  65 Supply events from 36 addresses, 6,465.0090 SPCXc in
  supplied now (eth_call): 6,464.2333 SPCXc = $873,221 at $135.0850
```

The numbers move as people supply and borrow, so yours will differ.

## How it counts

- Hub, spoke and oracle addresses come from the [Aave address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Base.sol). The SPCXc address is also listed in Coinbase's tokenized stocks API.
- Holders are addresses with a nonzero balance after replaying every SPCXc Transfer. The replayed supply is checked against `totalSupply()`.
- Supplied and borrowed amounts are read live from the spoke with `getReserveSuppliedAssets` and `getReserveTotalDebt`.
- Prices come from the market's Aave oracle with `getReservePrice`. The script also prints Coinbase's published NAV for SPCXc as a check.
- USDC is the only borrowable asset. "USDC owed by SPCXc suppliers" counts every address that has supplied SPCXc, and some of them hold other stocks as collateral too.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Supply, Withdraw and Borrow event on the Aave v4 tokenized stocks spoke on Base
(0x17905db0e4a3514467539956c084180616ae7b8d). My API token is in the
ENVIO_API_TOKEN environment variable. Chart collateral supplied per stock per day.
```
