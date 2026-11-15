"""Optional process-isolated native calculator; never invokes a shell."""

import json
import os
import subprocess

from astrology_evidence.calculations import (
    ChartSnapshot,
    calculate_chart,
)


def calculator(settings):
    def run(birth, chart_settings):
        if not settings.calculation_python:
            return calculate_chart(birth, chart_settings)
        env = {
            key: value
            for key, value in os.environ.items()
            if key in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH"}
        }
        if settings.calculation_pythonpath:
            env["PYTHONPATH"] = settings.calculation_pythonpath
        try:
            result = subprocess.run(
                [settings.calculation_python, "-m", "astrology_evidence.calculations.worker"],
                input=json.dumps(
                    {
                        "birth": birth.model_dump(mode="json"),
                        "settings": chart_settings.model_dump(mode="json"),
                    }
                ),
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
                check=True,
            )
            return ChartSnapshot.model_validate_json(result.stdout)
        except (subprocess.SubprocessError, OSError, ValueError):
            raise RuntimeError("Calculation service unavailable") from None

    return run
