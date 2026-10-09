"""Regenerate every figure of the report (takes about 2-3 minutes on a laptop)."""
import importlib
import time

SCRIPTS = [
    "potential",
    "regions",
    "sgd_vs_sgdm",
    "noise_floor",
    "diminishing",
    "counterexample",
]

if __name__ == "__main__":
    for name in SCRIPTS:
        t0 = time.time()
        print(f"[{name}]")
        importlib.import_module(name).main()
        print(f"  done in {time.time() - t0:.1f}s")
