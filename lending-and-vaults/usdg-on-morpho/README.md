# Paxos USDG on Morpho

**HyperSync finds 382 Morpho markets that lend Paxos USDG** across Robinhood Chain, Arbitrum and Ethereum. Read live in a run on 4 Nov 2026, they held $659.9M of USDG, and $593.2M of it (90%) was borrowed. Robinhood Chain had 371 of the markets and $516.7M, and Arbitrum had 8 markets and $143.2M.

| 4 Nov 2026 | USDG markets | Supplied |
| --- | --- | --- |
| Robinhood Chain | 371 | $516.7M |
| Arbitrum | 8 | $143.2M |
| Ethereum | 3 | $0.0M |
| Total | 382 | $659.9M |

## Why it's interesting

Morpho lets anyone create a lending market, so a stablecoin can end up in hundreds of them without a list anywhere. Reading every `CreateMarket` event is the reliable way to find them all. Most of the USDG here is lent against yield-bearing dollars like USDe and syrupUSDG, which tells you what borrowers are using it for.

## What it pulls

- Every `CreateMarket` log on Morpho on each chain, keeping the markets whose loan token is USDG. Morpho addresses come from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses) and USDG addresses from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/usdg/mainnet).
- For each of those markets, `market(id)` on Morpho for `totalSupplyAssets` and `totalBorrowAssets`, and `symbol()` on the collateral token, read from each chain's public RPC. USDG counts at $1.

The list of markets comes from HyperSync. The supplied and borrowed amounts are the markets' live state, read over public RPC.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Sample output from the 4 Nov 2026 run.

```
Robinhood Chain   371 USDG markets  $516.7M supplied
Arbitrum            8 USDG markets  $143.2M supplied
Ethereum            3 USDG markets  $0.0M supplied

USDG supplied on Morpho: $659.9M, of which $593.2M is borrowed (90%)
  $  348.0M supplied  $  311.0M borrowed  Robinhood Chain  USDe collateral  (53%)
  $  143.2M supplied  $  130.2M borrowed  Arbitrum         syrupUSDG collateral  (22%)
  $  100.6M supplied  $   90.6M borrowed  Robinhood Chain  syrupUSDG collateral  (15%)
  ...
```

People supply, borrow and repay all the time, so your numbers will differ a little.

## Change the window or chain

- **Chains.** Each chain is one entry in `CHAINS`, with its HyperSync endpoint, a public RPC, the Morpho address and the USDG address. Add a chain where both are live and that's on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Token.** Swap the USDG address in each entry for any other loan token to find its Morpho markets.
- **History.** To see how each market grew, add `Supply`, `Withdraw`, `Borrow` and `Repay` logs for the market IDs the script finds.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every Morpho market that
lends USDG, then reads each market's live state over RPC. My HyperSync token is
in the ENVIO_API_TOKEN environment variable.

Replace the RPC reads with HyperSync. Pull every Supply, Withdraw, Borrow and
Repay log for the USDG market IDs on Robinhood Chain and rebuild supplied and
borrowed per market, then print USDG supplied per day since the first market
opened. Keep the standard library only. Then check the rebuilt totals for the
three biggest markets against market(id) on Morpho, and explain the gap (interest).
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Morpho addresses](https://docs.morpho.org/get-started/resources/addresses)
- [Paxos USDG addresses](https://docs.paxos.com/guides/stablecoin/usdg/mainnet)
- [Envio Discord](https://discord.gg/envio)
