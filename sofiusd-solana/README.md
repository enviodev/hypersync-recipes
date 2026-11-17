# SoFiUSD supply on Solana

Up to slot 470,156,022 (16 Nov 2026), **SoFiUSD, the stablecoin issued by SoFi Bank, had a supply of $274.1M on Solana**, rebuilt from all 421 mints and burns since its first mint on 28 Apr 2026. Month-end supply rose every month from June, and $179M was minted from 1 Sep to 16 Nov.

| Month | Minted | Burned | Supply at month end |
|---|---:|---:|---:|
| 2026-04 | 0.0M | 0.0M | 0.0M |
| 2026-05 | 0.1M | 0.0M | 0.0M |
| 2026-06 | 209.2M | 5.8M | 203.5M |
| 2026-07 | 15.5M | 9.0M | 209.9M |
| 2026-08 | 19.6M | 14.9M | 214.7M |
| 2026-09 | 69.9M | 53.8M | 230.7M |
| 2026-10 | 64.8M | 45.0M | 250.6M |
| 2026-11 (to the 16th) | 44.5M | 21.1M | 274.1M |

## Why it's interesting

A bank-issued stablecoin is a new thing to see onchain, and every unit of it moves through two instructions. Mints and burns on one Token-2022 mint give you its full supply history, month by month, with nothing else to read.

## What it pulls

- **Token.** SoFiUSD, the Token-2022 mint `APhcqtzE73es3KAGiVksZFMLGwJDiAey5qZKUrQHEHfS` (symbol SOFID, 6 decimals). Its onchain metadata describes it as backed 1:1 by US dollars and issued by SoFi.
- **Program.** [Token-2022](https://spl.solana.com/token-2022), `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`.
- **Instructions.** `MintTo` (tag 7) and `MintToChecked` (tag 14) with the mint as account 0, and `Burn` (tag 8) and `BurnChecked` (tag 15) with the mint as account 1. The script asks HyperSync for those with the `d1`, `a0` and `a1` filters, then checks the tag and the mint again in code.
- **Amount.** The little-endian u64 after the one-byte tag, divided by 10^6.
- **Window.** Slot 370,000,000, before SoFiUSD launched on Solana, to the chain head.

The supply comes from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). Solana RPC is only the comparison below.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Sample output from a run on 16 Nov 2026.

```
Month          Minted       Burned   Supply at end
2026-04          0.0M         0.0M            0.0M
2026-05          0.1M         0.0M            0.0M
2026-06        209.2M         5.8M          203.5M
2026-07         15.5M         9.0M          209.9M
2026-08         19.6M        14.9M          214.7M
2026-09         69.9M        53.8M          230.7M
2026-10         64.8M        45.0M          250.6M
2026-11         44.5M        21.1M          274.1M

SoFiUSD supply on Solana from mints and burns: 274,066,133.48
Compare with Solana RPC getTokenSupply for APhcqtzE73es3KAGiVksZFMLGwJDiAey5qZKUrQHEHfS
```

## Change the token

- **Another stablecoin.** Swap `SOFIUSD` for another mint and the `/ 1e6` for its decimals. Change `START_SLOT` in `script.py` to a slot before its first mint. HyperSync's Solana history starts at slot 391,001,451 (3 Jan 2026), so a token that launched before then needs its earlier supply added from `getTokenSupply`.
- **Classic SPL tokens.** Swap `TOKEN_2022` for `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`.
- **Failed transactions.** The selections don't filter on success. For a token where that matters, add `"tx_success": True` to each one in `SELECTION`.

## Check the numbers

As the comparison, Solana RPC [`getTokenSupply`](https://solana.com/docs/rpc/http/gettokensupply) for the mint returned 274,066,133.48 at slot 470,149,545. That's the same as the HyperSync total to the cent.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana-query) to pull every Token-2022
MintTo, MintToChecked, Burn and BurnChecked on the SoFiUSD mint
APhcqtzE73es3KAGiVksZFMLGwJDiAey5qZKUrQHEHfS and rebuilds supply by month.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add the mint authority (account 2 on MintTo) to each mint and print how much each
authority minted per month, plus a daily supply series for the last 30 days. Keep
the standard library only. Then check that the final supply still matches
getTokenSupply for the mint.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [HyperIndex on Solana](https://docs.envio.dev/docs/HyperIndex/solana), if you want SoFiUSD supply live behind a GraphQL API
- [Token-2022 program](https://spl.solana.com/token-2022)
- [Envio Discord](https://discord.gg/envio)
