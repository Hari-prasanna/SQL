import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
SHARED_UTILS_SRC = REPO_ROOT / "shared" / "logistics_data_utils" / "src"

for path in (PROJECT_ROOT / "src", SHARED_UTILS_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
