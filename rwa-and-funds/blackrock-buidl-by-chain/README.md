# Where BlackRock's BUIDL sits, chain by chain

In a run on 9 Nov 2026, **BlackRock's BUIDL fund had $1.08B on the seven EVM chains BlackRock lists, and Avalanche held the most at $416.8M (38.7%)**. That's more than Ethereum, OP Mainnet, Arbitrum and Polygon combined. $2.04B of BUIDL has been minted on Avalanche since launch.

| Chain | Supply | Share |
| --- | --- | --- |
| Avalanche | $416.8M | 38.7% |
| Ethereum | $316.8M | 29.4% |
| BNB Chain | $277.5M | 25.7% |
| OP Mainnet | $26.6M | 2.5% |
| Tempo | $17.2M | 1.6% |
| Arbitrum | $12.6M | 1.2% |
| Polygon | $10.5M | 1.0% |

## Why it's interesting

BUIDL is one of the biggest tokenized funds, and it's spread across a lot of chains. Rebuilding supply from mints and burns gives you the per-chain picture from the chains themselves, and the full history means you can chart it day by day too. The same script works for any multichain token where you want supply per chain.

## What it pulls

- Every ERC-20 `Transfer` from or to the zero address (mints and burns) of BUIDL on each chain, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Every supply figure comes from HyperSync.
- One `totalSupply()` call per chain on a public RPC, as a check.

Token addresses are the official ones on BlackRock's [token addresses page](https://www.blackrock.com/corporate/compliance/scams-and-fraud/blackrock-token-addresses).

| Chain | Address |
| --- | --- |
| Avalanche | `0x53FC82f14F009009b440a706e31c9021E1196A2F` |
| Ethereum (BUIDL) | [`0x7712c34205737192402172409a8F7ccef8aA2AEc`](https://etherscan.io/token/0x7712c34205737192402172409a8F7ccef8aA2AEc) |
| Ethereum (BUIDL-I) | [`0x6a9DA2D710BB9B700acde7Cb81F10F1fF8C89041`](https://etherscan.io/token/0x6a9DA2D710BB9B700acde7Cb81F10F1fF8C89041) |
| BNB Chain | `0x2D5BdC96D9C8AabBDB38c9A27398513e7E5ef84F` |
| OP Mainnet | `0xa1CDAb15bBA75a80dF4089CaFbA013e376957cF5` |
| Tempo | `0xb5FF12Bd8010BaEf823D1BfA2Ce6bdc0109CBb24` |
| Arbitrum | [`0xA6525Ae43eDCd03dC08E775774dCAbd3bb925872`](https://arbiscan.io/token/0xA6525Ae43eDCd03dC08E775774dCAbd3bb925872) |
| Polygon | `0x2893Ef551B6dD69F661Ac00F11D93E5Dc5Dc0e99` |

Both Ethereum share classes count towards Ethereum. BUIDL has 6 decimals on every chain and a stable $1 value, so supply is shown in dollars. BUIDL is also on Solana and Aptos, which this script doesn't read.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Sample output from the 9 Nov 2026 run.

```
BlackRock BUIDL on EVM chains: $1,077,950,497
  Avalanche  $   416,822,490   38.7%
  Ethereum   $   316,772,397   29.4%
  BNB Chain  $   277,503,739   25.7%
  OP Mainnet $    26,572,637    2.5%
  Tempo      $    17,172,594    1.6%
  Arbitrum   $    12,629,108    1.2%
  Polygon    $    10,477,531    1.0%
Avalanche vs Ethereum, OP Mainnet, Arbitrum and Polygon combined: $416,822,490 vs $366,451,674
BUIDL minted on Avalanche since launch: $2,043,131,789
Checks
  Avalanche: replayed supply matches totalSupply() at block 99,867,223
  Ethereum: replayed supply matches totalSupply() at block 26,378,668
  BNB Chain: replayed supply matches totalSupply() at block 132,620,165
  OP Mainnet: replayed supply matches totalSupply() at block 159,322,313
  Tempo: replayed supply matches totalSupply() at block 48,215,732
  Arbitrum: replayed supply matches totalSupply() at block 522,735,768
  Polygon: replayed supply matches totalSupply() at block 97,025,310
```

BUIDL is minted and redeemed all the time, so your numbers will differ.

## Change the window or chain

- **Another fund.** `CHAINS` maps each chain to its HyperSync subdomain, a public RPC and the token addresses. Swap in any multichain token, a stablecoin or another fund, to get its supply per chain.
- **Add a chain.** Add a row with the chain's subdomain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), a public RPC and the token address.
- **Over time.** The script already reads every mint and burn with its block. Group them by day to chart supply on each chain over time.

## Check the numbers

The script checks itself. For each chain it compares the supply rebuilt from HyperSync mints and burns with `totalSupply()` read over a public RPC at the last block HyperSync returned, and the run above matched on all seven chains. You can repeat any one on the chain's explorer with the addresses above.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to replay every mint and burn of
BlackRock's BUIDL on seven EVM chains and rebuild supply per chain.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a daily supply series for each chain since BUIDL launched there and write it to
supply_daily.csv, one column per chain. Keep the standard library only. Then check that
the last row of each column matches the per-chain supply the script prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Avalanche on Envio](https://envio.dev/chains/avalanche)
- [BlackRock token addresses](https://www.blackrock.com/corporate/compliance/scams-and-fraud/blackrock-token-addresses)
- [Envio Discord](https://discord.gg/envio)
