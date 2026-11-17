# Safes on Ethereum that share one signer

Up to block 26,398,984 (12 Nov 2026), **272K new Safes were created on Ethereum in 2026, 3.8x the 70.9K of all of 2025**. Most of them are 2-of-2 Safes, and one owner address, `0xbe0b407782a7599380fa726db315340126d62229`, is a signer on 146K of them, 53.6% of every Safe created on Ethereum this year.

| 2026 Safes on Ethereum | |
| --- | --- |
| Created | 272,448 |
| 2-of-2 | 149,049 |
| 1-of-1 | 69,726 |
| 2-of-3 | 22,561 |
| With `0xbe0b...2229` as an owner (2-of-2) | 145,970 |

## Why it's interesting

A co-signer shared by that many new Safes only shows up when you decode every Safe's setup, which is one more event in the same HyperSync query. The same decoding works for any question about how Safes are set up, from thresholds to owners shared across accounts.

## What it pulls

All of it comes from HyperSync.

- Every `ProxyCreation` log from Safe's 1.3.0, 1.4.1 and 1.5.0 proxy factories on Ethereum since block 21,500,000 (late December 2024).
- Every `SafeSetup` log in the same range, which each Safe emits when it's set up, with its owners and threshold.
- Block timestamps, to put each Safe in a year (UTC).

Factory and singleton addresses are read from Safe's own [safe-deployments](https://github.com/safe-global/safe-deployments) repo when the script starts, the same sources as the [safe-growth](../safe-growth) example. A Safe counts when the factory's `ProxyCreation` event points at an official L1 or L2 singleton. Owners and threshold are the setup at creation, and owners can change later.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

A full run takes a few minutes. Sample output from a run on 12 Nov 2026, at about 13:00 UTC.

```
New Safes on Ethereum from Safe's 1.3.0, 1.4.1 and 1.5.0 factories, up to block 26,398,984
  2025: 70,866
  2026 so far: 272,448 (3.8x 2025)
2026 setups: 2-of-2 149,049, 1-of-1 69,726, 2-of-3 22,561, 2-of-4 4,862, 3-of-5 4,731
Most common owner across 2026 2-of-2 Safes: 0xbe0b407782a7599380fa726db315340126d62229 on 145,970 Safes (53.6% of all 2026 Safes)
Every other 2026 Safe: 126,478
```

New Safes are created every block, so your numbers will be a little higher.

## Change the window or chain

- **Window.** The script reads from `START_BLOCK` to the latest block and splits by calendar year. Move `START_BLOCK` back to include earlier years.
- **Chain.** Swap `URL` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and set `START_BLOCK` to a block on that chain just before 1 January 2025. Safe's factories sit at the same addresses on most chains.

## Check the numbers

As a comparison, we called `getOwners()` on Ethereum's public RPC for 30 random 2026 2-of-2 Safes, and all of them returned the shared signer. 40 random Safes across Ethereum and Base also returned the same owners and threshold as their `SafeSetup` event. You can check any Safe yourself in the [Safe app](https://app.safe.global) or on [Etherscan](https://etherscan.io/address/0xbe0b407782a7599380fa726db315340126d62229).

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every ProxyCreation
event from Safe's 1.3.0, 1.4.1 and 1.5.0 factories on Ethereum and every
SafeSetup event, then decodes each new Safe's owners and threshold. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Add a monthly count of 2026 Safes that include the most common owner, next to
all other 2026 Safes, and list the 10 most common owners overall. Keep the
standard library only. Then check that the monthly counts for that owner add up
to the total the script already prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Safe deployments](https://github.com/safe-global/safe-deployments)
- [Safe docs](https://docs.safe.global)
- [Envio Discord](https://discord.gg/envio)
