# Safes on Ethereum that share one second signer

Counts every Safe created on Ethereum in 2025 and 2026 with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), decodes each one's owners and threshold, and finds the owner that appears on the most 2026 Safes.

These are the numbers behind Envio's post on new Safes on Ethereum in 2026.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

A full run takes a few minutes.

## What it prints

```
New Safes on Ethereum from Safe's 1.3.0, 1.4.1 and 1.5.0 factories, up to block 26,398,984
  2025: 70,866
  2026 so far: 272,448 (3.8x 2025)
2026 setups: 2-of-2 149,049, 1-of-1 69,726, 2-of-3 22,561, 2-of-4 4,862, 3-of-5 4,731
Most common owner across 2026 2-of-2 Safes: 0xbe0b407782a7599380fa726db315340126d62229 on 145,970 Safes (53.6% of all 2026 Safes)
Every other 2026 Safe: 126,478
```

That run was on 12th November 2026, at about 13:00 UTC. New Safes are created every block, so your numbers will be a little higher.

## How it counts

- Factories and singletons come from Safe's own [safe-deployments](https://github.com/safe-global/safe-deployments) repo: the 1.3.0, 1.4.1 and 1.5.0 proxy factories, and the L1 and L2 Safe singletons for each version. These are the same sources as the [safe-growth](../safe-growth) recipe, and the yearly totals match it.
- A Safe counts when a factory's `ProxyCreation` event points at an official singleton. Its year is the UTC timestamp of that block.
- Owners and threshold come from the `SafeSetup` event each Safe emits when it is set up. This is the setup at creation; owners can change later.
- Checked against Ethereum's public RPC: 30 random 2026 2-of-2 Safes all returned the shared signer from `getOwners()`, and 40 random Safes across Ethereum and Base returned the same owners and threshold as their `SafeSetup` event.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Ethereum (endpoint
https://1.hypersync.xyz) to read every ProxyCreation event from Safe's 1.3.0, 1.4.1 and 1.5.0
proxy factories (addresses from github.com/safe-global/safe-deployments) and every SafeSetup
event. My API token is in the ENVIO_API_TOKEN environment variable. Count new Safes per year
and find which owner address appears on the most 2026 2-of-2 Safes.
```

## Learn more

- [HyperSync docs](https://docs.envio.dev/docs/HyperSync/overview)
- [Safe deployments](https://github.com/safe-global/safe-deployments)
