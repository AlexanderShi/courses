"""Where in the (beta, alpha) plane does each guarantee hold?

Nested regions (largest to smallest), all for an L-smooth objective:
  R4  quadratic objectives, exact gradients: stable iff alpha L < 2(1+beta)      (Prop. 7.2)
  R3  any L-smooth f, exact gradients: energy decreases if alpha L < 2(1-beta)   (Prop. 7.3)
  R2  convex f, stochastic gradients: alpha L <= (1-beta)/2                      (Thm. 6.8)
  R1  nonconvex f, stochastic gradients: alpha L <= (1-beta)^2/2                 (Thm. 5.3)
The star marks the parameters of the Lessard-Recht-Packard counterexample
(beta = 4/9, alpha L = 25/9): inside R4, outside R3.
Panel (b) shows the same regions in terms of the effective step gamma = alpha/(1-beta).
"""
import numpy as np
import matplotlib.pyplot as plt

from common import INK, RAMP, save, setup_style


def main():
    setup_style()
    beta = np.linspace(0.0, 0.99, 600)
    bounds_alpha = [
        (2 * (1 + beta), "R4: quadratic $f$, exact gradients", "white"),
        (2 * (1 - beta), "R3: any smooth $f$, exact gradients", "white"),
        ((1 - beta) / 2, "R2: convex $f$, stochastic", "white"),
        ((1 - beta) ** 2 / 2, "R1: nonconvex $f$, stochastic", "white"),
    ]
    lo = 1e-5
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for panel, ax in enumerate(axes):
        scale = 1.0 if panel == 0 else 1.0 / (1 - beta)        # alpha L  ->  gamma L
        for j, (b, label, _) in enumerate(bounds_alpha):
            ax.fill_between(beta, lo, b * scale, color=RAMP[j], lw=0, label=label)
            ax.plot(beta, b * scale, color=RAMP[min(j + 1, 3)] if j < 3 else RAMP[3], lw=0.8)
        b_lrp, a_lrp = 4 / 9, 25 / 9
        y_lrp = a_lrp if panel == 0 else a_lrp / (1 - b_lrp)
        ax.plot([b_lrp], [y_lrp], marker="*", ms=11, color="#eb6834", mec="white", mew=1.0,
                ls="none", label="LRP counterexample", zorder=5)
        ax.set_yscale("log")
        ax.set_xlim(0, 0.99)
        ax.set_xlabel(r"momentum $\beta$")
        ax.grid(False)
        if panel == 0:
            ax.set_ylim(lo, 20)
            ax.set_ylabel(r"$\alpha L$  (step size $\times$ smoothness)")
            ax.set_title(r"(a) in terms of the step size $\alpha$")
        else:
            ax.set_ylim(1e-3, 1e3)
            ax.set_ylabel(r"$\gamma L = \alpha L/(1-\beta)$")
            ax.set_title(r"(b) in terms of the effective step $\gamma$")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.13),
               labelcolor=INK)
    fig.tight_layout(w_pad=2.0)
    save(fig, "regions.pdf")


if __name__ == "__main__":
    main()
