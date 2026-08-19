#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D
from PIL import Image

PAPER_THRESHOLD = 2


def render(mutated: bool, path: Path) -> None:
    angles = [-20, 0, 20]
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(-0.75, 0.75)
    ax.set_axis_off()

    markers = []
    originals = []
    for x, theta in enumerate(angles):
        marker_style = MarkerStyle(
            r"$\rightarrow$", transform=Affine2D().rotate_deg(theta)
        )
        (line,) = ax.plot(
            x,
            0,
            marker=marker_style,
            markersize=70,
            linestyle="None",
            color="black",
        )
        markers.append(line)
        originals.append(line.get_fillstyle())

    if mutated:
        for line, original_fillstyle in zip(markers, originals):
            line.set_fillstyle("left")
            line.set_fillstyle(original_fillstyle)

    fig.savefig(path, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def phash(path: Path, image_size: int = 32, lowfreq: int = 8) -> np.ndarray:
    image = Image.open(path).convert("L").resize(
        (image_size, image_size), Image.Resampling.LANCZOS
    )
    pixels = np.asarray(image, dtype=np.float64)
    n = image_size
    x = np.arange(n)
    k = np.arange(n)[:, None]
    dct_basis = np.cos(np.pi * (2 * x + 1) * k / (2 * n))
    dct_basis[0, :] *= 1 / np.sqrt(2)
    dct = (2 / n) * (dct_basis @ pixels @ dct_basis.T)
    block = dct[:lowfreq, :lowfreq].reshape(-1)
    ac = block[1:]
    return ac > np.median(ac)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results/live"))
    parser.add_argument("--expect-detected", action="store_true")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    seed = args.out / "seed.png"
    mutant = args.out / "set-revert.png"
    render(False, seed)
    render(True, mutant)

    distance = int(np.count_nonzero(phash(seed) != phash(mutant)))
    report = {
        "matplotlib_version": matplotlib.__version__,
        "case": "matplotlib#31257 adapted to endpoint-preserving set-revert",
        "mutation": "set_fillstyle('left') -> restore original fillstyle",
        "phash_distance": distance,
        "paper_threshold_tau": PAPER_THRESHOLD,
        "detected": distance > PAPER_THRESHOLD,
        "seed_image": seed.name,
        "mutant_image": mutant.name,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

    if args.expect_detected and not report["detected"]:
        raise SystemExit(
            f"Expected the paper-era bug to exceed pHash threshold {PAPER_THRESHOLD}, "
            f"but observed distance={distance}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
