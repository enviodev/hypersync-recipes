# Active addresses without dusting

On one EVM chain over 30 Oct to 8 Nov 2026, **the busiest day had 2.77M addresses receive a token, but only 395K once dusting was dropped**. A handful of contracts sending one tiny transfer to each of thousands of addresses made daily active addresses look about 7x bigger than they were.

| Day (UTC) | Recipients | Without dusting | Dusters dropped |
| --- | --- | --- | --- |
| 2026-11-05 | 304,885 | 180,590 | 1 |
| 2026-11-06 | 644,781 | 292,094 | 5 |
| 2026-11-07 | 2,002,972 | 195,420 | 4 |
| 2026-11-08 | 2,767,882 | 395,487 | 3 |

## Why it's interesting

A sudden jump in daily active addresses is often not new users. Dusting contracts send one tiny transfer to each of thousands of addresses in a single transaction, and every one of those addresses shows up as active that day. If you report active addresses for any chain or token, this is the filter to run first.

The rule is about behaviour, not about any token, so it works on any chain HyperSync supports with no list of known spammers.

## What it pulls

All of it comes from HyperSync.

- Every log with the `Transfer` topic (`0xddf252ad...`), which covers ERC-20 and ERC-721 transfers, between the first and last block of each UTC day. The recipient is `topic2`. Transfers to the zero address, which are burns, are left out.
- For each log, the contract, the block and the transaction index, so transfers can be grouped per contract and per transaction.
- Block timestamps, to find the first block of each UTC day by binary search.

A recipient counts once per day, however many tokens it received. A contract counts as a duster on a given day when all three are true.

- It sent tokens to at least 10,000 addresses that day (`MIN_RECIPIENTS`).
- It averaged at least 20 transfers per transaction (`MIN_PER_TX`).
- At least 99% of its transfers went to a different address (`MIN_UNIQUE_SHARE`).

"Without dusting" counts recipients from every other contract, so an address that got dust and a real transfer on the same day still counts. The rule also catches genuine batch airdrops, which you may want to count separately.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

`CHAIN` is the network name HyperSync uses, the subdomain in `https://<chain>.hypersync.xyz`, for example `base` or `arbitrum`.

```bash
export ENVIO_API_TOKEN=your-token
CHAIN=base python3 script.py                                    # the last 14 full UTC days
CHAIN=base START=2026-10-30 END=2026-11-08 python3 script.py    # your own window, both days included
```

Busy chains carry millions of `Transfer` logs a day, so a long window takes a while. `WORKERS` sets how many days run in parallel (default 2), `OUT=daily.json` saves the results, and `TOP=3` also lists the biggest contracts it kept, so you can check the rule.

Sample output, the daily table from a 10-day run. Under each day the script also lists every contract it dropped, with its recipients, transfers, transactions and average batch size.

```
day            transfers   recipients  without dusting  dusters
2026-10-30     1,734,270       63,658           63,658        0
2026-10-31     1,146,356       86,771           86,771        0
2026-11-01     1,116,569      153,211          147,575        1
2026-11-02     1,336,812      100,897           94,028        1
2026-11-03     1,400,501      118,868           73,150        2
2026-11-04     1,914,031      172,683          164,919        1
2026-11-05     1,840,900      304,885          180,590        1
2026-11-06     2,267,337      644,781          292,094        5
2026-11-07     6,268,491    2,002,972          195,420        4
2026-11-08     5,979,105    2,767,882          395,487        3
```

## Change the window or chain

- **Chain.** Set `CHAIN` to any EVM network on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Window.** `START` and `END` take UTC dates, both included. With neither, it covers the 14 full days before today.
- **Rule.** `MIN_RECIPIENTS`, `MIN_PER_TX` and `MIN_UNIQUE_SHARE` are environment variables too. A quieter chain may need a lower `MIN_RECIPIENTS`. Check the dropped list before you publish a number.

## Check the numbers

Run with `TOP=3` and look at the biggest contracts the rule kept next to the ones it dropped. Then paste a dropped contract into that chain's block explorer and open one of its transactions. A duster's transaction should show one small transfer to each of hundreds of different addresses.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer log on
a chain one UTC day at a time, counts unique recipients, then counts them again
after dropping contracts that look like dusters. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a second count of unique senders per day (topic1), with and without the
dusting contracts, and include it in the OUT file. Keep the standard library
only. Run it with CHAIN=base for the last 3 days and check that the recipient
columns match a run without your change.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Wildcard indexing with HyperIndex](https://docs.envio.dev/docs/HyperIndex/wildcard-indexing), to keep this filter running live on every transfer
- [Envio Discord](https://discord.gg/envio)
