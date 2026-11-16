# ether.fi card payments on Optimism

Reads every `Spend` event from ether.fi Cash on Optimism with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). ether.fi Cash settles each card payment onchain, so one `Spend` event is one payment, with the cardholder's safe, the card issuer and the USD amount. The script prints card payments, cardholders and USD spent for a window, the typical payment per cardholder, how many cardholders paid on every day, and a day-by-day table.

These are the numbers behind Envio's post on the typical ether.fi cardholder paying $13.45 a swipe.

## The finding

From 9 to 15 Nov 2026 (UTC), on OP Mainnet:

- 36K cardholders made 457K card payments worth $33.5M.
- The typical cardholder's payment was $13.45. That's the median, across cardholders, of each cardholder's own median payment, so a few very busy accounts can't move it.
- More than 5K cardholders paid with the card on every day of the week.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py                          # the last 7 full UTC days
python script.py 2026-11-09 2026-11-15    # a fixed window, both dates included
```

A week is about 460K events and takes a few minutes.

## What it prints

```
ether.fi Cash on Optimism, 09 Nov to 15 Nov 2026 UTC (7 days)
Spend events by issuer: {'Rain': 443720, 'PIX': 3879, 'Reap': 13565, 'CardOrder': 917}
Spend events by mode:   {'Debit': 438250, 'Credit': 23831}

Card payments 457,285  USD $33,481,254  cardholders 36,072
Median payment $9.92  under $100 90.3%
Typical payment per cardholder (median of each cardholder's own median) $13.45
Cardholders whose typical payment is under $20: 63.3%
Cardholders who paid on all 7 days: 5,547

day         payments  cardholders  usd
2026-11-09    64,048       18,447  $   4,834,198
2026-11-10    61,701       18,653  $   5,742,068
2026-11-11    62,917       18,668  $   4,806,000
2026-11-12    70,053       18,745  $   5,344,265
2026-11-13    65,462       18,849  $   4,537,266
2026-11-14    71,537       19,327  $   4,550,177
2026-11-15    61,567       17,764  $   3,667,280
```

## How it counts

- Contracts come from ether.fi's [deployed contracts](https://etherfi.gitbook.io/etherfi/contracts-and-integrations/deployed-contracts) page and the [cash-v3 repo](https://github.com/etherfi-protocol/cash-v3/tree/master/deployments/mainnet). The `CashModule` (`0x7Ca0b75E67E33c0014325B739A8d019C4FE445F0`) calls the `CashEventEmitter` (`0x380B2e96799405be6e3D965f4044099891881acB`) on every payment.
- The event is `Spend(address indexed safe, bytes32 indexed txId, BinSponsor indexed binSponsor, address[] tokens, uint256[] amounts, uint256[] amountInUsd, uint256 totalUsdAmt, Mode mode)` from [`CashEventEmitter.sol`](https://github.com/etherfi-protocol/cash-v3/blob/master/src/modules/cash/CashEventEmitter.sol). `totalUsdAmt` has 6 decimals.
- The query uses HyperSync's default join, and the script only keeps logs whose address and topic0 match. Each `txId` is counted once.
- Card payments are the `Reap` and `Rain` issuers from the `BinSponsor` enum in [`ICashModule.sol`](https://github.com/etherfi-protocol/cash-v3/blob/master/src/interfaces/ICashModule.sol). `PIX` (Brazil's Pix rail) and `CardOrder` are reported but left out of card payments.
- A cardholder is one ether.fi safe, the `safe` topic on the event.

## Check the numbers yourself

- Over RPC: `eth_getLogs` on `https://mainnet.optimism.io` for the emitter and the `Spend` topic over one hour (blocks 159,613,747 to 159,615,547) returned 3,885 events and $291,946.88, the same as HyperSync for that range.
- From transactions: in the 24 hours to 16 Nov 2026 13:40 UTC, HyperSync saw 62,904 calls to `spend()` on the `CashModule` and 62,909 `Spend` events.
- In September 2026 the emitter logged 1,586,993 `Spend` events from 48,709 safes. SpendNode's independent [September 2026 report](https://www.spendnode.io/crypto-cards/stats/september-2026/) gives about 1.59M events and 48,709 wallets for ether.fi that month.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Optimism (endpoint
https://optimism.hypersync.xyz) to read every Spend event from ether.fi's CashEventEmitter
0x380B2e96799405be6e3D965f4044099891881acB (topic0
0x244f4cc0665ad7ee4709aa59b30d3ea581cecde1b0430a3f23a5dc609d4890fc). My API token is in the
ENVIO_API_TOKEN environment variable. Use the default join and keep only logs whose address and
topic0 match. topic1 is the cardholder's safe, topic2 the payment id, topic3 the card issuer
(0 Reap, 1 Rain, 2 PIX, 3 CardOrder), and the 4th 32-byte word of data is the USD amount with 6
decimals. Show card payments per day, cardholders per day and each cardholder's typical payment.
```

To keep it live instead of re-running a script, ask the agent to turn it into a [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer on the same event and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

## Links

- Envio HyperSync docs: https://docs.envio.dev/docs/HyperSync/overview
- ether.fi Cash contracts: https://etherfi.gitbook.io/etherfi/contracts-and-integrations/deployed-contracts
- ether.fi cash-v3 source: https://github.com/etherfi-protocol/cash-v3
- OP Mainnet docs: https://docs.optimism.io
- Envio Discord: https://discord.gg/envio
