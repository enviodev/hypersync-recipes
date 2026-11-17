# USDC on Arc, every mint and burn

In the 30 days to 3 Nov 2026, **USDC supply on Arc grew from $513M to $1.11B**. $4.40B was minted and $3.80B burned, and $1.78B of the burning went through Circle Gateway and CCTP on its way to other chains.

| | 4 Oct to 3 Nov 2026 |
| --- | --- |
| Supply at the start | $513M |
| Minted | $4.40B |
| Burned | $3.80B |
| Supply at the end | $1.11B |
| Burned through Circle Gateway | $1.28B |
| Burned through CCTP | $501M |
| Burned through other addresses | $2.02B |

## Why it's interesting

Arc is Circle's own chain, and USDC is its native asset. Every dollar that arrives is a mint and every dollar that leaves is a burn, so mints and burns tell you how much USDC is moving through the chain, not only how much sits there. Labelling each burn by the address that sent it shows how much of that traffic is Circle's own crosschain plumbing.

## What it pulls

- Every `Transfer` log on USDC [`0x3600000000000000000000000000000000000000`](https://docs.arc.io/arc/references/contract-addresses) to or from the zero address. USDC has 6 decimals through its ERC-20 interface.
- Burns are labelled by the address that sent the USDC to the zero address. The Circle Gateway (`0x77777777dcc4d5a8b6e418fd04d8997ef11000ee`) and CCTP (`0xfd78ee919681417d192449715b2594ab58f5d002`) addresses come from Circle's [Gateway](https://developers.circle.com/gateway/references/contract-addresses) and [CCTP](https://developers.circle.com/cctp/references/contract-addresses) contract pages.

Supply is mints minus burns since the first block, plus the 10,000 USDC genesis balance that never had a `Transfer` log. Every number here comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 30                          # the last 30 days
python3 script.py 30 2026-11-03T09:00:25      # the window above
```

Sample output from the window above.

```
USDC on Arc, 30 days from 04 Oct 09:00 UTC to 03 Nov 09:00 UTC
Supply then  $513M
Minted       $4.40B
Burned       $3.80B
Supply now   $1.11B  (net $599M added)
  burned via Circle Gateway $1.28B
  burned via CCTP           $501M
  burned via other          $2.02B
```

Without an end time the window ends at the latest block, so your numbers will differ.

## Change the window or chain

- **Window.** The first argument is the number of days. The second is an end time in UTC, so you can rerun any past window exactly.
- **Labels.** Add any address to `CIRCLE` to split out burns from another contract.
- **Chain.** USDC works the same way on every chain Circle issues it on. Change `URL` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `USDC` to Circle's address there, and drop `GENESIS`, which only applies to Arc.

## Check the numbers

The sister example [arc-stablecoins-30d](../arc-stablecoins-30d) checks the same supply rebuild against USDC's `totalSupply()` over RPC, and it matches to the last unit at every block it tried.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every USDC mint and burn
on Arc and label each burn by the address that sent it. My HyperSync token is in
the ENVIO_API_TOKEN environment variable.

Add the same split for mints, by the address that received the new USDC, and
print minted and burned per UTC day for the last 30 days with Gateway and CCTP
as separate columns. Keep the standard library only. Then check the supply at
the end of the last day against USDC totalSupply() on https://rpc.mainnet.arc.io
at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Arc contract addresses](https://docs.arc.io/arc/references/contract-addresses)
- [Circle Gateway contract addresses](https://developers.circle.com/gateway/references/contract-addresses)
- [CCTP contract addresses](https://developers.circle.com/cctp/references/contract-addresses)
- [Envio Discord](https://discord.gg/envio)
