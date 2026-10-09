"""The function value f(x_k) is not monotone under momentum; the potential Phi_k is.

Heavy ball on the 1-D quadratic f(x) = x^2/2 (L = 1) with beta = 0.9 and the
largest step allowed by the main theorem, alpha = (1-beta)^2/(2L).

(a) deterministic run: the iterate x_k and the extrapolated point z_k;
(b) deterministic run: f(x_k) - f* oscillates, Phi_k decreases monotonically;
(c) stochastic run (sigma = 1, 20 000 repetitions): the expectations behave
    the same way until both settle at the noise floor.
"""
import numpy as np
import matplotlib.pyplot as plt

from common import (BLUE, ORANGE, INK2, MUTED, Quadratic, heavy_ball, lyapunov,
                    save, setup_style)


def main():
    setup_style()
    prob = Quadratic([1.0])
    beta = 0.9
    alpha = (1 - beta) ** 2 / (2 * prob.L)
    K = 300

    # ---- deterministic run ----------------------------------------------
    def rec(k, X, D):
        Z = X + beta / (1 - beta) * D
        return X[0, 0], Z[0, 0], prob.f(X)[0], lyapunov(prob, X, D, beta)[0]

    _, ks, vals = heavy_ball(lambda X, k: prob.grad(X), np.array([[1.0]]), alpha, beta, K,
                             record=rec)
    x, z, fx, phi = map(np.array, zip(*vals))
    assert np.all(np.diff(phi) <= 1e-15), "Phi must be non-increasing (Theorem 5.3, sigma = 0)"

    # ---- stochastic run ---------------------------------------------------
    rng = np.random.default_rng(1)
    R, sigma = 20000, 1.0

    def oracle(X, k):
        return prob.grad(X) + sigma * rng.standard_normal(X.shape)

    def rec_s(k, X, D):
        return prob.f(X).mean(), lyapunov(prob, X, D, beta).mean()

    _, ks_s, vals_s = heavy_ball(oracle, np.full((R, 1), 1.0), alpha, beta, K, record=rec_s)
    Ef, Ephi = map(np.array, zip(*vals_s))
    gamma = alpha / (1 - beta)
    floor = gamma * sigma**2 * (1 + beta) / (2 * (2 * (1 + beta) - alpha * prob.L))

    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.35))
    ax = axes[0]
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.plot(ks, x, color=BLUE, ls="-", label=r"iterate $x_k$")
    ax.plot(ks, z, color=ORANGE, ls="--", label=r"extrapolated $z_k$")
    ax.set_xlim(0, 150)
    ax.set_xlabel("iteration $k$")
    ax.set_title("(a) iterates (no noise)")
    ax.legend(loc="upper right")

    ax = axes[1]
    ax.semilogy(ks, fx, color=BLUE, ls="-", label=r"$f(x_k)-f^\star$")
    ax.semilogy(ks, phi, color=ORANGE, ls="--", label=r"potential $\Phi_k$")
    ax.set_ylim(1e-14, 10)
    ax.set_xlabel("iteration $k$")
    ax.set_title("(b) function value vs. potential")
    ax.legend(loc="upper right")

    ax = axes[2]
    ax.semilogy(ks_s, Ef, color=BLUE, ls="-", label=r"$\mathbb{E}\,f(x_k)-f^\star$")
    ax.semilogy(ks_s, Ephi, color=ORANGE, ls="--", label=r"$\mathbb{E}\,\Phi_k$")
    ax.axhline(floor, color=INK2, lw=0.8)
    ax.annotate("noise floor (Prop. 7.1)", xy=(K, floor), xytext=(K * 0.40, floor * 0.42),
                color=INK2, fontsize=7.5)
    ax.set_ylim(1e-3, 3)
    ax.set_xlabel("iteration $k$")
    ax.set_title(r"(c) with noise ($\sigma=1$)")
    ax.legend(loc="upper right")

    fig.tight_layout(w_pad=1.2)
    save(fig, "potential.pdf")
    print(f"  alpha={alpha:.4g}, gamma={gamma:.4g}, predicted floor E f = {floor:.4g}, "
          f"empirical tail mean E f = {Ef[-100:].mean():.4g}")


if __name__ == "__main__":
    main()
