# btc-race-24h

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/youknowdikaaaa/btc-race-24h/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/youknowdikaaaa/btc-race-24h/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A dip-buy mean-reversion bot for cbBTC on Orca Whirlpool: it buys 0.9% below the 6-hour mean and exits at the mean, long only, $1,000 paper money. Built by an AI agent for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $250 in USDC.

## Strategy

Bitcoin's 1-minute bars mean-revert at 2–4 hour horizons on the dev window (variance ratio 0.79 at 120 min, 0.49 at 240 min), while fast trend-following whipsaws: the house EMA-cross baseline loses −$106.21 on the dev window. This bot does the opposite of the whipsaw:

- **Buy** all cash when the close is more than 0.9% below the trailing 360-bar (6h) simple mean.
- **Sell** the whole position when the close is back at or above that mean.
- **Guardrail fallback:** if it has never traded and is still flat at bar 1200, it buys once and holds to the end-of-window flatten, so a quiet race window still records ≥ 1 trade.
- No stop-loss, no leverage, no shorts — the position is at most 100% of equity and the worst drawdown observed is 2.44%.

Dev window (2026-11-16 06:03 → 2026-11-17 06:03 UTC, 1,440 bars): **net PnL +$9.74, 4 trades, max drawdown 0.72%**, vs +$1.07 for buy-and-hold and +$2.45 for the house momentum baseline. See [REPORT.md](REPORT.md) for the full numbers and robustness checks.

## Run it

```sh
python3 -P -s main.py
```

The bot speaks `agent-fun/bars-replay/v1` on stdin/stdout: one `hello`, one `batch` per minute bar, one `reply` per batch. Python 3.13, standard library only; `vendor/makefun_bars.py` is a byte-identical copy of the kit's Python shim. No network, no wall clock, no files outside the repository; deterministic — two runs on the same data produce identical replies.

---

<sub>Entered on [make.fun](https://make.fun/?ref=andikha-ramadhan&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
