"""Shared pieces for the numerical illustrations in the SGDM report.

Contents
--------
* Plot styling (validated colour palette, thin marks, recessive grid).
* Test problems:
    - ``Quadratic``          f(x) = 0.5 * sum_i h_i x_i^2
    - ``PLNonconvex``        f(x) = sum_i (x_i^2 + 3 sin^2 x_i)   (nonconvex, PL)
    - ``NonconvexLogistic``  logistic loss + nonconvex regulariser
    - ``LRPFunction``        the strongly convex counterexample of
                             Lessard, Recht & Packard (2016)
* ``heavy_ball`` -- the SGDM iteration in heavy-ball form,
      x_{k+1} = x_k - alpha_k g_k + beta (x_k - x_{k-1}),
  vectorised over independent runs (rows of the state matrix).

Every script in this folder imports from here, so all figures share one
definition of the algorithm.
"""
from __future__ import annotations

import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
# Categorical slots in fixed order (validated for colour-vision deficiency
# on a white surface); line styles provide a secondary, colour-free encoding
# so the figures also survive greyscale printing.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SERIES = [BLUE, ORANGE, AQUA, YELLOW]
LINESTYLES = ["-", "--", "-.", ":"]
MARKERS = ["o", "s", "^", "D"]
# Ordinal one-hue ramp (light -> dark) for nested regions.
RAMP = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
# Chart chrome / ink.
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "report", "figures")


def setup_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "mathtext.fontset": "dejavusans",
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "text.color": INK,
        "axes.labelcolor": INK2,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "grid.linestyle": "-",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 1.6,
        "lines.solid_capstyle": "round",
        "lines.dash_capstyle": "round",
        "legend.frameon": False,
        "axes.titlelocation": "left",
        "axes.titlecolor": INK,
    })


def save(fig, name: str) -> str:
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {os.path.relpath(path)}")
    return path


# --------------------------------------------------------------------------
# Test problems.  Each exposes f(X), grad(X) for X of shape (R, d) (one row
# per independent run), the smoothness constant L, and f_star = inf f.
# --------------------------------------------------------------------------
class Quadratic:
    """f(x) = 0.5 * sum_i h_i x_i^2 with curvatures h_i > 0."""

    def __init__(self, h):
        self.h = np.asarray(h, dtype=float)
        self.d = self.h.size
        self.L = float(self.h.max())
        self.mu = float(self.h.min())
        self.f_star = 0.0

    def f(self, X):
        return 0.5 * np.sum(self.h * X**2, axis=-1)

    def grad(self, X):
        return self.h * X


class PLNonconvex:
    """f(x) = sum_i (x_i^2 + 3 sin^2 x_i).

    Nonconvex (f'' = 2 + 6 cos 2x takes negative values) yet it satisfies the
    Polyak-Lojasiewicz inequality with mu = 1/32 (Karimi et al., 2016).
    Smoothness constant L = 8, minimiser x* = 0, f* = 0.
    """

    L = 8.0
    mu = 1.0 / 32.0
    f_star = 0.0

    def __init__(self, d):
        self.d = d

    def f(self, X):
        return np.sum(X**2 + 3.0 * np.sin(X) ** 2, axis=-1)

    def grad(self, X):
        return 2.0 * X + 3.0 * np.sin(2.0 * X)


class NonconvexLogistic:
    """Binary logistic regression with the nonconvex regulariser
    lam * sum_j x_j^2 / (1 + x_j^2):

        f(x) = (1/n) sum_i log(1 + exp(-b_i a_i^T x)) + lam * sum_j x_j^2/(1+x_j^2).

    Mini-batch gradients (sampling with replacement) are unbiased with
    bounded variance, so Assumptions A1-A4 of the report hold, with
    L <= ||A||_2^2 / (4n) + 2 lam.
    """

    def __init__(self, n=1000, d=20, lam=0.1, seed=0):
        rng = np.random.default_rng(seed)
        A = rng.standard_normal((n, d))
        x_true = rng.standard_normal(d) * 2.0
        p = 1.0 / (1.0 + np.exp(-A @ x_true))
        b = np.where(rng.random(n) < p, 1.0, -1.0)
        self.A, self.b, self.lam, self.n, self.d = A, b, lam, n, d
        self.L = np.linalg.norm(A, 2) ** 2 / (4 * n) + 2 * lam
        self.f_star = 0.0  # a valid lower bound (both terms are >= 0)

    def f(self, X):
        Z = -(X @ self.A.T) * self.b                      # (R, n)
        loss = np.mean(np.logaddexp(0.0, Z), axis=-1)
        reg = self.lam * np.sum(X**2 / (1 + X**2), axis=-1)
        return loss + reg

    def _reg_grad(self, X):
        return self.lam * 2.0 * X / (1 + X**2) ** 2

    def grad(self, X):
        Z = -(X @ self.A.T) * self.b                      # (R, n)
        S = 0.5 * (1.0 + np.tanh(0.5 * Z))                # sigmoid(Z), stable
        G = -(S * self.b) @ self.A / self.n               # (R, d)
        return G + self._reg_grad(X)

    def stoch_grad(self, X, batch, rng):
        """Unbiased mini-batch gradient: indices drawn uniformly with replacement."""
        R = X.shape[0]
        idx = rng.integers(0, self.n, size=(R, batch))
        Ab = self.A[idx]                                  # (R, B, d)
        bb = self.b[idx]                                  # (R, B)
        z = -np.einsum("rbd,rd->rb", Ab, X) * bb
        s = 0.5 * (1.0 + np.tanh(0.5 * z))
        G = -np.einsum("rb,rbd->rd", s * bb, Ab) / batch
        return G + self._reg_grad(X)


class LRPFunction:
    """Strongly convex, smooth counterexample (mu = 1, L = 25) from
    Lessard, Recht & Packard (2016, Sec. 4.6):

        f(x) = 25 x^2 / 2              if x < 1
             = x^2 / 2 + 24 x - 12     if 1 <= x < 2
             = 25 x^2 / 2 - 24 x + 36  if x >= 2
    """

    L, mu, f_star = 25.0, 1.0, 0.0

    @staticmethod
    def f(x):
        x = np.asarray(x, dtype=float)
        return np.where(x < 1, 12.5 * x**2,
                        np.where(x < 2, 0.5 * x**2 + 24 * x - 12, 12.5 * x**2 - 24 * x + 36))

    @staticmethod
    def grad(x):
        x = np.asarray(x, dtype=float)
        return np.where(x < 1, 25 * x, np.where(x < 2, x + 24, 25 * x - 24))


# --------------------------------------------------------------------------
# The algorithm
# --------------------------------------------------------------------------
def heavy_ball(grad_oracle, x0, alphas, beta, n_iter, record=None, record_every=1):
    """Run SGDM in heavy-ball form, vectorised over runs.

    Parameters
    ----------
    grad_oracle : callable (X, k) -> G returning a (stochastic) gradient for
        every row of X at iteration k.
    x0 : array (R, d) of starting points (x_{-1} = x_0, i.e. zero velocity).
    alphas : float or callable k -> alpha_k.
    beta : momentum parameter in [0, 1).
    record : optional callable (k, X, D) -> value, evaluated at
        k = 0, record_every, 2*record_every, ...; X = x_k and D = x_k - x_{k-1}.

    Returns (X_final, list_of_iterations, list_of_recorded_values).
    """
    X = np.array(x0, dtype=float)
    D = np.zeros_like(X)                       # d_0 = x_0 - x_{-1} = 0
    alpha_of = alphas if callable(alphas) else (lambda k, a=alphas: a)
    ks, vals = [], []
    for k in range(n_iter + 1):
        if record is not None and k % record_every == 0:
            ks.append(k)
            vals.append(record(k, X, D))
        if k == n_iter:
            break
        G = grad_oracle(X, k)
        D = beta * D - alpha_of(k) * G         # d_{k+1} = beta d_k - alpha_k g_k
        X = X + D                              # x_{k+1} = x_k + d_{k+1}
    return X, np.array(ks), vals


def lyapunov(problem, X, D, beta):
    """Phi_k = f(z_k) - f* + L beta^2 / (2 (1-beta)^2) * ||x_k - x_{k-1}||^2,
    with z_k = x_k + beta/(1-beta) (x_k - x_{k-1})."""
    Z = X + beta / (1.0 - beta) * D
    c = problem.L * beta**2 / (2.0 * (1.0 - beta) ** 2)
    return problem.f(Z) - problem.f_star + c * np.sum(D**2, axis=-1)
