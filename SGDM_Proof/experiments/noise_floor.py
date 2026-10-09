"""With a constant step, SGDM stalls at a noise floor proportional to gamma*sigma^2,
and (to first order) the floor depends on (alpha, beta) only through gamma = alpha/(1-beta).

(a) quadratic f(x) = x^2/2 with additive N(0, 1) noise: empirical stationary E f(x_k)
    (markers) vs. the exact formula of Proposition 7.1 (lines);
(b) nonconvex PL function f(x) = sum_i (x_i^2 + 3 sin^2 x_i), d = 10, additive Gaussian
    noise with E||noise||^2 = 1: long-run E||grad f(x_k)||^2 vs. the bound 4 L gamma sigma^2
    of Theorem 6.1 (K -> infinity) and the local-quadratic prediction h gamma sigma^2 / 2, h = 8.
Only step sizes inside the theorem's range gamma <= (1-beta)/(2L) are used in (b).
"""
import numpy as np
import matplotlib.pyplot as plt

from common import (BLUE, ORANGE, AQUA, INK2, MUTED, PLNonconvex, Quadratic,
                    heavy_ball, save, setup_style)

BETAS = [0.0, 0.5, 0.9]
COLORS = [BLUE, ORANGE, AQUA]
# Markers coincide when the floor depends only on gamma, so use nested shapes:
# large hollow circle, medium hollow square, small filled triangle.
MARK = [dict(marker="o", ms=8.5, mfc="none", mew=1.3),
        dict(marker="s", ms=6.0, mfc="none", mew=1.3),
        dict(marker="^", ms=4.5, mew=0.0)]


def stationary_mean(problem, quantity, alpha, beta, sigma, K_burn, K_avg, R, seed):
    rng = np.random.default_rng(seed)
    d = problem.d

    def oracle(X, k):
        return problem.grad(X) + sigma / np.sqrt(d) * rng.standard_normal(X.shape)

    acc = []

    def rec(k, X, D):
        if k >= K_burn:
            acc.append(quantity(X).mean())
        return None

    heavy_ball(oracle, np.zeros((R, d)), alpha, beta, K_burn + K_avg, record=rec, record_every=5)
    return float(np.mean(acc))


def main():
    setup_style()
    sigma = 1.0
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))

    # ---------------- (a) quadratic: exact formula ------------------------
    quad = Quadratic([1.0])
    h = 1.0
    ax = axes[0]
    gammas = np.logspace(-3, -0.3, 7)
    gg = np.logspace(-3.1, -0.2, 100)
    for j, beta in enumerate(BETAS):
        emp = []
        for i, g in enumerate(gammas):
            alpha = (1 - beta) * g
            K_burn = int(10 / (g * h)) + 200
            emp.append(stationary_mean(quad, quad.f, alpha, beta, sigma, K_burn, 4000, 4000,
                                       seed=100 * j + i))
        a = (1 - beta) * gg
        theory = gg * sigma**2 * (1 + beta) / (2 * (2 * (1 + beta) - a * h))
        ax.loglog(gg, theory, color=COLORS[j], lw=1.2)
        ax.loglog(gammas, emp, ls="none", color=COLORS[j], label=rf"$\beta={beta}$", **MARK[j])
        print(f"  quad beta={beta}: emp/theory = "
              + ", ".join(f"{e / (g * (1 + beta) / (2 * (2 * (1 + beta) - (1 - beta) * g))):.3f}"
                          for e, g in zip(emp, gammas)))
    ax.loglog(gg, gg * sigma**2 / 4, color=MUTED, lw=0.8, ls=":", label=r"$\gamma\sigma^2/4$")
    ax.set_xlabel(r"effective step $\gamma=\alpha/(1-\beta)$")
    ax.set_ylabel(r"stationary $\mathbb{E}\,f(x_k)-f^\star$")
    ax.set_title(r"(a) quadratic: exact floor (Prop. 7.1)")
    ax.legend(loc="upper left")

    # ---------------- (b) nonconvex PL function: bound -------------------
    pl = PLNonconvex(d=10)
    L = pl.L
    ax = axes[1]

    def gn2(X):
        return np.sum(pl.grad(X) ** 2, axis=-1)

    base = np.array([1 / 160 * 2.0 ** (-j) for j in range(6, -4, -1)])   # 9.8e-5 ... 0.05
    for j, beta in enumerate(BETAS):
        gams = base[base <= (1 - beta) / (2 * L) + 1e-12]
        emp = []
        for i, g in enumerate(gams):
            alpha = (1 - beta) * g
            K_burn = int(10 / (8 * g)) + 500
            emp.append(stationary_mean(pl, gn2, alpha, beta, sigma, K_burn, 6000, 400,
                                       seed=1000 + 100 * j + i))
        ax.loglog(gams, emp, ls="none", color=COLORS[j], label=rf"$\beta={beta}$", **MARK[j])
    gg = np.logspace(-4.2, -1.1, 100)
    ax.loglog(gg, 4 * L * gg * sigma**2, color=INK2, lw=1.0, label=r"bound $4L\gamma\sigma^2$")
    ax.loglog(gg, 8 * gg * sigma**2 / 2, color=MUTED, lw=0.8, ls=":",
              label=r"$h\gamma\sigma^2/2$, $h=8$")
    ax.set_xlabel(r"effective step $\gamma=\alpha/(1-\beta)$")
    ax.set_ylabel(r"long-run $\mathbb{E}\,\|\nabla f(x_k)\|^2$")
    ax.set_title("(b) nonconvex PL function: bound")
    ax.legend(loc="upper left", ncol=1)
    fig.tight_layout(w_pad=1.5)
    save(fig, "noise_floor.pdf")


if __name__ == "__main__":
    main()
