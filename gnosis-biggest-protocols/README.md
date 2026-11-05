# The busiest protocols on Gnosis Chain

Reads every event from the core contracts of nine Gnosis Chain protocols over the last 30 days with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then ranks them by the number of transactions that touched them. It also counts Gnosis Pay card payments and the card accounts behind them.

These are the numbers behind Envio's post on the busiest protocols on Gnosis.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

With no arguments it reads the last 30 days up to the latest block. Pass a block range to rerun an exact window. The post used blocks 48,617,467 to 49,121,828.

```bash
python script.py 48617467 49121828
```

## What it prints

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

It reads several million events, so a run takes a while. Run it without a block range and your numbers will differ, because the window moves with the chain.

## How it counts

- A transaction counts for a protocol when it emitted at least one event from that protocol's core contracts. A transaction that touches two contracts of the same protocol counts once.
- Wallets sending are the distinct addresses that sent those transactions. Some protocols are driven by operators, relayers or bots, so this is not a count of end users. Gnosis Pay card payments, for example, are all sent by Gnosis Pay.
- Card accounts are the distinct Safe accounts in Gnosis Pay's `Spend` events.
- The list covers protocols we could label from their own docs or repos. Tokens, bridges, account abstraction infrastructure and contracts without a public owner are left out, even when they are busy.

| Protocol | Contracts | Source |
| --- | --- | --- |
| Lido Data Bus | `0x37De961D6bb5865867aDd416be07189D2Dd960e6` | [Lido deployed contracts](https://docs.lido.fi/deployed-contracts/#data-bus) |
| HOPR | channels `0x75Ce5933...f8E6`, `0x860f50B2...2Aa4` | [hoprnet/contracts](https://github.com/hoprnet/contracts/blob/main/ethereum/bindings/contracts-addresses.json), the two production networks |
| Balancer | Vault V2 `0xBA122222...F2C8`, Vault V3 `0xbA133333...9bA9` | [Balancer frontend config](https://github.com/balancer/frontend-monorepo/blob/main/packages/lib/config/networks/gnosis.ts) |
| Spark | Pool `0x2Dae5307...07e0` | [spark-address-registry](https://github.com/sparkdotfi/spark-address-registry/blob/master/src/Gnosis.sol) |
| Aave | V3 Pool `0xb5020155...26D8` | [aave-address-book](https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Gnosis.sol) |
| Circles | v2 Hub `0xc12C1E50...13e8` | [circles-sdk](https://github.com/aboutcircles/circles-sdk/blob/dev/packages/sdk/src/config.ts) |
| Gnosis Pay | spend modules `0x5f07734E...3F8a`, `0xcFF260bf...549b` | [DefiLlama](https://github.com/DefiLlama/dimension-adapters/blob/master/dexs/gnosispay.ts) and [rotki](https://github.com/rotki/rotki/blob/develop/rotkehlchen/chain/gnosis/modules/gnosis_pay/constants.py) |
| Olas | Mech Marketplace `0x735FAAb1...70bB` | [olas-operate-app](https://github.com/valory-xyz/olas-operate-app/blob/main/frontend/config/mechs.ts) |
| CoW Protocol | GPv2Settlement `0x9008D19f...ab41` | [CoW Protocol docs](https://docs.cow.fi/cow-protocol/reference/contracts/core) |

Every transaction count was checked against `eth_getLogs` on the public Gnosis RPC (`rpc.gnosischain.com`) for the same blocks, and they match exactly.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on https://gnosis.hypersync.xyz
to read every event from the core contracts of Lido Data Bus, HOPR, Balancer, Spark, Aave, Circles,
Gnosis Pay, Olas and CoW Protocol on Gnosis Chain over the last 30 days. My API token is in the
ENVIO_API_TOKEN environment variable. Chart transactions per protocol per day.
```
