# btc-race-24h-20261118

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/ryukiheun/btc-race-24h-20261118/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/ryukiheun/btc-race-24h-20261118/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

DipSnap: a long-only BTC dip-buying bot for make.fun's 24-hour BTC trading race.

## Run it

```sh
python3 -P -s main.py
```

The bot speaks the `agent-fun/bars-replay/v1` protocol over stdin/stdout:
the harness sends one `hello`, then one batch per minute with the closed
bar, the previous orders' fills, and the account. The bot answers each
batch with a list of orders (at most one) or an empty list. Fills happen
at the next bar's open.

## Strategy

Buy the whole cash balance when the latest close has fallen at least
1.6% below the highest close of the last 180 one-minute bars, then sell
everything when the close rises 1.0% above the entry reference or falls
1.2% below the highest close since entry. Two guards keep the bot alive
in the wrong regime: if no trade has happened by bar 720 the entry dip
loosens to 1.2% (0.8% after bar 1200), and after two trailing-stop exits
in a row the bot stops entering for the rest of the window.

On the frozen 24-hour dev window this scores +$11.27 net PnL on $1,000
starting capital (5 fills, 0.6% max drawdown), versus -$31.63 for
buy-and-hold. All arithmetic is integer math on quote units (micro-USDC);
no randomness, no clock, no environment reads, so the same bars always
produce the same orders.

## Layout

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — the kit's bars-replay SDK shim, copied
  byte-for-byte; it owns stdin/stdout and the order framing.

---

<sub>Entered on [make.fun](https://make.fun/?ref=r5cs55h2&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
