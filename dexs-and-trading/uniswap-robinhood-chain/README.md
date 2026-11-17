# Uniswap on Robinhood Chain

Reads every Uniswap v2, v3 and v4 swap on Robinhood Chain with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints swaps per Uniswap version, the total, when the total passed each milestone, and how many Robinhood stock tokens have traded on Uniswap.

These are the numbers behind Envio's post on Uniswap's Robinhood Chain milestone.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py 2026-11-01 2026-11-02
```

With two UTC dates it counts the swaps between them. With no dates it counts every swap since launch. That is hundreds of millions of logs, so a full run takes over an hour.

## How it counts

- Contracts come from Uniswap's deployment pages for [v4](https://developers.uniswap.org/docs/protocols/v4/deployments), [v3](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) and [v2](https://developers.uniswap.org/docs/protocols/v2/deployments).
- v4 swaps are read from the PoolManager. v2 and v3 swaps only count when the pool was created by the official factory, so forks are left out.
- Stock tokens come from the Robinhood API that the [stock tokens docs](https://docs.robinhood.com/chain/stock-tokens) point to.
- Milestones are counted in days from 1st July 2026, the first day of real activity on the chain.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Uniswap v4 Swap from the PoolManager on Robinhood Chain (chain ID 4663,
https://developers.uniswap.org/docs/protocols/v4/deployments) for the last 7 days.
My API token is in the ENVIO_API_TOKEN environment variable.
Count swaps per day and show me which pools traded the most.
```
