"""SGDM behaves like SGD run with the effective step gamma = alpha/(1-beta).

Nonconvex logistic regression (n = 1000, d = 20, mini-batch 1), 100 runs from
x_0 = (-1, ..., -1).
(a) matched effective step gamma = (1-0.9)/(2L) (inside the theorem's range
    for every beta shown): the three methods are indistinguishable;
(b) matched raw step alpha: momentum beta = 0.9 multiplies the effective step
    by 10 -- faster start, but a 10x higher noise floor.
Plotted: E ||grad f(x_k)||^2 (mean over runs, light centred moving average).
"""
import numpy as np
import matplotlib.pyplot as plt

from common import (BLUE, ORANGE, AQUA, LINESTYLES, NonconvexLogistic, heavy_ball, save,
                    setup_style)


def run(prob, alpha, beta, K, R, seed, batch=1, every=10):
    rng = np.random.default_rng(seed)
    x0 = np.tile(np.full(prob.d, -1.0), (R, 1))

    def oracle(X, k):
        return prob.stoch_grad(X, batch, rng)

    def rec(k, X, D):
        G = prob.grad(X)
        return np.mean(np.sum(G**2, axis=1))

    _, ks, vals = heavy_ball(oracle, x0, alpha, beta, K, record=rec, record_every=every)
    return ks, np.array(vals)


def smooth(y, w):
    """Centred moving average whose half-width grows with the index (at most w//2),
    so the fast early transient is not blurred on a logarithmic time axis."""
    y = np.asarray(y, dtype=float)
    c = np.concatenate([[0.0], np.cumsum(y)])
    i = np.arange(y.size)
    half = np.minimum(np.minimum(w // 2, i // 4), y.size - 1 - i)
    return (c[i + half + 1] - c[i - half]) / (2 * half + 1)


def main():
    setup_style()
    prob = NonconvexLogistic()
    L = prob.L
    K, R, every = 30000, 100, 10
    gamma = (1 - 0.9) / (2 * L)
    print(f"  L = {L:.3f}, gamma = {gamma:.4f}")

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    ax = axes[0]
    for j, beta in enumerate([0.0, 0.5, 0.9]):
        ks, g2 = run(prob, (1 - beta) * gamma, beta, K, R, seed=10 + j, every=every)
        lab = "SGD" if beta == 0 else rf"SGDM, $\beta={beta}$"
        ax.loglog(ks[1:], smooth(g2, 20)[1:], color=[BLUE, ORANGE, AQUA][j], ls=LINESTYLES[j],
                  label=lab + rf", $\alpha={(1 - beta) * gamma:.3f}$")
    ax.set_title(r"(a) same effective step $\gamma=\alpha/(1-\beta)$")
    ax.set_xlabel("iteration $k$")
    ax.set_ylabel(r"$\mathbb{E}\,\|\nabla f(x_k)\|^2$")
    ax.legend(loc="lower left")

    ax = axes[1]
    alpha = (1 - 0.9) ** 2 / (2 * L)
    for j, beta in enumerate([0.0, 0.9]):
        ks, g2 = run(prob, alpha, beta, K, R, seed=20 + j, every=every)
        lab = "SGD" if beta == 0 else rf"SGDM, $\beta={beta}$"
        ax.loglog(ks[1:], smooth(g2, 20)[1:], color=[BLUE, AQUA][j], ls=LINESTYLES[2 * j],
                  label=lab + rf" ($\gamma={alpha / (1 - beta):.4f}$)")
    ax.set_title(rf"(b) same step size $\alpha={alpha:.4f}$")
    ax.set_xlabel("iteration $k$")
    ax.legend(loc="upper right")
    fig.tight_layout(w_pad=1.5)
    save(fig, "sgd_vs_sgdm.pdf")


if __name__ == "__main__":
    main()
