"""BTC race bot: dip-buy mean reversion against a long SMA, long only.

Strategy (all integer arithmetic, deterministic, no clock/network/files):
  - Keep the last SMA_LEN one-minute closes of CBBTC.
  - FLAT and close < SMA * (1 - DIP): buy all cash.
  - LONG and close >= SMA: sell the whole position.
  - Guardrail fallback: if the bot has never traded and is still flat at
    bar >= FALLBACK_SEQ, buy once and hold to the end-of-window flatten,
    so a quiet race window still records >= 1 trade.
  - max_slippage_bps is wide open (10000): a fill's modelled slippage +
    impact is ~13 bps, far inside it, so orders are never refused for slip.

Why: the dev window is range-bound (variance ratio < 1 at 2-4h): after a
60-min drop > 0.5% the next 60 min averages +9.9 bps, after a 60-min rise
> 0.5% it averages -25.7 bps. Fast trend-following whipsaws (the house
EMA-cross loses -$106 on dev); buying a dip vs the 6h mean and exiting at
the mean captures the reversion while paying only ~35 bps per round trip.
See REPORT.md for dev numbers and robustness checks.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SMA_LEN = 360          # 6 hours of 1-minute closes
DIP_NUM = 991          # buy when close < SMA * 991/1000  (0.9% below the mean)
DIP_DEN = 1000
FALLBACK_SEQ = 1200    # bar from which the guardrail fallback may fire
MAX_SLIP_BPS = 10000


class Strategy:
    """Pure state: closes history + whether the fallback has fired."""

    def __init__(self, sma_len=SMA_LEN, dip_num=DIP_NUM, dip_den=DIP_DEN,
                 fallback_seq=FALLBACK_SEQ):
        self.sma_len = sma_len
        self.dip_num = dip_num
        self.dip_den = dip_den
        self.fallback_seq = fallback_seq
        self.closes = []
        self.fallback_used = False
        self.ever_ordered = False  # True once any order has been issued

    def decide(self, close, cash, qty, seq):
        """Orders for this bar. close/cash/qty are ints; seq is the batch seq."""
        self.closes.append(close)
        if len(self.closes) < self.sma_len:
            return []
        sma_sum = sum(self.closes[-self.sma_len:])
        if qty > 0:
            # long: exit when the price is back at or above its 6h mean
            if close * self.sma_len >= sma_sum:
                self.ever_ordered = True
                return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                         "max_slippage_bps": MAX_SLIP_BPS}]
            return []
        # flat: buy a dip below the mean
        if close * self.sma_len * self.dip_den < sma_sum * self.dip_num:
            if cash > 0:
                self.ever_ordered = True
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": cash,
                         "max_slippage_bps": MAX_SLIP_BPS}]
            return []
        # guardrail fallback: never traded and late in the window — buy once
        # and hold to the end-of-window flatten, so a quiet race window still
        # records >= 1 trade. Gated on never having ordered: a bot that
        # already traded meets the bar, and a late buy after a completed
        # round trip only bleeds fees (on dev it would buy the 1285 top).
        if (seq >= self.fallback_seq and not self.fallback_used
                and not self.ever_ordered and cash > 0):
            self.fallback_used = True
            self.ever_ordered = True
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": cash,
                     "max_slippage_bps": MAX_SLIP_BPS}]
        return []


_STRAT = Strategy()


def on_batch(state, batch):
    if state.warming_up:
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    pos = state.positions.get(SYMBOL)
    qty = pos.qty if pos is not None else 0
    return _STRAT.decide(close, state.cash, qty, state.seq)


if __name__ == "__main__":
    makefun_bars.run(on_batch)
