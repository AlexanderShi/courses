"""Diminishing step sizes remove the noise floor.

(a) nonconvex logistic regression, beta = 0.9, mini-batch 1, 50 runs:
    constant gamma = (1-beta)/(2L) vs. gamma_k = gamma_0 / sqrt(k+1)   (Theorem 6.4);
(b) nonconvex PL function (d = 10, additive noise, sigma = 1), beta = 0.9, 100 runs:
    constant gamma = (1-beta)/(2L) vs. gamma_k = 8 / (mu (k + a)),
    a = 16 L / (mu (1-beta))                                            (Corollary 6.7).
Both schedules start from the same gamma_0; momentum is used in heavy-ball form with
alpha_k = (1-beta) gamma_k.
"""
import numpy as np
import matplotlib.pyplot as plt

from common import (BLUE, ORANGE, MUTED, LINESTYLES, NonconvexLogistic, PLNonconvex,
                    heavy_ball, save, setup_style)


def log_record_steps(K, n=200):
    return np.unique(np.concatenate([[0], np.round(np.logspace(0, np.log10(K), n)).astype(int)]))


def run(problem, oracle, x0, gammas, beta, K, quantity):
    steps = set(log_record_steps(K).tolist())
    out_k, out_v = [], []

    def rec(k, X, D):
        if k in steps:
            out_k.append(k)
            out_v.append(quantity(X).mean())
        return None

    heavy_ball(oracle, x0, lambda k: (1 - beta) * gammas(k), beta, K, record=rec)
    return np.array(out_k), np.array(out_v)


def main():
    setup_style()
    beta = 0.9
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))

    # ---------------- (a) nonconvex logistic --------------------------------
    prob = NonconvexLogistic()
    g0 = (1 - beta) / (2 * prob.L)
    K, R = 100000, 50
    x0 = np.tile(np.full(prob.d, -1.0), (R, 1))
    ax = axes[0]
    for j, (name, sched) in enumerate([
            (r"constant $\gamma=\gamma_0$", lambda k: g0),
            (r"$\gamma_k=\gamma_0/\sqrt{k+1}$", lambda k: g0 / np.sqrt(k + 1))]):
        rng = np.random.default_rng(7 + j)
        ks, v = run(prob, lambda X, k: prob.stoch_grad(X, 1, rng), x0, sched, beta, K,
                    lambda X: np.sum(prob.grad(X) ** 2, axis=-1))
        ax.loglog(ks[1:], v[1:], color=[BLUE, ORANGE][j], ls=LINESTYLES[j], label=name)
    kk = np.logspace(3, 5, 10)
    ax.loglog(kk, 0.5 * v[-1] * np.sqrt(K / kk), color=MUTED, lw=0.8, ls=":",
              label=r"slope $-1/2$")
    ax.set_xlabel("iteration $k$")
    ax.set_ylabel(r"$\mathbb{E}\,\|\nabla f(x_k)\|^2$")
    ax.set_title("(a) nonconvex logistic regression")
    ax.legend(loc="lower left")

    # ---------------- (b) PL function -----------------------------------------
    pl = PLNonconvex(d=10)
    L, mu, sigma = pl.L, pl.mu, 1.0
    g0 = (1 - beta) / (2 * L)
    a = 16 * L / (mu * (1 - beta))
    K, R = 1_000_000, 100
    x0 = np.full((R, pl.d), 3.0)
    ax = axes[1]
    for j, (name, sched) in enumerate([
            (r"constant $\gamma=(1-\beta)/(2L)$", lambda k: g0),
            (r"$\gamma_k=8/(\mu(k+a))$", lambda k: 8.0 / (mu * (k + a)))]):
        rng = np.random.default_rng(70 + j)
        ks, v = run(pl, lambda X, k: pl.grad(X) + sigma / np.sqrt(pl.d)
                    * rng.standard_normal(X.shape), x0, sched, beta, K, pl.f)
        ax.loglog(ks[1:], v[1:], color=[BLUE, ORANGE][j], ls=LINESTYLES[j], label=name)
        print(f"  PL {name}: final E f = {v[-1]:.3g}")
    kk = np.logspace(5, 6, 10)
    ax.loglog(kk, 0.5 * v[-1] * K / kk, color=MUTED, lw=0.8, ls=":", label=r"slope $-1$")
    ax.set_xlabel("iteration $k$")
    ax.set_ylabel(r"$\mathbb{E}\,f(x_k)-f^\star$")
    ax.set_ylim(1e-7, 300)
    ax.set_title("(b) nonconvex PL function")
    ax.legend(loc="lower left")
    fig.tight_layout(w_pad=1.5)
    save(fig, "diminishing.pdf")


if __name__ == "__main__":
    main()
