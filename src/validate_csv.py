from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "csv"

SPECS = {
    "psus.csv":         {"required": ["id", "wattage"], "ints": ["wattage"]},
    "cpus.csv":         {"required": ["id", "socket", "ramGen", "draw"], "ints": ["draw"]},
    "motherboards.csv": {"required": ["id", "socket", "ramGen", "formFactor", "interface"], "ints": []},
    "gpus.csv":         {"required": ["id", "lengthMm", "draw", "recommendedPsu"], "ints": ["lengthMm", "draw", "recommendedPsu"]},
    "ram.csv":          {"required": ["id", "ramGen"], "ints": []},
    "storage.csv":      {"required": ["id", "interface"], "ints": []},
    "cases.csv":        {"required": ["id", "acceptsFormFactor", "maxGpuMm"], "ints": ["maxGpuMm"]},
    "builds.csv":       {"required": ["id", "parts"], "ints": []},
}


def check_file(name, spec):
    errors = []
    path = CSV_DIR / name
    if not path.exists():
        return [f"{name}: file missing"]
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing_cols = [c for c in spec["required"] if c not in header]
        if missing_cols:
            return [f"{name}: missing columns {missing_cols}"]
        for i, row in enumerate(reader, start=2):
            for col in spec["required"]:
                if not (row.get(col) or "").strip():
                    errors.append(f"{name} row {i}: empty required field '{col}'")
            for col in spec["ints"]:
                val = (row.get(col) or "").strip()
                if val and not val.lstrip("-").isdigit():
                    errors.append(f"{name} row {i}: '{col}'='{val}' is not an integer")
    return errors


def validate_all():
    errors = []
    for name, spec in SPECS.items():
        errors.extend(check_file(name, spec))
    return errors


if __name__ == "__main__":
    import sys
    errs = validate_all()
    if errs:
        print(f"{len(errs)} validation error(s):")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)
    print("all CSVs valid")
