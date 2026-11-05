# Tokenized Circle stock onchain

Finds every issuer's tokenized Circle (CRCL) stock and reads every transfer of it on the EVM chains [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview) covers. It prints how much Circle stock each issuer has onchain and on which chain, and how much of it sits in DEX pools and lending markets.

These are the numbers behind Envio's post on where tokenized Circle stock lives.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

The Robinhood token alone has more than a million transfers, so a run takes about 20 minutes.

## What it prints

```
Tokenized Circle (CRCL) stock onchain: 5,141,770 shares, $380.4M at $73.99 (Coinbase CRCLc NAV)
  Binance bStocks $  158.6M  41.7%
      BNB Chain $  158.6M
  xStocks         $  124.0M  32.6%
      X Layer   $   64.5M
      Solana    $   56.9M
      Ethereum  $    1.6M
      Ink       $    0.5M
      Mantle    $    0.5M
  Ondo            $   87.1M  22.9%
      BNB Chain $   72.3M
      Ethereum  $   12.2M
      Solana    $    2.5M
  Robinhood       $   10.6M   2.8%
      Robinhood $   10.6M
  Coinbase        $    0.1M   0.0%
      Base      $    0.1M
By chain: BNB Chain 60.7%, X Layer 17.0%, Solana 15.6%, Ethereum 3.6%, Robinhood 2.8%, Ink 0.1%, Mantle 0.1%, Base 0.0%
On the EVM chains ($256.5M), by holder type
  wallet         $  191.7M  74.7%
  other contract $   58.5M  22.8%
  dex            $    4.5M   1.8%
  lending        $    1.7M   0.7%
Binance Hot Wallet 20 holds 82.1% of Binance's CRCLB
Checks
  Ondo on Ethereum: replayed supply matches totalSupply() at block 26,348,909
  ...
  Binance bStocks on BNB Chain: replayed supply matches totalSupply() at block 131,827,309
```

The numbers move as tokens are minted, redeemed and traded, so yours will differ.

## How it counts

- Token addresses come from each issuer's own list: Ondo's token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses), the [xStocks product list](https://xstocks.fi/us/products), Robinhood's [stock token API](https://docs.robinhood.com/chain/stock-tokens), Coinbase's [tokenized stocks API](https://docs.base.org/sdks/tokenized-stocks), and Binance's CRCLB entry in Trust Wallet's token registry, which links to [bstocks.finance](https://www.bstocks.finance/).
- Supply on each EVM chain is every mint minus every burn, checked against `totalSupply()`.
- xStocks mints every EVM token to one wallet (`0x5f7a4c11...a2ad`) and sends it out from there, so that wallet's balance is left out as not yet issued. On Solana the xStocks minter's balance is left out the same way. X Layer and Solana are not covered by HyperSync, so their supply is read from public RPCs.
- xStocks' TON and Tron tokens are left out, since we could not tell issued and unissued balances apart there.
- Every token is valued at one CRCL price, Coinbase's published NAV for CRCLc. None of the tokens use a share multiplier other than 1.
- Holder types cover the EVM chains HyperSync reads. Holders with at least 0.01% of a token are checked onchain: DEX pools answer `factory()` and `token0()` or are a known pool manager or vault (Uniswap v4, PancakeSwap Infinity), lending markets are Aave style tokens or a known lending singleton (Morpho, Lista DAO Moolah), and wallets have no code or an EIP-7702 delegation. Smaller holders count as wallets.
- Binance Hot Wallet 20 (`0xf977814e...1acec`) is labelled on BscScan.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of the
tokenized Circle (CRCL) stock tokens from Binance bStocks (BNB Chain 0x80f3d493ebce97e343c53d29a137942416b4ffc0),
Ondo (addresses in the sheet at https://docs.ondo.finance/addresses) and xStocks (https://xstocks.fi/us/products).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart how much of each token sits in DEX pools, lending markets and wallets, day by day.
```
