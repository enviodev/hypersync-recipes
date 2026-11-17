# Real-world collateral on Kamino Lend

On 16 Nov 2026, **$378M of tokenized real-world credit sat as collateral in five Kamino Lend markets on Solana, with $257M borrowed against it**. Reinsurance (ONyc) was the biggest at $166M, then car loans (AUTO) at $98M, home equity (PRIME) at $84M and payments financing (PST) at $30M.

| Real-world collateral | Supplied |
|---|---:|
| ONyc (reinsurance, OnRe) | $165.8M |
| AUTO (US car loans, Hastra) | $98.3M |
| PRIME (home equity lines of credit, Hastra) | $83.5M |
| PST (payments financing, Huma) | $30.1M |
| Total | $377.7M |

| Borrowed against it | Amount |
|---|---:|
| USDC | $107.6M |
| wYLDS | $62.9M |
| USDG | $36.3M |
| PYUSD | $28.6M |
| CASH | $21.8M |
| Total | $257.3M |

## Why it's interesting

Car loans, home equity and reinsurance are now working collateral in a Solana money market, and stablecoins are being borrowed against them. Each Kamino market is a set of reserve accounts, so you can read what's supplied and borrowed straight from the chain, reserve by reserve.

## What it pulls

| Market | Address | Collateral |
|---|---|---|
| OnRe | `47tfyEG9SsdEnUm9cw5kY9BXngQGqu3LBoop9j5uTAv8` | ONyc |
| AUTO | `Btu8835QDYgdTnMJJBSidbfQhrZzryZbMhCpty6h6Xdk` | AUTO |
| Figure | `CqAoLuqWtavaVE8deBjMKe8ZfSt9ghR6Vb8nfsyabyHA` | PRIME |
| Huma | `52FSGeeokLpgvgAMdqxyt5Hoc2TbUYj5b8yxrEdZ37Vf` | PST |
| Sentora Huma PST | `CyyFApdfEzHM5dVowALutPiL3fZepMrThtQUed77A1KN` | PST |

- **Reserves.** `getProgramAccounts` on the [Kamino Lend](https://kamino.com/docs) program `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD` over Solana RPC, filtered on the 8,624-byte reserve size and the lending market at offset 32. Then `getMultipleAccounts` reads each reserve.
- **Reserve state.** Each reserve's `ReserveLiquidity` gives the token mint, the supply vault, `available_amount`, `borrowed_amount_sf` and `market_price_sf`, the price Kamino itself uses. Supplied is available plus borrowed, valued at that price. Reserves under $1M supplied are left out, and the borrowed totals count reserves with at least $1M borrowed.
- **Vault balances.** HyperSync's `account_activity` table gives the latest token balance of every supply vault, walking back up to about six days of slots. The script prints whether it matches the reserve's `available_amount`.

To be upfront about where the numbers come from, the supplied and borrowed totals come from reserve accounts read over public Solana RPC, priced with Kamino's own reserve prices. [HyperSync](https://docs.envio.dev/docs/HyperSync/solana) is the independent read of each vault's balance that checks the reserve decoding.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
SOLANA_RPC=https://your-rpc python3 script.py   # use your own RPC instead of the public one
```

It prints one line per reserve, then the totals, and writes them to `kamino_rwa.json`. The end of a run on 16 Nov 2026.

```
Real-world collateral
  Reinsurance (OnRe ONyc)          $  165.8M
  Car loans (Hastra AUTO)          $   98.3M
  Home equity (Hastra PRIME)       $   83.5M
  Payments financing (Huma PST)    $   30.1M
  Total                            $  377.7M

Borrowed against it
  USDC                             $  107.6M
  wYLDS                            $   62.9M
  USDG                             $   36.3M
  PYUSD                            $   28.6M
  CASH                             $   21.8M
  Total                            $  257.3M
```

Reserve balances change every slot, so your numbers will differ.

## Change the markets

- **Another Kamino market.** Add its address to `MARKETS` with a label and the mint of the asset you want counted as collateral. Add any new token mints to `SYMBOLS` so they print by name.
- **Thresholds.** The $1M cut-offs sit next to `supplied` and `usd_borrowed` near the bottom of `script.py`.
- **Vault lookback.** `vault_balances` walks back up to 1.3M slots. Raise it if a quiet vault shows `HyperSync None`.

## Check the numbers

Each reserve line ends with `vault matches` when HyperSync's latest balance for the supply vault equals the reserve's `available_amount`. In our 16 Nov run, 17 of 22 reserves matched. Three vaults had no activity in the lookback window, and the two PYUSD vaults showed a different balance, so those reserves rest on the RPC read alone.

We also compared every figure with Kamino's own reserve metrics, and they matched to within rounding.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It finds every reserve of five Kamino
Lend RWA markets over Solana RPC, decodes supplied and borrowed amounts, and checks
each supply vault's balance with HyperSync account_activity
(https://docs.envio.dev/docs/HyperSync/solana-query). My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a daily history of each RWA supply vault's balance for the last 30 days, built
from HyperSync account_activity post_token_balance rows. Keep the standard library
only. Run it on one market first and check that the latest day equals the
available_amount the script already prints for that reserve.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana) and its [query reference](https://docs.envio.dev/docs/HyperSync/solana-query)
- [Kamino docs](https://kamino.com/docs)
- [Envio Discord](https://discord.gg/envio)
