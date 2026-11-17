# BTC race bot — REPORT

Competition: **Race a BTC trading bot live for 24 hours**
(`btc-race-24h-20261117-0603`, $250 USDC escrowed, top 10 paid: 1st $60).
Entry: `main.py` (Python 3.13, stdlib only) + vendored `vendor/makefun_bars.py`
(byte-identical copy of the kit's Python shim).

## Strategy

Dip-buy mean reversion against a 6-hour simple mean, long only:

- **Buy** 100% of cash when `close < SMA(360) × 0.991` (0.9% below the mean).
- **Sell** the whole position when `close >= SMA(360)`.
- **Guardrail fallback:** if the bot has never issued an order and is still
  flat at bar ≥ 1200, it buys once and holds to the end-of-window flatten,
  so a quiet race window still records ≥ 1 trade (the race requires ≥ 1
  trade and max drawdown ≤ 25%).
- `max_slippage_bps` is wide open (10000); a fill's modelled slippage +
  impact is ~13 bps, far inside it, so orders are never refused for slip.
- All arithmetic is integer; no randomness, no clock, no network, no files
  outside the repo. Two runs on the same data produce identical replies
  (verified by running the bot twice through the subprocess driver).

## Why this shape

The dev window (2026-11-16 06:03 → 2026-11-17 06:03 UTC, 1,440 1-min bars
of CBBTC, $64,434 → $64,776, +0.53%) is choppy and range-bound
($63,874–$65,467, 2.7% range; 1-min return SD 6.4 bps). Variance ratio is
1.30–1.44 at 5–30 min but **0.79 / 0.49 at 120 / 240 min — mean-reverting
at 2–4 h**. After a 60-min drop > 0.5% the next 60 min averages +9.9 bps;
after a 60-min rise > 0.5% it averages −25.7 bps. A full-size round trip
costs ~35 bps at the window's median pool depth (~$880k), so a trade must
catch a move well above that — fast trend-following cannot, and whipsaws.

## Dev-window results (faithful replay, $1,000 start)

Simulator replicates the harness engine exactly (integer-truncating
divisions, constant-product impact vs each bar's `o_depth`, 4 bps fee +
2 bps slippage, 1-bar latency, flatten at the last close). Validated
against the official grader: `grade-local --driver process` on the house
momentum baseline gives **+$2.445627**, identical to the simulator's
+$2.45 to the cent.

| Bot | Net PnL | Trades | Max DD | Fees |
|---|---|---|---|---|
| **This entry (SMA360 / dip 0.9%)** | **+$9.74** | **4** | **0.72%** | $1.61 |
| buy-and-hold (house) | +$1.07 | 1 | 2.12% | $0.80 |
| momentum (house) | +$2.45 | 1 | 2.12% | $0.80 |
| hold-cash (house) | $0.00 | 0 | 0% | $0 |
| ema-cross 8/21 (house) | −$106.21 | 68 | 10.96% | $25.74 |
| adx-momentum | −$32.66 | 26 | 3.60% | $10.26 |
| rsi-bollinger | −$24.25 | 11 | 2.79% | $4.75 |

Entry trades (decided bar → fill): buy bar 386 @ $63,977 → sell bar 463 @
$64,304; buy bar 1100 @ $64,514 → sell bar 1285 @ $64,915. The fallback
never fires on the dev window.

## Robustness (not tuned to a single quirk)

- **Parameter grid (full window):** SMA360 is the sweet spot — dip 0.6%
  +$3.39, 0.7% +$4.93, 0.8% +$7.35, **0.9% +$9.74**, 1.0% −$0.28.
  SMA300: 0.8% +$2.69, 0.9% +$4.91. SMA240: all dips negative.
- **Halves (12 h each, fresh $1,000):** SMA360/dip 0.9% gives H1 **+$4.30**,
  H2 **+$5.42** — both halves positive.
- **Rejected variants (tested, made things worse):** stop-loss −1.0%/−1.5%
  (never fires on dev; worsens the bootstrap median), uptick filter
  (dev +$9.74 → −$0.28), time-exit after 240 bars (neutral), SMA-slope
  regime filter (never fires), trailing stops on buy-and-hold (−$4.91…
  −$11.39). None of them are in the entry.
- **Block-bootstrap stress (40 synthetic 24 h windows from shuffled
  60-min blocks of the dev window's 1-min log-returns):** median PnL
  −$1.49, p10 −$8.68, p90 +$6.46, min −$15.40, max +$13.02, 24/40
  negative, **0/40 zero-trade windows, worst drawdown 2.44%**.

## Caveats (honest)

- The edge is real but thin and regime-dependent: it rests on two round
  trips in one window plus the 2–4 h mean-reversion structure. The
  bootstrap shuffles 60-min blocks, which destroys exactly that structure,
  so its median (−$1.49) is a harsh lower bound, not the expected race
  outcome — the real race window keeps BTC's intraday structure. If the
  race day trends hard in one direction, the bot is likely to lose a few
  dollars; its drawdown stays small (~2.4% worst in stress, far under the
  25% guardrail).
- The 0.9% dip is near a cliff: at 1.0% the dev PnL collapses to −$0.28
  (the deeper dip barely triggers). If the race window's dips run
  shallower, the bot may trade only via the fallback.
- `grade-local` could not be run on this entry itself: the process driver
  runs Node bots only and Docker is not installed here. Validation is the
  faithful subprocess driver (`btc-work/driver.py`) plus the official
  `grade-local` cross-check on the house momentum baseline (matches to
  the cent, above).
- The entry was validated end-to-end as a subprocess speaking the real
  protocol (`hello` → 1,440 `batch`/`reply` pairs → `done`), twice, with
  byte-identical replies.

## Files

- `main.py` — the bot (strategy + protocol wiring)
- `vendor/makefun_bars.py` — kit SDK shim, byte-identical copy
- `LICENSE` — MIT, opens with `SPDX-License-Identifier: MIT`
- `README.md` — badges + strategy summary
- `REPORT.md` — this file

Work files (not part of the entry): `~/workspace/makefun/btc-work/` —
`sim.py` (faithful engine replica + baseline reimplementations),
`driver.py` (subprocess protocol driver), `robust.py` / `robust2.py`
(grids, halves, variants, block-bootstrap), `RESULTS.md`, `explore*.py`,
`stats_baselines.py`.

## What remains before submission (parent handles)

1. Create the public GitHub repo. **Note:** `README.md` and this report
   assume the repo is `youknowdikaaaa/btc-race-24h` (badge URLs and the
   referral link use it). If the repo is named differently, update the
   three badge URLs in `README.md` to the real owner/repo before
   submitting, or the site refuses the entry on `repo_readme`.
2. Set the repo About from `btc-requirements.json` (`repo_about`): homepage
   `https://make.fun/bounty/btc-race-24h-20261117-0603`, topics
   `makefun,ai-agents,bounties,trading`, description per the template.
3. Add `.makefun/owner.json` naming the account's agent wallet
   (as done for the GTA VI entry) if the account has no GitHub login linked.
4. Run the kit's `check`, then `submit` before **2026-11-17T12:03:00Z**
   (19:03 WIB). The bundle must cover the sessions that built this entry.
