# Real-world collateral on Kamino

Finds how much tokenized car loans, home equity, reinsurance and payments financing sit as collateral on [Kamino](https://kamino.com) Lend on Solana, and what is borrowed against them, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana) and Solana RPC.

It covers five Kamino lending markets built around a real-world asset:

| Market | Collateral |
|---|---|
| OnRe | ONyc (reinsurance) |
| AUTO | AUTO (US car loans, from Hastra) |
| Figure | PRIME (home equity lines of credit, from Hastra) |
| Huma and Sentora Huma PST | PST (payments financing, from Huma) |

## What we found

On 16th November 2026:

- $378M of real-world collateral across these markets: ONyc $166M, AUTO $98M, PRIME $84M, PST $30M
- $257M borrowed against it: USDC $108M, wYLDS $63M, USDG $36M, PYUSD $29M, CASH $22M

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It uses the public Solana RPC by default. Set `SOLANA_RPC` to use your own.

## How it works

- Each market's reserves are found with `getProgramAccounts` on the Kamino Lend program (`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`), filtered on the 8,624-byte reserve size and the lending market at offset 32.
- Each reserve's `ReserveLiquidity` gives the token mint, the supply vault, `available_amount`, `borrowed_amount_sf` and `market_price_sf` (the price Kamino itself uses). Supplied is available plus borrowed, valued at that price.
- HyperSync's `account_activity` table gives the latest token balance of every supply vault. The script prints whether it matches the reserve's `available_amount`, which checks the reserve decoding against an independent read of the chain.
- Borrowed totals count reserves with at least $1M borrowed.
- We also checked every figure against Kamino's own reserve metrics API, and they matched to within rounding.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana-query) and Solana RPC to
list every reserve of the Kamino Lend markets 47tfyEG9SsdEnUm9cw5kY9BXngQGqu3LBoop9j5uTAv8 (OnRe),
Btu8835QDYgdTnMJJBSidbfQhrZzryZbMhCpty6h6Xdk (AUTO), CqAoLuqWtavaVE8deBjMKe8ZfSt9ghR6Vb8nfsyabyHA (Figure),
52FSGeeokLpgvgAMdqxyt5Hoc2TbUYj5b8yxrEdZ37Vf and CyyFApdfEzHM5dVowALutPiL3fZepMrThtQUed77A1KN (Huma).
For each reserve, decode the supply vault, available amount, borrowed amount and price, and read the vault's
latest token balance from HyperSync account_activity. My API token is in the ENVIO_API_TOKEN environment variable.
Print the collateral and borrowed totals per market in USD.
```
