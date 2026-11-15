"""Write the API contract to backend/openapi.json. Usage: python -m backend.export_openapi"""

import json
from pathlib import Path

from backend.app import app

OUT = Path(__file__).resolve().parent / "openapi.json"


def main() -> None:
    text = json.dumps(app.openapi(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
