# Robinhood Earn USDG vault depositors

Reads every deposit and withdrawal on the USDG vault behind Robinhood Earn with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It counts the wallets that have deposited, shows how much a typical wallet puts in, adds up what has been supplied, and checks the result against the vault's own `totalAssets()` read over RPC.

These are the numbers behind Envio's post on Robinhood Earn depositors.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

The first run reads every event since the vault opened (about six minutes) and saves them to `rows.json`. Run `python script.py --cached` to reuse that file. It also writes one row per day to `daily.json`: deposits, active wallets, new wallets, the running wallet count and net USDG supplied.

## What it prints

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
Top 10 wallets put in $1,096,913,242 (38% of all deposits)
Wash check: 9 wallets with 20+ deposits and 20+ withdrawals in one day
```

That run was on 10th Nov 2026. Half of the 86,752 wallets have put in $150 or less in total. The net flow ($528.5M) sits about $5M below `totalAssets()` ($533.5M), and that gap is the interest the vault has earned and not yet paid out. "Supplied in total" counts every deposit, so money that went in, came out and went back in counts each time.

## How it counts

- USDG on Robinhood is `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, from Robinhood's [contracts page](https://docs.robinhood.com/chain/contracts/).
- Robinhood's [Earn support page](https://robinhood.com/us/en/support/articles/crypto-earn/) says Earn lends USDG through a Morpho vault curated by Steakhouse Financial. Steakhouse links the vault, Steakhouse USDG at `0xBeEff033F34C046626B8D0A041844C5d1A5409dd`, in its [1st Sep markets update](https://kitchen.steakhouse.financial/p/defi-markets-update-2026-09-01), and calls it "the USDG vault behind Robinhood Earn" in its [stock token collateral post](https://kitchen.steakhouse.financial/p/steakhouse-onboards-robinhood-stock). Morpho's API lists it as by far the largest USDG vault on Robinhood. Other apps can deposit into the same vault too, so the wallet count is everyone who has deposited, mostly through Earn.
- HyperSync reads the vault's ERC-4626 `Deposit` and `Withdraw` events in one query, using the default join so each log comes with its block timestamp and transaction. Only logs whose address and topic0 match the vault and the two events are kept.
- A wallet is the `owner` in a `Deposit` event, the account that receives the vault shares. Almost every deposit is sent by a relayer on the wallet's behalf, so the transaction sender is not used to count wallets.
- Amounts are in USDG (6 decimals), counted at $1.
- Wash check: a wallet with 20 or more deposits and 20 or more withdrawals on the same UTC day is flagged as cycling. Nine wallets were flagged, about 2% of all deposited dollars, and they change none of the headline numbers.
- `totalAssets()` (selector `0x01e1d114`) is read from Robinhood's public RPC as a second check.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Robinhood (chain 4663,
endpoint https://robinhood.hypersync.xyz) to read every ERC-4626 Deposit and Withdraw event on the
Steakhouse USDG Morpho vault 0xBeEff033F34C046626B8D0A041844C5d1A5409dd. My API token is in the
ENVIO_API_TOKEN environment variable. Count unique depositing wallets (the Deposit owner), the median
total deposited per wallet, and new wallets per day, then compare net deposits with totalAssets().
```

## Learn more

- [Robinhood on Envio](https://envio.dev/chains/robinhood): HyperSync and HyperIndex support for Robinhood
- [USDG on Morpho](https://github.com/enviodev/hypersync-recipes/tree/main/usdg-on-morpho): every Morpho market lending USDG, by chain
- [Uniswap v4 hooks on Robinhood](https://github.com/enviodev/hypersync-recipes/tree/main/uniswap-v4-hooks-robinhood): every v4 pool and hook on Robinhood
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
