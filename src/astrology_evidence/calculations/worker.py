"""JSON-only calculation subprocess entry point for isolated native engine state."""

import json
import sys

from astrology_evidence.calculations import BirthInput, ChartSettings, calculate_chart


def main():
    try:
        payload = json.load(sys.stdin)
        chart = calculate_chart(
            BirthInput.model_validate(payload["birth"]),
            ChartSettings.model_validate(payload["settings"]),
        )
        print(chart.model_dump_json())
    except Exception:
        print(json.dumps({"error": "calculation_failed"}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
