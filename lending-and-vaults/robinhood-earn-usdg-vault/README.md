# Robinhood Earn USDG vault depositors

Up to 10 Nov 2026, **86.8K wallets had made 431K deposits into the USDG vault behind Robinhood Earn**, and half of them have put in $150 or less in total. Net of withdrawals, $528.5M of USDG has gone in since the vault opened on 3 Jun 2026.

| Wallets that deposited in total | Wallets | Share |
| --- | --- | --- |
| Under $100 | 34,486 | 40% |
| Under $1,000 | 57,786 | 67% |
| Under $10,000 | 75,447 | 87% |
| Under $1,000,000 | 86,528 | 100% |

## Why it's interesting

Robinhood Earn puts a familiar savings product on top of an onchain vault, so you can see who's using it straight from the vault's events. A median wallet total of $150 shows a lot of it is everyday savings money. It's also a clean ERC-4626 example, and the same two events work for any vault.

## What it pulls

- Every ERC-4626 `Deposit` and `Withdraw` log on the Steakhouse USDG vault on Robinhood Chain, `0xBeEff033F34C046626B8D0A041844C5d1A5409dd`. Amounts are USDG (`0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, 6 decimals, from Robinhood's [contracts page](https://docs.robinhood.com/chain/contracts/)), counted at $1.
- A wallet is the `owner` in a `Deposit` event, the account that receives the vault shares. Almost every deposit is sent by a relayer on the wallet's behalf, so the transaction sender isn't used.

Robinhood's [Earn support page](https://robinhood.com/us/en/support/articles/crypto-earn/) says Earn lends USDG through a Morpho vault curated by Steakhouse Financial, and Steakhouse names this vault as the one behind Robinhood Earn in its [stock token collateral post](https://kitchen.steakhouse.financial/p/steakhouse-onboards-robinhood-stock). Other apps can deposit into the same vault, so the wallet count is everyone who has deposited, mostly through Earn.

As a sanity check, the script flags wallets with 20 or more deposits and 20 or more withdrawals on the same UTC day. Nine wallets were flagged, about 2% of deposited dollars, and they change none of the headline numbers. Every number in the finding comes from HyperSync. Only the `totalAssets()` check is read over RPC.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py             # read every event and save them to rows.json
python3 script.py --cached    # reuse rows.json
```

The first run reads every event since the vault opened, which takes about six minutes. It also writes one row per day to `daily.json` with deposits, active wallets, new wallets, the running wallet count and net USDG supplied. Sample output from a run on 10 Nov 2026.

```
Steakhouse USDG vault 0xbeeff033f34c046626b8d0a041844c5d1a5409dd on Robinhood, blocks up to 111,196,066
First deposit 2026-06-03, last 2026-11-10
Deposits 431,287 from 86,752 wallets. Withdrawals 185,830
Supplied in total $2,883,054,386, withdrawn $2,354,543,752, net $528,510,634
Vault totalAssets() now $533,502,192 (net flow plus interest earned)
Median deposit $85.08, mean $6,685
Median total deposited per wallet $150.00
  wallets that deposited under $      100:  34,486 (40%)
  wallets that deposited under $    1,000:  57,786 (67%)
  wallets that deposited under $   10,000:  75,447 (87%)
  wallets that deposited under $1,000,000:  86,528 (100%)
...
```

"Supplied in total" counts every deposit, so money that went in, came out and went back in counts each time. Your numbers will be higher, as new deposits come in.

## Change the window or chain

- **Window.** The query starts at `from_block` 0. Raise it to look at a recent stretch, or use `daily.json` to slice by date.
- **Vault.** Swap `VAULT` for any ERC-4626 vault and `USDG` for its asset. The event signatures are standard, so nothing else changes.
- **Chain.** Change `URL` to another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `RPC` to a public RPC there.

## Check the numbers

As the comparison, the script reads the vault's own `totalAssets()` over Robinhood Chain's public RPC. Net flow from events ($528.5M) sits about $5M below `totalAssets()` ($533.5M), and that gap is interest the vault has earned.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every ERC-4626 Deposit
and Withdraw on the Steakhouse USDG vault on Robinhood Chain and count depositing
wallets. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a monthly cohort table, grouping wallets by the month of their first deposit
and showing how many still hold shares at the end of each later month. Keep the
standard library only and use --cached while you iterate. Then check one wallet's
share balance against balanceOf on the vault over https://rpc.mainnet.chain.robinhood.com.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Robinhood Chain contracts](https://docs.robinhood.com/chain/contracts/)
- [Robinhood Earn](https://robinhood.com/us/en/support/articles/crypto-earn/)
- [Envio Discord](https://discord.gg/envio)
