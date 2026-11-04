# Tokenized Treasury funds on Solana

Reads every token balance change of the five biggest tokenized Treasury funds on Solana with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/solana) and rebuilds each fund's supply day by day.

These are the numbers behind Envio's post on J.P. Morgan's JLTXX reaching $741M on Solana in under two weeks.

| Fund | Manager | Mint |
|---|---|---|
| JLTXX | J.P. Morgan | `J4cTuCH6frt4AnEmKfMS2k8hsUf7K94PV62sjUJno8Cz` |
| BUIDL | BlackRock, via Securitize | `GyWgeqpy5GueU2YbkE8xqUeVEokCMMCEeUrfbtMw6phr` |
| SHVon | Ondo, tracks iShares SHV | `XDZNiWPHH8fyb8PCyTeiJsVsBnBhkBZbcYoxvVpondo` |
| SWEEP | State Street and Galaxy | `AgBSDfS7CNRunBeREHHdF9S57fai5b3EXH1hgvZkRPhB` |
| USDY | Ondo | `A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6` |

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a number of days to change the window, for example `python script.py 40`. It reads in parallel and takes about 15 minutes for 40 days.

## What it prints

Supply in fund tokens at the end of each week. JLTXX and BUIDL are priced at $1 a token and SWEEP a little above. SHVon tracks one SHV share and USDY trades a little above $1.

```
Fund supply in tokens at the end of each week
                                 27 Sep   04 Oct   11 Oct   18 Oct   25 Oct   01 Nov
JLTXX (J.P. Morgan)                0.0M      0.0M      0.0M     17.0M    450.3M    740.8M
BUIDL (BlackRock)                987.9M    967.6M    931.1M    885.6M    886.4M    812.7M
SHVon (Ondo)                       1.9M      2.1M      2.3M      2.7M      2.8M      3.1M
SWEEP (State Street, Galaxy)     156.4M    156.4M    156.4M    161.3M    205.7M    205.7M
USDY (Ondo)                      156.5M    156.5M    156.5M    156.5M    156.5M    156.5M
```

That is `python script.py 40`, run on 4th Nov.

## How it counts

- Every Solana transaction that touches a token account lists each account's balance before and after. HyperSync serves these as `account_activity` rows, filtered here by mint.
- Summed over a transaction, the before and after balances cancel out for transfers, so what's left is that transaction's mints minus burns.
- The script reads today's supply with Solana RPC `getTokenSupply` and walks back through each day's net change.
- JLTXX, SHVon and SWEEP launched inside HyperSync's Solana range. Summing their changes from launch lands on today's onchain supply to the last unit.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync for Solana (https://docs.envio.dev/docs/HyperSync/solana) to read
every account_activity row for the JLTXX mint J4cTuCH6frt4AnEmKfMS2k8hsUf7K94PV62sjUJno8Cz
since slot 451000000. My API token is in the ENVIO_API_TOKEN environment variable.
Sum post_token_balance minus pre_token_balance per UTC day and chart the fund's supply.
```
