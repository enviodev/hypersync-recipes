# SPCXc on Aave v4 on Base

At Base block 58,687,504 on 17 Nov 2026, **9.7K addresses held SPCXc, Coinbase's tokenized SpaceX stock**, rebuilt from 1.70M transfers. Aave listed it on its v4 tokenized stocks market on 31 Oct 2026, and by that block 102 addresses had supplied 11.3K SPCXc across 256 supply events. 9.8K SPCXc was still supplied, 34.9% of all SPCXc. The market had eight stocks listed with $17.3M of stock collateral supplied, valued at the Chainlink prices HyperSync reads from the feeds behind Aave's oracle, and 7.4M USDC borrowed against it. HyperSync rebuilds all of these from the token's transfers, the spoke's events and the price feeds' logs.

## Why it's interesting

Tokenized stocks as lending collateral is new, and Aave v4's hub and spoke layout is new too. This script shows how to follow both at once. It replays the token's full history to get holders, then reads every user action on the market's spoke. If you're building on Aave v4 or tracking stock tokens as collateral, it's a working map of the events and calls you need.

## What it pulls

- Every SPCXc `Transfer` since deployment, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). The holder count and the minted minus burned supply come from HyperSync.
- Every `Supply`, `Withdraw`, `Borrow`, `Repay`, `LiquidationCall`, `ReportDeficit` and `SetUsingAsCollateral` on the market's spoke, from HyperSync. The $17.2M of stock collateral, the 7.4M USDC borrowed, and the supply event, supplier and collateral counts come from here.
- `AnswerUpdated` logs from the nine Chainlink aggregators behind the market's Aave oracle (one per stock, plus USDC/USD), from HyperSync. The dollar values use the latest answer of each at or before the snapshot block. The aggregator addresses come from the oracle's `getReserveSource()`, then each feed proxy's `aggregator()`.
- `getReservePrice` on the market's Aave oracle, `totalSupply()`, `getReserveSuppliedAssets`, `getReserveTotalDebt` and `getUserTotalDebt` through `eth_call` on Base's public RPC, only as checks.
- Coinbase's tokenized stocks API, `https://api.coinbase.com/v1/tokenized-stocks`, as a cross-check on decimals and supply.

Aave v4 keeps positions in shares, and every spoke event carries both shares and amounts. The script counts supply shares and drawn (debt) shares per reserve and per user, takes away shares removed in liquidations, and turns shares into assets with the rate in the reserve's latest event. Borrowed USDC is drawn debt, which leaves out Aave v4's premium debt.

Hub, spoke and oracle addresses come from the [Aave address book for Aave v4 on Base](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Base.sol). SPCXc is [`0xb2000000000000000000007b9fcbd005511acbd5`](https://basescan.org/token/0xb2000000000000000000007b9fcbd005511acbd5) and the spoke is [`0x17905db0e4a3514467539956c084180616ae7b8d`](https://basescan.org/address/0x17905db0e4a3514467539956c084180616ae7b8d).

USDC is the borrowable asset on this market. "USDC owed by SPCXc suppliers" counts every address that has supplied SPCXc, and some of them also post other stocks as collateral.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

The SPCXc replay covers over a million events, so a run takes a few minutes. Sample output at block 58,687,504.

```
SPCXc 0xb2000000000000000000007b9fcbd005511acbd5 at block 58,687,504
  decimals 8, UI multiplier 1
  supply, minted - burned (HyperSync Transfers)  28,027.77489694
  Check (RPC totalSupply()):                     28,027.77489694  matches
  holders with a nonzero balance: 9,662 (from 1,699,711 Transfer events)
...
  8 stocks listed: AAPLc, AMZNc, GOOGLc, METAc, MSFTc, NVDAc, TSLAc, SPCXc
  stock collateral supplied: $17,272,133 at Chainlink feed prices read with HyperSync
  USDC supplied: 8,920,109, USDC borrowed (drawn debt, without premium): 7,370,517
  Check (RPC getReserveSuppliedAssets, getReserveTotalDebt at the same block)
  ...
  7       USDC          8,920,114.2979 (gap -5.6012)      7,370,564.71 (gap -47.69)
  8       SPCXc             9,775.9135 (gap 0.0000)              0.00 (gap 0.00)
  Check (Aave oracle getReservePrice over RPC): stock collateral $17,272,133, gap +0.00%
  SPCXc   feed $  140.7900  oracle $  140.7900  (feed updated 17 Nov 2026 15:01 UTC)

SPCXc on the market, reserve 8, listed 31 Oct 2026 15:17 UTC (block 53,335,255)
  first supply 31 Oct 2026 21:20 UTC
  256 Supply events from 102 addresses, 11,260.4006 SPCXc in
  50 Withdraw events, 1,484.4364 SPCXc out, net 9,775.9642
  supplied now: 9,775.9135 SPCXc = $1,376,351 at $140.7900
  share of all SPCXc: 34.9%
  83 addresses still supply SPCXc, 68 with it enabled as collateral
  USDC owed now by SPCXc suppliers (drawn debt): 813,777.66
  ...
  Check (RPC getUserTotalDebt, summed): 813,803.60, gap -25.94
```

Positions change every block, so your numbers will differ.

## Change the window or chain

- **Another stock.** Swap `SPCXC` for any of the other seven stock tokens on the market (AAPLc, AMZNc, GOOGLc, METAc, MSFTc, NVDAc, TSLAc). Their addresses are in the Coinbase API and the address book.
- **Another Aave v4 market.** Swap the hub, spoke and oracle constants for another file in the [Aave address book](https://github.com/bgd-labs/aave-address-book/tree/main/src), `HYPERSYNC` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and `RPC` for a public RPC on that chain.

## Check the numbers

The script checks itself against Base's public RPC at the same block. In the run above, the SPCXc supply rebuilt from transfers matched `totalSupply()` to the last decimal, and every stock reserve rebuilt from spoke events matched `getReserveSuppliedAssets` exactly. USDC supplied sat $6 below the spoke's figure and USDC borrowed $48 below `getReserveTotalDebt`, because the events give the share rate as of each reserve's last event and leave out premium debt. It also prints Coinbase's published supply and NAV for SPCXc as an outside comparison. For prices, it values the stock collateral at Aave's oracle (`getReservePrice` over RPC) as a labelled check and prints the feed and oracle price for each stock. In the run above the two totals were identical to the dollar, and every stock's price matched, so the Chainlink answers HyperSync reads are what the oracle serves.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Base to replay every SPCXc Transfer
and every Supply, Withdraw, Borrow, Repay and LiquidationCall on the Aave v4 tokenized stocks spoke.
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
