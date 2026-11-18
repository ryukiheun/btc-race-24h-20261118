"""DipSnap: a long-only BTC dip-buying bot for make.fun's 24-hour BTC race.

Protocol: the harness sends one hello line, then one batch per minute.
Each batch carries the closed bar and the previous reply's fills plus the
account. The bot answers with a list of orders (at most one here), or an
empty list. Fills happen at the next bar's open, so every decision uses
the latest close while the fill price is one minute ahead.

Strategy, in one paragraph: buy the whole cash balance when the latest
close has fallen at least 1.6% below the highest close of the last 180
bars, then sell everything when the close rises 1.0% above the entry
reference or falls 1.2% below the highest close since entry. Two guards
keep the bot alive in the wrong regime: if no trade has happened by bar
720 the entry dip loosens to 1.2% (0.8% after bar 1200), and after two
trailing-stop exits in a row the bot stops entering for the window.

Everything is integer math on quote units (micro-USDC). No randomness,
no clock, no environment reads: the same bars always produce the same
orders.
"""

import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars  # noqa: E402  (vendor shim, copied byte-for-byte from the kit)

SYMBOL = "CBBTC"

LOOKBACK_BARS = 180          # rolling-high window (3 hours of 1-minute bars)
TAKE_PROFIT_PCT = 100        # close >= entry_ref * 101 / 100  -> sell
TRAILING_STOP_PCT = 988      # close <= peak * 988 / 1000      -> sell
ENTRY_DIP = 984              # close <= high * 984 / 1000      -> buy
ENTRY_DIP_RELAXED = 988      # after bar 720 with no trade yet
ENTRY_DIP_LAST_CHANCE = 992  # after bar 1200 with no trade yet
RELAX_BAR = 720
LAST_CHANCE_BAR = 1200
MIN_NOTIONAL = 1_000_000     # $1 in quote units
MAX_SLIPPAGE_BPS = 200
MAX_CONSEC_STOPS = 2


def make_bot():
    """Return the on_batch callback. All bot state lives in this closure,
    never on the SDK state object, so a fresh state each batch cannot
    wipe the rolling history."""
    closes = deque(maxlen=LOOKBACK_BARS)
    entry_ref = None   # close of the first batch where a position appears
    peak = None        # highest close seen while holding
    trades_done = 0    # buy decisions made so far
    consec_stops = 0   # trailing-stop exits in a row (a take-profit resets it)

    def buy_all_cash(cash):
        return [{
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": cash,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    def sell_all(qty):
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    def on_batch(state, batch):
        nonlocal entry_ref, peak, trades_done, consec_stops
        bar = state.latest.get(SYMBOL)
        if bar is None:
            return []  # no bar for this symbol: send nothing, touch nothing
        close = int(bar["c"])
        closes.append(close)

        if SYMBOL in state.positions:
            if entry_ref is None:
                entry_ref = close
                peak = close
            if close > peak:
                peak = close
            if close * 100 >= entry_ref * 101:
                entry_ref = None
                peak = None
                consec_stops = 0
                return sell_all(state.positions[SYMBOL].qty)
            if close * 1000 <= peak * TRAILING_STOP_PCT:
                entry_ref = None
                peak = None
                consec_stops += 1
                return sell_all(state.positions[SYMBOL].qty)
            return []

        entry_ref = None
        peak = None
        if consec_stops >= MAX_CONSEC_STOPS:
            return []
        if trades_done == 0 and state.seq >= LAST_CHANCE_BAR:
            dip = ENTRY_DIP_LAST_CHANCE
        elif trades_done == 0 and state.seq >= RELAX_BAR:
            dip = ENTRY_DIP_RELAXED
        else:
            dip = ENTRY_DIP
        if len(closes) >= LOOKBACK_BARS and close * 1000 <= max(closes) * dip:
            if state.cash > MIN_NOTIONAL:
                trades_done += 1
                return buy_all_cash(state.cash)
        return []

    return on_batch


if __name__ == "__main__":
    makefun_bars.run(make_bot())
