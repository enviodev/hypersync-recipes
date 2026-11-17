# Safenet staking on Ethereum

Rebuilds Safenet staking from its onchain events with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview): how much SAFE is staked, how many wallets are actively staking week by week since launch, and how much SAFE has been claimed in rewards.

These are the numbers behind Envio's post on Safenet stakers.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It takes under a minute.

## What it prints

```
Safenet staking on Ethereum, up to block 26,400,141
  SAFE staked: 71,430,389 (7.14% of the 1B SAFE supply)
  Active stakers: 892
  SAFE rewards claimed so far: 4,342,928 by 129 wallets
Week by week (SAFE staked, active stakers):
  2026-W14     4,092,878    22
  ...
  2026-W46    71,430,389   892
```

That run was on 12th November 2026. Your numbers will move as people stake, withdraw and claim.

## How it counts

- Contracts come from Safe's own docs, [Contracts and audits](https://docs.safefoundation.org/safenet-aegis/resources/contracts-and-audits): Staking `0x115E78f160e1E3eF163B05C84562Fa16fA338509` and Reward distribution `0xe5139Fc0FB8eae81e30d8a85C22E88c6757120f2`, both on Ethereum.
- A wallet's stake goes up on `StakeIncreased` and down on `WithdrawalInitiated`. An active staker is a wallet with more than zero SAFE staked across all validators.
- Rewards claimed is the sum of every `Claimed` event on the reward distribution contract.
- Checked against Ethereum's public RPC: the rebuilt total equals the Staking contract's `totalStakedAmount()` on two RPC providers, and 10 random stakers' `totalStakerStakes()` match.
- At 30th June the rebuild gives 539 active stakers and 54.8M SAFE staked, the same figures as [Safe's Q2 2026 report](https://safefoundation.org/reports/q2-2026).
