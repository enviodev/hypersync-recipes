# SPCXc on Aave v4 on Base

At Base block 53,521,593, **9K addresses held SPCXc, Coinbase's tokenized SpaceX stock**, rebuilt from 1.17M transfers. Aave listed it on its v4 tokenized stocks market on 31 Oct 2026, and by that block 36 addresses had supplied 6.5K SPCXc across 65 supply events. The market had eight stocks listed with $14.3M of stock collateral supplied, and 6M USDC borrowed against it.

## Why it's interesting

Tokenized stocks as lending collateral is new, and Aave v4's hub and spoke layout is new too. This script shows how to follow both at once. It replays the token's full history to get holders, then reads every user action on the market's spoke. If you're building on Aave v4 or tracking stock tokens as collateral, it's a working map of the events and calls you need.

## What it pulls

- Every SPCXc `Transfer` since deployment, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). The holder count and the minted minus burned supply come from HyperSync.
- Every `Supply`, `Withdraw`, `Borrow` and `Repay` on the market's spoke, from HyperSync. The supply event and supplier counts come from here.
- The market's live state through `eth_call` on Base's public RPC. `totalSupply()` on the token, `getReserveSuppliedAssets` and `getReserveTotalDebt` on the spoke, and `getReservePrice` on the market's Aave oracle. The $14.3M collateral and the 6M USDC borrowed come from these calls, not from HyperSync.
- Coinbase's tokenized stocks API, `https://api.coinbase.com/v1/tokenized-stocks`, as a cross-check on decimals and supply.

Hub, spoke and oracle addresses come from the [Aave address book for Aave v4 on Base](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Base.sol). SPCXc is [`0xb2000000000000000000007b9fcbd005511acbd5`](https://basescan.org/token/0xb2000000000000000000007b9fcbd005511acbd5) and the spoke is [`0x17905db0e4a3514467539956c084180616ae7b8d`](https://basescan.org/address/0x17905db0e4a3514467539956c084180616ae7b8d).

USDC is the borrowable asset on this market. "USDC owed by SPCXc suppliers" counts every address that has supplied SPCXc, and some of them also post other stocks as collateral.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

The SPCXc replay covers over a million events, so a run takes a few minutes. Sample output at block 53,521,593:

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

Positions change every block, so your numbers will differ.

## Change the window or chain

- **Another stock.** Swap `SPCXC` for any of the other seven stock tokens on the market (AAPLc, AMZNc, GOOGLc, METAc, MSFTc, NVDAc, TSLAc). Their addresses are in the Coinbase API and the address book.
- **Another Aave v4 market.** Swap the hub, spoke and oracle constants for another file in the [Aave address book](https://github.com/bgd-labs/aave-address-book/tree/main/src), `HYPERSYNC` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and `RPC` for a public RPC on that chain.

## Check the numbers

The script checks itself. The SPCXc supply rebuilt from HyperSync transfers is compared with `totalSupply()` read over RPC, and the run above matched to the last decimal. It also prints Coinbase's published supply and NAV for SPCXc as an outside comparison.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Base to replay every SPCXc Transfer
and every Supply, Withdraw, Borrow and Repay on the Aave v4 tokenized stocks spoke.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a daily series of net collateral supplied per stock, from the Supply and Withdraw
events the script already reads, and write it to collateral_daily.csv. Keep the
standard library only. Then check that the SPCXc running total on the last day matches
the "supplied now" figure the script prints, allowing for interest.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aave v4 address book for Base](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Base.sol)
- [Aave docs](https://aave.com/docs)
- [Envio Discord](https://discord.gg/envio)
