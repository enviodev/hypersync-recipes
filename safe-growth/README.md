# Every Safe created, month by month

Reads every `ProxyCreation` event from Safe's canonical proxy factories (1.3.0, 1.4.1 and 1.5.0) on 14 chains with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then counts the new Safes by month and by chain.

These are the numbers behind Envio's post on Safe's growth in 2026.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It reads about 26 million factory events across all 14 chains and takes about 25 minutes, most of it on Optimism and Base. To run fewer chains, trim the `CHAINS` list at the top of the script. It also writes `safes_by_month.json` with every chain's monthly counts.

## What it prints

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

Across the 14 chains, 4,673,124 Safes were created between 1st January and 11th November 2026, and new Safes per month went from 132,039 in February to 824,853 in September, more than 6x. Base made up 3,609,195 of this year's Safes, and September was its biggest month yet with 761,332. Your numbers will be higher, since Safes keep getting created.

## How it counts

- Factory and singleton addresses come from Safe's own [safe-deployments](https://github.com/safe-global/safe-deployments) repo: the 1.3.0 `proxy_factory` (canonical and EIP-155 builds), the 1.4.1 and 1.5.0 `safe_proxy_factory`, and the `safe` and `safe_l2` singletons of each version.
- A Safe counts when a factory emits `ProxyCreation` for a proxy whose singleton is one of those official Safe contracts, L1 or L2 build. Proxies pointing at anything else are left out.
- Each Safe is dated by its creation block, grouped by calendar month in UTC.
- Safes made by older factories (1.0.0 to 1.2.0) or zkSync's separate deployments are not included, so the totals here sit below Safe's own all-network figure of 60M+ accounts.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) and Safe's deployments repo
(https://github.com/safe-global/safe-deployments) to read every ProxyCreation event from Safe's
1.3.0, 1.4.1 and 1.5.0 proxy factories on Base. My API token is in the ENVIO_API_TOKEN environment
variable. Show me new Safes per week for 2026, and which singleton version each one uses.
```
