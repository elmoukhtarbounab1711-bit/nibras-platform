"""CLI لاستيراد القانون المقارن — فرنسا (DILA) وتحديثات يدوية.

الاستخدام:
    python scripts/import_comp_france.py [--dataset constitu|cass] [--skip-download]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services_comp_import import (
    FRANCE_DATASETS,
    import_france_decisions,
)


def main():
    ap = argparse.ArgumentParser(
        description="استيراد قرارات فرنسية إلى القانون المقارن (comp_*)")
    ap.add_argument(
        "--dataset", choices=list(FRANCE_DATASETS), default="constitu",
        help="مجموعة البيانات (constitu = المجلس الدستوري، cass = محكمة النقض)")
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()

    result = import_france_decisions(args.dataset)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    print(f"Run #{result['run_id']}: "
          f"found={result['found']}, imported={result['imported']}, "
          f"skipped={result['skipped']}, failed={result['failed']}")


if __name__ == "__main__":
    main()
