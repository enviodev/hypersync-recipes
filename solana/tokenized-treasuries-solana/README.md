# Tokenized Treasury funds on Solana, day by day

**J.P. Morgan's JLTXX fund went from 17M tokens on Solana at the end of 17 Oct 2026 to 740.8M at the end of 31 Oct, about $741M at $1 a token**. It passed 450.3M a week in, on 24 Oct, and held 738.0M on 14 Nov. Every JLTXX figure is summed by HyperSync from the fund's first mint. The script tracks it alongside four other Treasury funds on Solana from BlackRock, Ondo, State Street and Galaxy.

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
- JLTXX, SHVon and SWEEP launched after slot 391,000,000, where HyperSync's Solana history starts. Their first balance change is after slot 416,000,000, so the script reads from there and their supply is every change HyperSync returns, summed from zero. HyperSync produces those numbers on its own, the JLTXX headline included.
- BUIDL and USDY are older than HyperSync's Solana history, so their rows start from today's supply on Solana's public RPC (`getTokenSupply`) and walk back through HyperSync's daily changes. They're marked `*` in the output.

Every Solana transaction that touches a token account lists each account's balance before and after. Summed over a transaction, transfers cancel out, so what's left is that transaction's mints minus burns.

JLTXX and BUIDL are priced at $1 a token and SWEEP a little above. SHVon tracks one SHV share, and USDY trades a little above $1. The table below is in fund tokens, not dollars.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py       # the last 65 days
python3 script.py 40    # the last 40 days
```

It always reads from slot 416,000,000, so the newer funds are summed from launch, and takes about 15 minutes. Sample output from `python3 script.py 40` on 17 Nov 2026.

```
Fund supply in tokens at the end of each week
                                 10 Oct   17 Oct   24 Oct   31 Oct   07 Nov   14 Nov
JLTXX (J.P. Morgan)                0.0M     17.0M    450.3M    740.8M    737.4M    738.0M
BUIDL (BlackRock) *              931.1M    885.6M    886.4M    812.7M    540.6M    467.3M
SHVon (Ondo)                       2.3M      2.7M      2.8M      3.1M      3.3M      3.9M
SWEEP (State Street, Galaxy)     156.4M    161.3M    205.7M    205.7M    205.7M    254.8M
USDY (Ondo) *                    156.5M    156.5M    156.5M    156.5M     41.8M      7.1M
* starts from Solana RPC getTokenSupply, since the fund is older than HyperSync's Solana history
Check (RPC getTokenSupply, read after the HyperSync pull)
  JLTXX (J.P. Morgan): HyperSync 738,042,856.35, RPC 738,042,856.35 (match)
  SHVon (Ondo): HyperSync 3,799,751.38, RPC 3,799,751.38 (match)
  SWEEP (State Street, Galaxy): HyperSync 254,812,619.61, RPC 254,812,619.61 (match)
```

## Change the window or chain

- **Window.** Pass a number of days. Windows reaching back before slot 416,000,000 take longer, since the script reads every balance change in them.
- **Another token.** Add any SPL mint to the `FUNDS` dict, a stablecoin, a stock token or another fund, and you'll get its daily supply in the same table.
- **Slot range.** The [HyperSync Solana docs](https://docs.envio.dev/docs/HyperSync/solana) cover the slot range and the query fields if you want to go further back or pull other columns.

## Check the numbers

The script checks itself on every run. For JLTXX, SHVon and SWEEP it prints the supply HyperSync summed from launch next to `getTokenSupply` from Solana's public RPC, read straight after. In the 17 Nov run all three matched to the last unit. If a mint or burn lands between the HyperSync pull and the RPC read, the line says so. You can also check any mint's current supply on the [Solana Explorer](https://explorer.solana.com).

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
Read script.py and README.md in this folder. It uses HyperSync on Solana
(https://docs.envio.dev/docs/HyperSync/solana) to read every account_activity row for
five tokenized Treasury fund mints and rebuild each fund's supply day by day.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a column for the number of distinct token accounts that received each fund each
day, from the same account_activity rows, and write the daily table to daily.csv.
Keep the standard library only. Run it with 14 days first. Then check that the JLTXX
supply it prints still matches getTokenSupply.
```

## Links

- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Envio Discord](https://discord.gg/envio)
