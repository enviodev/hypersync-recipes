# Solana DEX swaps by program

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer that counts every successful swap on Solana's main DEX programs, day by day, and splits each count into swaps sent straight to the DEX and swaps another program called in for you. Jupiter routes are counted on their own row.

These are the numbers behind Envio's post on who carries Solana's trading, ahead of Breakpoint. Solana Compass relayed a Fidelity stat that Solana DEXs log about 15% as many trades as the major US stock exchanges, with no breakdown. This is the breakdown.

## What we found

We counted 220M successful swaps across the ten programs over the seven UTC days from 3rd to 9th November 2026, about 31M a day.

- PumpSwap carried just over half of them.
- Meteora DAMM v2 came second with about 1 in 6, more than Orca Whirlpool, Raydium CLMM and Meteora DLMM put together. More than 9 in 10 DAMM v2 swaps were sent to it directly.
- Orca Whirlpool, Raydium CLMM and Meteora DLMM work the other way. More than 8 in 10 of their swaps were called in by another program, such as the Jupiter aggregator, rather than sent to them directly.

| Program | Swaps | Share | Called by another program |
|---|---:|---:|---:|
| PumpSwap | 119.6M | 54.3% | 13% |
| Meteora DAMM v2 | 35.7M | 16.2% | 7% |
| Pump.fun curve | 28.3M | 12.8% | 76% |
| Orca Whirlpool | 11.0M | 5.0% | 88% |
| Raydium CLMM | 9.7M | 4.4% | 81% |
| Meteora DLMM | 9.0M | 4.1% | 91% |
| Raydium CPMM | 3.4M | 1.5% | 87% |
| Raydium LaunchLab | 1.7M | 0.8% | 82% |
| Raydium AMM v4 | 1.5M | 0.7% | 81% |
| Meteora DAMM v1 | 0.4M | 0.2% | 97% |
| Total | 220.2M | 100% | |
| Jupiter routes (not in the total) | 18.2M | | 21% |

Meteora DAMM v2's daily share stayed between 13% and 18% all week.

## Programs and swap instructions

Program IDs and instruction discriminators come from each project's own GitHub repo or published IDL. Only instructions that trade are listed in `config.yaml`, so liquidity, fee, position and event-logging calls never match.

| Program | Program ID | Swap instructions |
|---|---|---|
| Raydium AMM v4 | `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` | SwapBaseIn, SwapBaseOut, SwapBaseInV2, SwapBaseOutV2 |
| Raydium CLMM | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` | swap, swap_v2, swap_router_base_in |
| Raydium CPMM | `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C` | swap_base_input, swap_base_output |
| Raydium LaunchLab | `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` | buy_exact_in, buy_exact_out, sell_exact_in, sell_exact_out |
| Orca Whirlpool | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` | swap, swap_v2, two_hop_swap, two_hop_swap_v2 |
| Meteora DLMM | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | swap, swap2, swap_exact_out, swap_exact_out2, swap_with_price_impact, swap_with_price_impact2 |
| Meteora DAMM v1 | `Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB` | swap |
| Meteora DAMM v2 | `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG` | swap, swap2 |
| PumpSwap | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | buy, sell, buy_exact_quote_in, buy_v2, sell_v2, buy_exact_quote_in_v2, multi_hop_swap |
| Pump.fun bonding curve | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | buy, sell, buy_exact_sol_in, the v2 and v3 buys and sells, multi_hop_curve_swap |
| Jupiter v6 (routes only) | `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4` | route, shared_accounts_route, exact_out_route and their v2, token-ledger and attestation variants |

Sources: [raydium-amm](https://github.com/raydium-io/raydium-amm), [raydium-idl](https://github.com/raydium-io/raydium-idl), [orca-so/whirlpools](https://github.com/orca-so/whirlpools), [dlmm-sdk](https://github.com/MeteoraAG/dlmm-sdk), [damm-v1-sdk](https://github.com/MeteoraAG/damm-v1-sdk), [damm-v2](https://github.com/MeteoraAG/damm-v2), [pump-public-docs](https://github.com/pump-fun/pump-public-docs), [jupiter-cpi](https://github.com/jup-ag/jupiter-cpi).

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and an API token from the [Envio Dashboard](https://envio.dev/app/api-tokens).

```bash
cp .env.example .env   # then paste your token into it
pnpm install
pnpm codegen
pnpm dev
```

`config.yaml` covers one UTC day, 9 Nov 2026 (slots 467108373 to 467510826). Change `start_slot` and `end_slot` to index another window. A day is about 34M matched instructions. On a laptop one day took about 20 minutes, so for the week we ran one copy of the indexer per day, side by side, each with its own database.

When it finishes, query the `DailyVenueSwaps` entity in the GraphQL playground at http://localhost:8080, or straight from Postgres:

```sql
select day, program, swaps, "topLevel", "inner"
from "DailyVenueSwaps"
order by day, swaps desc;
```

## How it counts

- A swap is one matched swap instruction, top-level or inner. Inner instructions are calls another program made by CPI, such as an aggregator or a trading bot. HyperIndex sees both, and `isInner` tells them apart.
- Jupiter routes are kept on their own row and left out of every share. The pool swaps a route triggers are already counted under each DEX, so adding the route as well would count the same trade twice.
- A multi-hop instruction counts once per program it runs in. A PumpSwap multi-hop that also trades on the Pump.fun curve shows up once under each.
- Only successful transactions count. HyperSync does not serve the instructions of failed transactions.
- Days are UTC. The slot at each midnight was found from block times.
- Not covered: venues that publish no IDL or swap layout (the private market makers that only quote through aggregators, such as HumidiFi, SolFi, Tessera V, GoonFi and ZeroFi), and order books such as Phoenix and OpenBook. Their trades are not in these numbers.

## How we checked it

- On two windows, 100 slots and 2,000 slots (467300000 to 467301999, run from a clean copy of this folder), the indexer's counts matched a direct HyperSync count of the same instructions exactly, for every program.
- In four single slots spread across the week (464700001, 465900123, 466800777 and 467400555) we decoded every successful transaction from Solana RPC `getBlock`, top-level and inner, and counted the same instructions. Every program matched exactly.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Build an Envio HyperIndex indexer on Solana (https://docs.envio.dev/docs/HyperIndex/solana)
that counts swap instructions per UTC day for these programs: Raydium AMM v4, CLMM, CPMM,
Orca Whirlpool, Meteora DLMM and DAMM v2, PumpSwap and the Pump.fun bonding curve.
Take each program ID and swap instruction discriminator from the project's own IDL or repo,
match only swap instructions, and split every count into top-level and inner (CPI) calls
using instruction.isInner. Count Jupiter v6 routes separately so routed trades aren't
counted twice. My API token is in the ENVIO_API_TOKEN environment variable.
```

## Learn more

- [Indexing on Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Solana instruction handlers](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [Solana configuration file](https://docs.envio.dev/docs/HyperIndex/solana/configuration)
- [How to index and track stablecoin transfers on Solana](https://docs.envio.dev/blog/index-solana-stablecoin-transfers)
- [Solana on Envio](https://envio.dev/chains/solana)
