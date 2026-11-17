# Safenet staking on Ethereum

Up to Ethereum block 26,427,839 (16 Nov 2026), **66.3M SAFE was staked in Safenet by 891 wallets**, 6.63% of the 1B SAFE supply. Staking opened in week 14 of 2026 with 22 wallets, passed 500 by the end of June and reached 891. Stakers have claimed **4.3M SAFE in rewards** across 129 wallets.

| | Up to block 26,427,839 |
| --- | --- |
| SAFE staked | 66,323,792 |
| Share of SAFE supply | 6.63% |
| Active stakers | 891 |
| Rewards claimed | 4,343,045 SAFE |
| Wallets that claimed | 129 |

## Why it's interesting

Safenet stakers back the validators that check Safe transactions, so the staked total and the number of stakers show how much of the SAFE community is taking part. The whole history fits in two contracts and three events, which makes this a good template for rebuilding any staking contract's state from its logs, with no archive node.

## What it pulls

- `StakeIncreased` and `WithdrawalInitiated` from the Safenet Staking contract [`0x115E78f160e1E3eF163B05C84562Fa16fA338509`](https://etherscan.io/address/0x115E78f160e1E3eF163B05C84562Fa16fA338509).
- `Claimed` from the Safenet reward distribution contract [`0xe5139Fc0FB8eae81e30d8a85C22E88c6757120f2`](https://etherscan.io/address/0xe5139Fc0FB8eae81e30d8a85C22E88c6757120f2).

Both addresses are listed on Safe's [contracts and audits](https://docs.safefoundation.org/safenet-aegis/resources/contracts-and-audits) page. A wallet's stake goes up on `StakeIncreased` and down on `WithdrawalInitiated`. An active staker is a wallet with more than zero SAFE staked across all validators. Rewards claimed is the sum of every `Claimed` event. Every number here comes from HyperSync.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes about two minutes. Sample output from a run on 16 Nov 2026.

```
Safenet staking on Ethereum, up to block 26,427,839
  SAFE staked: 66,323,792 (6.63% of the 1B SAFE supply)
  Active stakers: 891
  SAFE rewards claimed so far: 4,343,045 by 129 wallets
Week by week (SAFE staked, active stakers):
  2026-W14     4,092,878    22
  2026-W15    15,427,254    91
  2026-W16    40,027,748   199
  ...
  2026-W26    54,777,793   526
  ...
  2026-W45    69,791,731   890
  2026-W46    66,323,792   891
```

Stakes move every week, so your numbers will differ.

## Change the window or chain

- **Start.** The two start blocks are passed to `logs()` in `main()`. They sit just before each contract's first event, so leave them unless you want a later starting point.
- **Weekly or daily.** The series is keyed on the ISO week (`%G-W%V`). Change that format string to `%Y-%m-%d` for a daily series.
- **Other staking contracts.** Swap `STAKING`, `REWARDS` and the topic hashes for any contract that emits stake and withdraw events, and `URL` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).

## Check the numbers

The Staking contract keeps its own total. As the RPC comparison, at block 26,427,839 `totalStakedAmount()` returns 66,323,792.21 SAFE, the same as the rebuild.

```bash
cast call 0x115E78f160e1E3eF163B05C84562Fa16fA338509 "totalStakedAmount()(uint256)" \
  --rpc-url https://ethereum-rpc.publicnode.com --block 26427839
```

`totalStakerStakes(address)` does the same for any one staker. As an outside comparison, Safe's [Q2 2026 report](https://safefoundation.org/reports/q2-2026) gives 539 active stakers and 54.8M SAFE staked at 30 June. The weekly series shows 526 stakers and 54.8M SAFE in week 26, which ends 28 June.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to rebuild Safenet staking on
Ethereum from StakeIncreased, WithdrawalInitiated and Claimed events. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Add an optional end block argument so I can rebuild the state at any past block.
Then add a per-validator breakdown (StakeIncreased carries the staker and the
validator, so check the contract ABI on Etherscan for which topic is which) and
print the ten validators with the most SAFE staked. Keep the standard library
only. Check the total against totalStakedAmount() on
0x115E78f160e1E3eF163B05C84562Fa16fA338509 at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Raw HTTP query examples](https://docs.envio.dev/docs/HyperSync/hypersync-curl-examples), the same plain requests this script makes
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Safenet contracts and audits](https://docs.safefoundation.org/safenet-aegis/resources/contracts-and-audits)
- [Safe Foundation Q2 2026 report](https://safefoundation.org/reports/q2-2026)
- [Envio Discord](https://discord.gg/envio)
