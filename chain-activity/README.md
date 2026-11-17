# Chain activity, wallets and accounts

Scripts for chain-wide activity. Count transactions, active addresses, fees, Safes and smart accounts across a whole chain, all with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Example | Chain | How to |
| --- | --- | --- |
| [base-smart-accounts-gas-covered](base-smart-accounts-gas-covered) | Count ERC-4337 smart accounts and how many had gas covered by a paymaster |
| [active-addresses-without-dusting](active-addresses-without-dusting) | EVM chains | Count daily active addresses with dusting filtered out |
| [monad-biggest-apps](monad-biggest-apps) | Monad | Rank Monad apps by transactions over 30 days |
| [monad-volatility-day](monad-volatility-day) | Monad | Compare one day on Monad with a 30-day baseline, hour by hour |
| [gnosis-biggest-protocols](gnosis-biggest-protocols) | Gnosis | Rank the busiest protocols on Gnosis Chain |
| [ink-monthly-activity](ink-monthly-activity) | Ink | Count Ink transactions and active addresses by month |
| [polygon-october-fees](polygon-october-fees) | Polygon | Find which contracts paid the most gas on Polygon PoS |
| [arbitrum-priority-fees](../arbitrum-priority-fees) | Arbitrum | Count Arbitrum transactions paying a priority fee, day by day |
| [erc4337-user-operations-ethereum](../erc4337-user-operations-ethereum) | Ethereum | Pull every ERC-4337 user operation on Ethereum |
| [ethereum-approval-cleanups](ethereum-approval-cleanups) | Ethereum | Split ERC-20 approval revokes on Ethereum into cleanups and resets |
| [safe-growth](safe-growth) | 14 chains | Count every Safe created, by month and chain |
| [safe-shared-signer](safe-shared-signer) | Ethereum | Decode every new Safe's owners and find the most common signer |
| [safenet-staking](safenet-staking) | Ethereum | Track SAFE staked in Safenet and active stakers week by week |
| [circles-trust-gnosis](circles-trust-gnosis) | Gnosis | Count Circles v2 humans and trust links on Gnosis Chain |
| [uni-new-holders](uni-new-holders) | Ethereum | Count new UNI holders per day since 2020 |

### Also on Solana

| Example | How to |
| --- | --- |
| [solana-durable-nonces](../solana/solana-durable-nonces) | Count Solana transactions that use durable nonces |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
