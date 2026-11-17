# Every Safe created, month by month

Between 1 Jan and 11 Nov 2026, **4.67M Safes were created from Safe's 1.3.0, 1.4.1 and 1.5.0 factories on 14 chains, and new Safes per month grew more than 6x, from 132K in February to 825K in September**. Base accounted for 3.61M of this year's Safes. Across all time, the same factories have made 26.1M Safes.

| Month | New Safes |
| --- | --- |
| 2026-02 | 132,039 |
| 2026-04 | 228,547 |
| 2026-06 | 525,764 |
| 2026-08 | 704,095 |
| 2026-09 | 824,853 |
| 2026-10 | 794,368 |

## Why it's interesting

Every Safe starts life as a `ProxyCreation` event from one of a few official factories, and those factories sit at the same addresses on most chains. So one query shape gives you every Safe on every chain, and you can see where smart accounts are actually being created month by month.

## What it pulls

All of it comes from HyperSync.

- Every `ProxyCreation` log from Safe's 1.3.0 `proxy_factory` (canonical and EIP-155 builds) and the 1.4.1 and 1.5.0 `safe_proxy_factory`, on Ethereum, Base, Optimism, Polygon, Arbitrum, BNB Chain, Gnosis, Avalanche, Unichain, Berachain, Scroll, Celo, Linea and Ink.
- Block timestamps, to date each Safe by its creation block in UTC.

Factory and singleton addresses are read from Safe's own [safe-deployments](https://github.com/safe-global/safe-deployments) repo when the script starts. A Safe counts when the event's singleton is one of the official `safe` or `safe_l2` contracts for those versions. Safes made by older factories (1.0.0 to 1.2.0) or zkSync's separate deployments aren't included, so these totals sit below Safe's own all-network figure of 60M+ accounts.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It reads about 26M factory events across all 14 chains and takes about 25 minutes, most of it on Optimism and Base. It also writes `safes_by_month.json` with every chain's monthly counts. Sample output from a run on 11 Nov 2026.

```
Safes created from Safe's 1.3.0, 1.4.1 and 1.5.0 factories on 14 chains, as of 11 Nov 2026 12:20 UTC

By chain (all time)
  Optimism     15,358,126
  Base          4,672,900
  Polygon       3,140,266
  BNB Chain       622,014
  Ethereum        583,796
  Gnosis          579,803
  Arbitrum        374,419
  Unichain        237,337
  Berachain       229,451
  Scroll           98,980
  Celo             68,084
  Avalanche        43,479
  Linea            28,245
  Ink              21,716
  Total        26,058,616

By month, last 24 months (2026-11 is month to date)
  2024-12    1,492,403
  2025-01    1,312,368
  2025-02      536,368
  2025-03      554,919
  2025-04      671,386
  2025-05      710,168
  2025-06    1,322,518
  2025-07    1,091,618
  2025-08    1,235,776
  2025-09      417,013
  2025-10      140,522
  2025-11      209,050
  2025-12      217,452
  2026-01      169,282
  2026-02      132,039
  2026-03      217,506
  2026-04      228,547
  2026-05      290,005
  2026-06      525,764
  2026-07      515,508
  2026-08      704,095
  2026-09      824,853
  2026-10      794,368
  2026-11      271,157

Record full month: 2024-12 with 1,492,403 Safes
Created in 2024: 8,025,621
Created in 2025: 8,419,158
Created in 2026: 4,673,124

Created in 2026 by chain
  Base          3,609,195
  Ethereum        271,489
  Gnosis          258,864
  BNB Chain       256,145
  Polygon         128,291
  Celo             56,754
  Arbitrum         50,438
  Optimism         32,647
  Avalanche         5,396
  Ink               1,147
  Berachain         1,012
  Linea               799
  Unichain            596
  Scroll              351
```

Safes keep getting created, so your numbers will be higher.

## Change the window or chain

- **Chains.** `CHAINS` maps a chain ID to a name, and the script calls `https://<chain id>.hypersync.xyz`. Trim it to run fewer chains, or add any chain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) where Safe's factories are deployed.
- **Versions.** `FACTORY_FILES` and `SINGLETON_FILES` list the safe-deployments files to read. Add a version's files to include it.
- **Window.** The script reads every block on each chain and groups by month. For a shorter period, read the monthly counts you need from `safes_by_month.json`.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every ProxyCreation
event from Safe's 1.3.0, 1.4.1 and 1.5.0 proxy factories on 14 chains and counts
new Safes by month and chain. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Run it on Base only and split the 2026 Safes by week and by singleton version
(1.3.0, 1.4.1 or 1.5.0, L1 or L2 build). Keep the standard library only. Then
check that the weekly counts add up to the Base line under "Created in 2026
by chain" from the original output.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Safe deployments](https://github.com/safe-global/safe-deployments)
- [Safe docs](https://docs.safe.global)
- [Envio Discord](https://discord.gg/envio)
