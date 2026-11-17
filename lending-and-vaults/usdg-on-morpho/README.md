# Paxos USDG on Morpho

**HyperSync finds 386 Morpho markets that lend Paxos USDG** across Robinhood Chain, Arbitrum and Ethereum. Rebuilt from their events in a run on 17 Nov 2026, they had $663.6M of USDG supplied, and $590.5M of it (89%) was borrowed. Robinhood Chain had 375 of the markets and $510.7M, and Arbitrum had 8 markets and $152.9M.

| 17 Nov 2026 | USDG markets | Supplied |
| --- | --- | --- |
| Robinhood Chain | 375 | $510.7M |
| Arbitrum | 8 | $152.9M |
| Ethereum | 3 | $0.0M |
| Total | 386 | $663.6M |

## Why it's interesting

Morpho lets anyone create a lending market, so a stablecoin can end up in hundreds of them without a list anywhere. Reading every `CreateMarket` event is the reliable way to find them all. Most of the USDG here is lent against yield-bearing dollars like USDe and syrupUSDG, which tells you what borrowers are using it for.

## How to read "supplied"

Supplied is what Morpho's markets record as supplied, not how much USDG sits in Morpho. The same USDG can be supplied, borrowed, supplied again in another market and borrowed again, so total supplied can be larger than the token's whole supply. What Morpho actually holds is supplied minus borrowed. On Arbitrum in this run that is about $15.6M for the biggest market, in line with the roughly $16.4M of USDG held by Morpho there.

## What it pulls

- Every `CreateMarket` log on Morpho on each chain, keeping the markets whose loan token is USDG. Morpho addresses come from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses) and USDG addresses from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/usdg/mainnet).
- Every `Supply`, `Withdraw`, `Borrow`, `Repay`, `AccrueInterest` and `Liquidate` log in those markets, from HyperSync. USDG counts at $1.
- `symbol()` on each collateral token for its name, and `market(id)` on Morpho for the check below, read from each chain's public RPC.

The list of markets and the supplied and borrowed amounts all come from HyperSync. The script rebuilds each market's `totalSupplyAssets` and `totalBorrowAssets` the way Morpho keeps them. Supplies, borrows and accrued interest add to them, while withdrawals, repays, and debt repaid or written off in liquidations take away. On Robinhood Chain these markets have millions of events, so the script splits the history into block ranges and pulls them side by side.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes about four minutes. Sample output from the 17 Nov 2026 run.

```
Robinhood Chain   375 USDG markets  $510.7M supplied  (up to block 116,484,701)
Arbitrum            8 USDG markets  $152.9M supplied  (up to block 525,000,787)
Ethereum            3 USDG markets  $0.0M supplied  (up to block 26,433,984)

USDG supplied on Morpho: $663.6M, of which $590.5M is borrowed (89%)
  $  357.2M supplied  $  315.6M borrowed  Robinhood Chain  USDe collateral  (54%)
  $  147.4M supplied  $  131.8M borrowed  Arbitrum         syrupUSDG collateral  (22%)
  $   87.3M supplied  $   78.6M borrowed  Robinhood Chain  syrupUSDG collateral  (13%)
  ...

Check (RPC market(id) at the same block)
  Robinhood Chain  USDe       supplied $357,233,657.37 (gap $0.00)  borrowed $315,645,051.43 (gap $0.00)
  Arbitrum         syrupUSDG  supplied $147,374,654.77 (gap $0.00)  borrowed $131,818,899.47 (gap $0.00)
  Robinhood Chain  syrupUSDG  supplied $87,256,849.77 (gap $0.00)  borrowed $78,562,826.09 (gap $0.00)
```

People supply, borrow and repay all the time, so your numbers will differ a little.

## Change the window or chain

- **Chains.** Each chain is one entry in `CHAINS`, with its HyperSync endpoint, a public RPC, the Morpho address and the USDG address. Add a chain where both are live and that's on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Token.** Swap the USDG address in each entry for any other loan token to find its Morpho markets.
- **History.** To see how each market grew, add `block_number` to the field selection and keep a running total per day as the script replays the events.

## Check the numbers

The script checks itself. For the three biggest markets it reads `market(id)` on Morpho over each chain's public RPC at the block HyperSync stopped at, and prints it next to the rebuilt figures. In the 17 Nov 2026 run all three matched to the cent for both supplied and borrowed.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every Morpho market that
lends USDG and rebuild each market's supplied and borrowed USDG from its events.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add block timestamps and print USDG supplied and borrowed on Robinhood Chain at
the end of each day since the first market opened. Keep the standard library
only. Then check the last day against market(id) on Morpho at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Morpho addresses](https://docs.morpho.org/get-started/resources/addresses)
- [Paxos USDG addresses](https://docs.paxos.com/guides/stablecoin/usdg/mainnet)
- [Envio Discord](https://discord.gg/envio)
