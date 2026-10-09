"""Parameters that are optimal for quadratics can fail on a smooth strongly
convex function (Lessard, Recht & Packard, 2016).

Deterministic heavy ball on the LRP function (mu = 1, L = 25) from x_{-1} = x_0 = 3.3:
  * alpha = 1/9, beta = 4/9  (the classical quadratic-optimal tuning): the iterates are
    attracted to the 3-cycle {792, -2208, 2592}/1225 and never converge;
  * beta = 4/9 with alpha = 0.04 < 2(1-beta)/L (energy condition, Prop. 7.3): converges;
  * beta = 4/9 with alpha = (1-beta)^2/(2L) (stochastic nonconvex condition): converges.
"""
from fractions import Fraction

import numpy as np
import matplotlib.pyplot as plt

from common import BLUE, ORANGE, AQUA, MUTED, LINESTYLES, LRPFunction, save, setup_style


def hb(alpha, beta, x0, K):
    xs = [x0]
    x_prev, x = x0, x0
    for _ in range(K):
        x_new = x - alpha * float(LRPFunction.grad(x)) + beta * (x - x_prev)
        x_prev, x = x, x_new
        xs.append(x)
    return np.array(xs)


def check_cycle():
    """Exact verification (rational arithmetic) that the 3-cycle is a periodic orbit."""
    a, b = Fraction(1, 9), Fraction(4, 9)

    def g(x):
        return 25 * x if x < 1 else (x + 24 if x < 2 else 25 * x - 24)

    p = [Fraction(792, 1225), Fraction(-2208, 1225), Fraction(2592, 1225)]
    prev, cur = p[2], p[0]
    for i in range(6):
        nxt = cur - a * g(cur) + b * (cur - prev)
        assert nxt == p[(i + 1) % 3], (i, nxt)
        prev, cur = cur, nxt
    return [float(q) for q in p]


def main():
    setup_style()
    cyc = check_cycle()
    print("  verified exact 3-cycle:", [round(c, 4) for c in cyc])
    L, beta, x0, K = 25.0, 4 / 9, 3.3, 60
    runs = [
        (1 / 9, r"$\alpha=1/9$ (optimal for quadratics)"),
        (0.04, r"$\alpha=0.04<2(1-\beta)/L$"),
        ((1 - beta) ** 2 / (2 * L), r"$\alpha=(1-\beta)^2/(2L)$"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))
    for j, (alpha, lab) in enumerate(runs):
        xs = hb(alpha, beta, x0, K)
        col, ls = [ORANGE, BLUE, AQUA][j], LINESTYLES[j]
        if j == 0:
            axes[0].plot(np.arange(31), xs[:31], color=col, ls=ls, marker="o", ms=3.0,
                         label=lab)
        else:
            axes[0].plot(np.arange(31), xs[:31], color=col, ls=ls, label=lab)
        axes[1].semilogy(np.arange(K + 1), LRPFunction.f(xs), color=col, ls=ls, label=lab)
    for c in cyc:
        axes[0].axhline(c, color=MUTED, lw=0.6)
    axes[0].set_xlabel("iteration $k$")
    axes[0].set_ylabel("$x_k$")
    axes[0].set_title(r"(a) iterates, $\beta=4/9$, $x_0=3.3$")
    axes[1].set_xlabel("iteration $k$")
    axes[1].set_ylabel(r"$f(x_k)-f^\star$")
    axes[1].set_ylim(1e-12, 1e3)
    axes[1].set_title("(b) function value")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.tight_layout(w_pad=1.5)
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.08))
    save(fig, "counterexample.pdf")


if __name__ == "__main__":
    main()
