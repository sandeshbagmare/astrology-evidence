"""Process adapter tests never transmit credentials to the calculation worker."""

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from astrology_evidence.calculations import BirthInput, ChartSettings
from astrology_evidence.calculations.adapter import calculator


def test_calculation_process_failure_is_safe(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-private-marker")
    settings = SimpleNamespace(
        calculation_python="python", calculation_pythonpath="trusted-local-path"
    )
    birth = BirthInput(
        birth_date="1990-01-01",
        local_time="12:00",
        time_precision="exact",
        latitude=1.0,
        longitude=2.0,
        timezone="UTC",
        timezone_history="confirmed",
    )
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("python", 15)) as run:
        with pytest.raises(RuntimeError, match="Calculation service unavailable"):
            calculator(settings)(birth, ChartSettings())
    assert "OPENAI_API_KEY" not in run.call_args.kwargs["env"]
    assert run.call_args.kwargs["timeout"] == 15
    assert run.call_args.args[0][1:] == ["-m", "astrology_evidence.calculations.worker"]
    assert "shell" not in run.call_args.kwargs
