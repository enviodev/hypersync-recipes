# The busiest protocols on Gnosis Chain

Over 30 days, blocks 48,617,467 to 49,121,828, **Lido's Data Bus was the busiest protocol on Gnosis Chain with 1.17M transactions**, then HOPR with 984K and Balancer with 811K. Gnosis Pay settled 117K card payments from 6K card accounts.

| Protocol | Transactions | Wallets sending |
| --- | --- | --- |
| Lido Data Bus | 1,166,544 | 13 |
| HOPR | 984,259 | 566 |
| Balancer | 810,517 | 1,558 |
| Spark | 403,666 | 323 |
| Aave | 346,510 | 1,009 |
| Circles | 138,149 | 208 |
| Gnosis Pay | 116,637 | 1 |
| Olas | 110,266 | 192 |
| CoW Protocol | 85,696 | 121 |

## Why it's interesting

Ranking a chain's protocols needs a clean definition of "touched". This script counts a transaction for a protocol when it emitted at least one event from that protocol's core contracts, which catches calls that come through routers, relayers and other contracts too. Wallets sending tells you how many addresses drive that activity, which for several protocols here is a small set of operators, relayers or bots. Gnosis Pay is the clearest case, with every card payment sent by Gnosis Pay itself.

## What it pulls

All of it comes from HyperSync.

- Every log from the core contracts below, joined to the transaction that emitted it, so each transaction and its sender are counted once per protocol.
- Gnosis Pay's `Spend` events, whose second data word is the card account's Safe.
- Block timestamps, to find the block 30 days back by binary search.

| Protocol | Contracts | Source |
| --- | --- | --- |
| Lido Data Bus | `0x37De961D6bb5865867aDd416be07189D2Dd960e6` | [Lido deployed contracts](https://docs.lido.fi/deployed-contracts/#data-bus) |
| HOPR | channels `0x75Ce59332721E3aE3064cb9652BCE35FFCE3f8E6`, `0x860f50B24Ba6A862736c5045747323e03aa52Aa4` | [hoprnet/contracts](https://github.com/hoprnet/contracts/blob/main/ethereum/bindings/contracts-addresses.json), the two production networks |
| Balancer | Vault V2 `0xBA12222222228d8Ba445958a75a0704d566BF2C8`, Vault V3 `0xbA1333333333a1BA1108E8412f11850A5C319bA9` | [Balancer frontend config](https://github.com/balancer/frontend-monorepo/blob/main/packages/lib/config/networks/gnosis.ts) |
| Spark | Pool `0x2Dae5307c5E3FD1CF5A72Cb6F698f915860607e0` | [spark-address-registry](https://github.com/sparkdotfi/spark-address-registry/blob/master/src/Gnosis.sol) |
| Aave | V3 Pool `0xb50201558B00496A145fE76f7424749556E326D8` | [aave-address-book](https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Gnosis.sol) |
| Circles | v2 Hub `0xc12C1E50ABB450d6205Ea2C3Fa861b3B834d13e8` | [circles-sdk](https://github.com/aboutcircles/circles-sdk/blob/dev/packages/sdk/src/config.ts) |
| Gnosis Pay | spend modules `0x5f07734E2B9C4dE6f9C32253d485741800da3F8a`, `0xcFF260bfbc199dC82717494299b1AcADe25F549b` | [Gnosisscan](https://gnosisscan.io/address/0x5f07734E2B9C4dE6f9C32253d485741800da3F8a) |
| Olas | Mech Marketplace `0x735FAAb1c4Ec41128c367AFb5c3baC73509f70bB` | [olas-operate-app](https://github.com/valory-xyz/olas-operate-app/blob/main/frontend/config/mechs.ts) |
| CoW Protocol | GPv2Settlement `0x9008D19f58AAbD9eD0D60971565AA8510560ab41` | [CoW Protocol docs](https://docs.cow.fi/cow-protocol/reference/contracts/core) |

The list covers protocols we could label from their own docs, repos or explorer. Tokens, bridges, account abstraction infrastructure and contracts without a public owner are left out, even when they're busy.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                        # the last 30 days up to the latest block
python3 script.py 48617467 49121828      # the blocks used above
```

It reads several million events, so a run takes a while. Sample output with blocks 48617467 to 49121828.

```
Busiest protocols on Gnosis Chain, blocks 48,617,467 to 49,121,828 (30 days)
                  transactions   wallets sending
  Lido Data Bus      1,166,544                13
  HOPR                 984,259               566
  Balancer             810,517             1,558
  Spark                403,666               323
  Aave                 346,510             1,009
  Circles              138,149               208
  Gnosis Pay           116,637                 1
  Olas                 110,266               192
  CoW Protocol          85,696               121
Gnosis Pay: 116,637 card payments from 6,010 card accounts (its transactions are sent by Gnosis Pay, not the cardholder)
```

With a fixed block range the numbers won't change. Without one, the window moves with the chain.

## Change the window or chain

- **Window.** Pass a start and end block. With none, the script goes back 30 days from the latest block by binary search on block timestamps. It looks in the last 700,000 blocks, so for a longer window widen `lo` in the search too.
- **Protocols.** `PROTOCOLS` maps a name to its contracts. Add or remove protocols there.
- **Chain.** Swap `URL` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and fill `PROTOCOLS` with that chain's contracts.

## Check the numbers

As a comparison, every transaction count was checked against `eth_getLogs` on the public Gnosis RPC (`rpc.gnosischain.com`) for the same blocks, and they matched exactly.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every event from the
core contracts of nine Gnosis Chain protocols and ranks them by transactions
and sending wallets. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Add a daily breakdown, with transactions per protocol per UTC day, using block
timestamps, and write it to daily.csv. Keep the standard library only. Run it
with blocks 48617467 49121828 and check that each protocol's daily counts add up
to its 30-day total.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Gnosis Chain docs](https://docs.gnosischain.com)
- [Envio Discord](https://discord.gg/envio)
