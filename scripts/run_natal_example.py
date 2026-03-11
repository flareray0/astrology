from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import astrology


def main() -> None:
    astrology.configure_ephemeris()

    natal = astrology.build_chart_from_input((1984, 11, 15), "11:27", 9, 37.38, 140.18, hsys="K")
    result = astrology.run_natal_report(natal, person_name="あなた")

    print("[OK] natal report generated")
    print("result_path:", result["result_path"])
    print("interpretation_path:", result["interpretation_path"])


if __name__ == "__main__":
    main()
