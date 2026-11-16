# SoFiUSD on Solana

Rebuilds the supply of SoFiUSD, the stablecoin issued by SoFi Bank, on Solana from every mint and burn, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana).

SoFiUSD on Solana is the Token-2022 mint `APhcqtzE73es3KAGiVksZFMLGwJDiAey5qZKUrQHEHfS` (symbol SOFID, 6 decimals; its onchain metadata reads "SoFi USD is a stablecoin backed 1:1 by US dollars, issued by SoFi").

## What we found

On 16th November 2026:

- 421 mints and burns since the first mint on 28th April 2026
- Supply of $274M, with the month-end supply higher every month since June
- A new mint on every weekday since 1st September, $179M minted in total over that time

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

Minted, burned and month-end supply per month, then the total supply. The total matches Solana RPC `getTokenSupply` for the mint to the cent (274,066,133.48 at slot 470,149,545).

## How it counts

- Mints are Token-2022 `MintTo` (tag 7) and `MintToChecked` (tag 14) instructions with the SoFiUSD mint as account 0. Burns are `Burn` (tag 8) and `BurnChecked` (tag 15) with the mint as account 1. The script asks HyperSync for those with the `d1`, `a0` and `a1` filters, then checks the tag and the mint again in code.
- The amount is the little-endian u64 after the one-byte tag, divided by 10^6.
- HyperSync serves successful transactions' instructions, so failed mints and burns are never counted.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) to find every Token-2022
(TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb) MintTo or MintToChecked instruction with a0 = APhcqtzE73es3KAGiVksZFMLGwJDiAey5qZKUrQHEHfS,
and every Burn or BurnChecked with a1 = that mint, from slot 370000000 to the head. My API token is in the
ENVIO_API_TOKEN environment variable. Rebuild the SoFiUSD supply over time and print it by month.
```
