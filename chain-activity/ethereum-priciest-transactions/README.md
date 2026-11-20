# How to find the most expensive transactions on Ethereum by gas fee

Over 24 hours (Ethereum blocks 26,448,650 to 26,455,833, 1,847,307 transactions), **the priciest transaction paid 0.4822 ETH in fees for a swap that used only 153,147 gas**. The sender paid 3,148 gwei for it, which is 14,648 times the base fee of its block. The runner-up paid 0.4720 ETH the opposite way, 4.2M gas at 112 gwei.

| # | Fee | Gas used | Gas price | Times the base fee |
| --- | --- | --- | --- | --- |
| 1 | 0.4822 ETH | 153,147 | 3,148 gwei | 14,648x |
| 2 | 0.4720 ETH | 4,225,995 | 112 gwei | 1,063x |
| 3 | 0.2994 ETH | 1,550,687 | 193 gwei | 189x |
| 4 | 0.2673 ETH | 1,501,056 | 178 gwei | 225x |
| 5 | 0.2583 ETH | 131,411 | 1,966 gwei | 4,222x |
| 6 | 0.2092 ETH | 260,694 | 803 gwei | 2,944x |
| 7 | 0.1652 ETH | 489,860 | 337 gwei | 918x |
| 8 | 0.1579 ETH | 199,349 | 792 gwei | 2,729x |
| 9 | 0.1565 ETH | 199,431 | 785 gwei | 954x |
| 10 | 0.1425 ETH | 128,161 | 1,112 gwei | 1,107x |

## Why it's interesting

A fee is gas used times the price paid per gas, so an expensive transaction can come from either side. The runner-up burned a lot of gas at a normal price. The winner used an ordinary amount of gas and bid a price thousands of times the base fee to get in. If you build anything that sends transactions, these are the outliers your gas estimates have to survive.

## What it pulls

- Every transaction in the window from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview), with the gas it used and the effective gas price it paid. The fee is the two multiplied together, in integer maths.
- The base fee of each top transaction's block, also from HyperSync, to show how far above it the price sat.
- A heap keeps only the 10 largest fees, so memory stays small.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                       # the last 7,200 blocks, about 24 hours
python3 script.py 26448650 26455833     # the window above
```

It scans about 1.8M transactions, so give it a few minutes. Sample output for the window above:

```
Ethereum transactions, blocks 26,448,650 to 26,455,833: 1,847,307 scanned

 1  0.4822 ETH    153,147 gas    3,148 gwei     14,648x the base fee  0x4575b6739b2f537d3b76dc4663859ef10601c61df956a0ca
 2  0.4720 ETH  4,225,995 gas      112 gwei      1,063x the base fee  0x3fc5282cf803a1460e5e38383f91fa3cc964b6068e2a17d0
 3  0.2994 ETH  1,550,687 gas      193 gwei        189x the base fee  0xed3bd842e44a076175253eeb5a69844a3fba3dd923ac806e
 4  0.2673 ETH  1,501,056 gas      178 gwei        225x the base fee  0x5175a12545041b2233ae314c7f376a549b49bbcf137fdae6
 5  0.2583 ETH    131,411 gas    1,966 gwei      4,222x the base fee  0x4d3d49fe3b2649a9284a0defaad880a13ea3c92824a567f5
 6  0.2092 ETH    260,694 gas      803 gwei      2,944x the base fee  0xfce1d79c70e960adb4251c950268e722e1b616fcbc4bf1a2
 7  0.1652 ETH    489,860 gas      337 gwei        918x the base fee  0x0e9ffa6599d834f75fff8a4fb21c75d92a42d4fdc36880a8
 8  0.1579 ETH    199,349 gas      792 gwei      2,729x the base fee  0x1775c68b10e24beb4849650968ab06cf3af8f108043df0e1
 9  0.1565 ETH    199,431 gas      785 gwei        954x the base fee  0xe3b6af1c7ab43b83e3de15edad9a256f72077816abc8e58c
10  0.1425 ETH    128,161 gas    1,112 gwei      1,107x the base fee  0xcab0a8b7c5e0db342e4dc165a59e4476d49d1d76e9f53cf4
```
