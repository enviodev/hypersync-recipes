# Circles trust links on Gnosis Chain

At the end of October 2026, **[Circles](https://aboutcircles.com) had 366K live trust links between 22.9K registered humans on Gnosis Chain, 2.01x the 182K a year earlier**. Humans grew from 9.8K to 22.9K over the same year.

| As of | Humans | Live trust links |
| --- | --- | --- |
| 2024-10-31 | 271 | 120 |
| 2025-04-30 | 1,901 | 9,041 |
| 2025-10-31 | 9,847 | 182,171 |
| 2026-04-30 | 15,657 | 226,657 |
| 2026-10-31 | 22,893 | 366,437 |

## Why it's interesting

Circles is a social money protocol. Each human mints their own currency, and trust between people is what lets those currencies flow. Trust is just a stream of `Trust` events with an expiry, so replaying them gives you the live social graph at any moment in its history. The same replay trick works for any onchain permission or allowlist that's set and revoked by events.

## What it pulls

All of it comes from HyperSync.

- Every `RegisterHuman` and `Trust` log from the Circles v2 Hub, `0xc12C1E50ABB450d6205Ea2C3Fa861b3B834d13e8`, from [The Circles Stack](https://docs.aboutcircles.com/circles-sdk/the-circles-protocol) docs.
- Every `BotCreated` log from Circles' invitations-at-scale contract, `0xd28b7c4f148b1f1e190840a1f7a796c5525d8902`.
- Block timestamps, to replay events up to each month end.

`Trust(truster, trustee, expiryTime)` is emitted when an avatar trusts another one, renews trust or removes it. Removing trust sets the expiry to the current time, so a link counts as live at a month end when its latest expiry is after that moment. A link is one direction, so two humans who trust each other make two links.

Only links where both sides are registered humans count. Links to or from groups and organisations are left out, as are links an avatar sets on itself. The 5,000 invitation bot accounts are registered as humans in the Hub so they can send invitations, and they're left out of both the human count and the links.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py             # up to the latest block
python3 script.py 49222000    # up to the block used above
```

It reads about 1.2M events in parallel block ranges and takes 5 to 10 minutes. Sample output with block 49222000, which reaches 11 Nov 2026.

```
Circles v2 on Gnosis Chain, blocks 36,400,000 to 49,222,000
5,000 invitation bot accounts left out

as of           humans    live trust links
2024-10-31         271                 120
2024-11-30         387                 255
2024-12-31         462                 549
2025-01-31         844               1,984
2025-02-28       1,144               4,176
2025-03-31       1,437               5,090
2025-04-30       1,901               9,041
2025-05-31       4,749              36,100
2025-06-30       7,235              75,252
2025-07-31       8,535              98,118
2025-08-31       9,065             120,173
2025-09-30       9,491             154,870
2025-10-31       9,847             182,171
2025-11-30      10,500             191,076
2025-12-31      10,877             199,686
2026-01-31      11,907             216,559
2026-02-28      13,037             222,803
2026-03-31      14,616             217,038
2026-04-30      15,657             226,657
2026-05-31      18,144             237,791
2026-06-30      20,391             292,232
2026-07-31      21,211             326,516
2026-08-31      21,917             345,026
2026-09-30      22,443             362,480
2026-10-31      22,893             366,437
2026-11-11      23,066             366,802

2026-10-31: 366,437 live trust links between 22,893 humans, 2.01x the 182,171 on 2025-10-31
```

The last row is the state at the last event before the end block. The summary line compares the last full month with the same month a year before.

## Change the window or chain

- **Window.** Pass an end block. The start is `START`, block 36,400,000, just before the Hub was deployed in October 2024.
- **Grouping.** `month_ends()` sets the snapshot points. Swap it for a weekly or daily series if you want finer steps.
- **Chain.** Circles v2 lives on Gnosis Chain. To replay another protocol's events the same way, swap `HYPERSYNC` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and the addresses and topics for that protocol's.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every RegisterHuman and
Trust event from the Circles v2 Hub on Gnosis Chain and replays them to count
live trust links between humans at each month end. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a count of mutual pairs, where both humans trust each other, at each month
end, and print it as a new column. Keep the standard library only. Run it with
end block 49222000 and check that the humans and live trust links columns are
unchanged.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Circles docs](https://docs.aboutcircles.com)
- [Envio Discord](https://discord.gg/envio)
