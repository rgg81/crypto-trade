"""Transparent stateless example. Copy this structure; replace the causal signal deliberately."""


class Strategy:
    def target_weights(self, context, *, seed):
        scores = {}
        weights = {}
        for symbol in context.eligible_symbols:
            frame = context.bars[symbol]
            if frame.empty or len(frame) < 25:
                continue
            returns = frame["close"].tail(25).pct_change().dropna()
            if returns.empty:
                continue
            scores[symbol] = float(returns.tail(3).mean())
        if len(scores) < 2:
            return weights
        ordered = sorted(scores, key=lambda symbol: scores[symbol])
        weights[ordered[0]] = -0.1
        weights[ordered[-1]] = 0.1
        return weights


def build_strategy():
    return Strategy()
