"""Uses statsmodels when installed; otherwise small scipy/numpy equivalents (exact McNemar, Holm, Wilson CI)."""
import numpy as np
from scipy import stats

try:
    from statsmodels.stats.contingency_tables import mcnemar as _mc
    from statsmodels.stats.multitest import multipletests as _mt
    from statsmodels.stats.proportion import proportion_confint as _pc
    HAVE_STATSMODELS = True
except ImportError:  # pragma: no cover
    HAVE_STATSMODELS = False


class _R:
    def __init__(self, statistic, pvalue): self.statistic, self.pvalue = statistic, pvalue


def mcnemar(table, exact=True):
    if HAVE_STATSMODELS:
        return _mc(table, exact=exact)
    b, c = table[0][1], table[1][0]
    n = b + c
    if n == 0:
        return _R(0.0, 1.0)
    return _R(float(min(b, c)), float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5))))


def multipletests_holm(pvals):
    p = np.asarray(pvals, float)
    if HAVE_STATSMODELS:
        return _mt(p, method="holm")[1]
    m = len(p); order = np.argsort(p); adj = np.empty(m); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i]); adj[i] = min(1.0, run)
    return adj


def wilson(k, n, alpha=0.05):
    if HAVE_STATSMODELS:
        return _pc(k, n, alpha=alpha, method="wilson")
    z = stats.norm.ppf(1 - alpha / 2); ph = k / n
    d = 1 + z * z / n; ctr = (ph + z * z / (2 * n)) / d
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return ctr - h, ctr + h
