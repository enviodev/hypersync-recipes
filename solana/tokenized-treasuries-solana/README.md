# Tokenized Treasury funds on Solana, day by day

**J.P. Morgan's JLTXX fund went from 17M tokens on Solana at the end of 18 Oct 2026 to 740.8M at the end of 1 Nov, about $741M at $1 a token**. It passed 450.3M a week in, on 25 Oct. The script tracks it alongside four other Treasury funds on Solana from BlackRock, Ondo, State Street and Galaxy.

| Fund | Manager | Mint |
| --- | --- | --- |
| JLTXX | J.P. Morgan | [`J4cTuCH6frt4AnEmKfMS2k8hsUf7K94PV62sjUJno8Cz`](https://explorer.solana.com/address/J4cTuCH6frt4AnEmKfMS2k8hsUf7K94PV62sjUJno8Cz) |
| BUIDL | BlackRock, via Securitize | [`GyWgeqpy5GueU2YbkE8xqUeVEokCMMCEeUrfbtMw6phr`](https://explorer.solana.com/address/GyWgeqpy5GueU2YbkE8xqUeVEokCMMCEeUrfbtMw6phr) |
| SHVon | Ondo, tracks iShares SHV | [`XDZNiWPHH8fyb8PCyTeiJsVsBnBhkBZbcYoxvVpondo`](https://explorer.solana.com/address/XDZNiWPHH8fyb8PCyTeiJsVsBnBhkBZbcYoxvVpondo) |
| SWEEP | State Street and Galaxy | [`AgBSDfS7CNRunBeREHHdF9S57fai5b3EXH1hgvZkRPhB`](https://explorer.solana.com/address/AgBSDfS7CNRunBeREHHdF9S57fai5b3EXH1hgvZkRPhB) |
| USDY | Ondo | [`A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6`](https://explorer.solana.com/address/A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6) |

## Why it's interesting

Some of the biggest names in asset management now issue Treasury funds straight onto Solana, and a new one can reach hundreds of millions in days. A daily supply series is the clearest way to see that happen. The trick here works for any SPL token. Every balance change in a transaction nets out to that transaction's mints minus burns, so you get supply over time without decoding a single instruction.

## What it pulls

- Every token balance change for the five mints, as `account_activity` rows from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). The daily net mints and burns come from HyperSync.
- Today's supply for each mint from Solana's public RPC with `getTokenSupply`. The script starts from that number and walks back through each day's net change, so the anchor comes from RPC and the day-by-day changes come from HyperSync.

Every Solana transaction that touches a token account lists each account's balance before and after. Summed over a transaction, transfers cancel out, so what's left is that transaction's mints minus burns.

JLTXX and BUIDL are priced at $1 a token and SWEEP a little above. SHVon tracks one SHV share, and USDY trades a little above $1. The table below is in fund tokens, not dollars.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py       # the last 65 days
python3 script.py 40    # the last 40 days
```

It reads in parallel and takes about 15 minutes for 40 days. Sample output from `python3 script.py 40` on 4 Nov 2026:

```
Fund supply in tokens at the end of each week
                                 27 Sep   04 Oct   11 Oct   18 Oct   25 Oct   01 Nov
JLTXX (J.P. Morgan)                0.0M      0.0M      0.0M     17.0M    450.3M    740.8M
BUIDL (BlackRock)                987.9M    967.6M    931.1M    885.6M    886.4M    812.7M
SHVon (Ondo)                       1.9M      2.1M      2.3M      2.7M      2.8M      3.1M
SWEEP (State Street, Galaxy)     156.4M    156.4M    156.4M    161.3M    205.7M    205.7M
USDY (Ondo)                      156.5M    156.5M    156.5M    156.5M    156.5M    156.5M
```

## Change the window or chain

- **Window.** Pass a number of days. Longer windows take longer, since the script reads every balance change in them.
- **Another token.** Add any SPL mint to the `FUNDS` dict, a stablecoin, a stock token or another fund, and you'll get its daily supply in the same table.
- **Slot range.** The [HyperSync Solana docs](https://docs.envio.dev/docs/HyperSync/solana) cover the slot range and the query fields if you want to go further back or pull other columns.

## Check the numbers

JLTXX, SHVon and SWEEP launched inside HyperSync's Solana range. Summing their changes from launch with HyperSync alone lands on the `getTokenSupply` figure from Solana's RPC to the last unit, which is the comparison. You can also check any mint's current supply on the [Solana Explorer](https://explorer.solana.com).

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana) to read every account_activity row for
five tokenized Treasury fund mints and rebuild each fund's supply day by day.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a column for the number of distinct token accounts that received each fund each
day, from the same account_activity rows, and write the daily table to daily.csv.
Keep the standard library only. Run it with 14 days first. Then check that JLTXX supply
summed from its launch day matches getTokenSupply.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Envio Discord](https://discord.gg/envio)
