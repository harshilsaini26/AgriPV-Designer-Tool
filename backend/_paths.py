"""Make the repo's own packages importable without installing them (spec §8).

Vercel bundles every file reachable at build time, with the project root as the working directory, so the
model core and the physics engine are imported straight from their source folders.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

for _src in (REPO_ROOT / "apv_core" / "src", REPO_ROOT / "apv_physics" / "src"):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
