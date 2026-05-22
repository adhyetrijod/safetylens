"""
Simulation engine — scenario-based parameter drift modelling.
"""

import numpy as np
from typing import List

SCENARIOS = {
    "Sensor drift (gradual)": {
        "description": "Models slow sensor drift or gradual process deviation. Common cause: fouled sensor, slow leak, heat exchanger scaling.",
        "default_drift": 0.5,
        "direction": "up",
    },
    "Sudden upset (step change)": {
        "description": "Models an abrupt process disturbance — pump trip, valve stuck open/closed, feed composition change.",
        "default_drift": 2.5,
        "direction": "up",
    },
    "Thermal runaway": {
        "description": "Models accelerating temperature rise — typical of exothermic reactions with loss of cooling.",
        "default_drift": 1.5,
        "direction": "up",
    },
    "Concentration depletion": {
        "description": "Models falling reagent concentration — bath depletion, dosing pump failure, dilution by water ingress.",
        "default_drift": 0.8,
        "direction": "down",
    },
    "Pressure loss": {
        "description": "Models falling pressure — leak, seal failure, blocked inlet.",
        "default_drift": 1.0,
        "direction": "down",
    },
    "Oscillating instability": {
        "description": "Models control loop hunting or PID oscillation around setpoint — typical of poorly tuned controllers.",
        "default_drift": 0.3,
        "direction": "oscillate",
    },
}


def run_scenario_simulation(
    soc_lo: float,
    soc_hi: float,
    sol_lo: float,
    sol_hi: float,
    steps: int,
    noise_pct: float,
    drift_rate: float,
    direction: str,
) -> List[float]:
    """
    Simulates a parameter trajectory under a given scenario.
    Returns list of values length = steps.
    """
    start   = (soc_lo + soc_hi) / 2
    span    = sol_hi - sol_lo if sol_hi > sol_lo else 100
    noise_σ = span * noise_pct

    values = [start]
    for i in range(1, steps):
        prev  = values[-1]
        noise = np.random.normal(0, noise_σ)

        if direction == "up":
            # Accelerating drift upward
            accel = 1 + (i / steps) * 0.5
            drift = span * drift_rate * accel
            new   = prev + drift + noise

        elif direction == "down":
            accel = 1 + (i / steps) * 0.5
            drift = span * drift_rate * accel
            new   = prev - drift + noise

        elif direction == "oscillate":
            amplitude = span * drift_rate * (1 + i / steps)
            new = start + amplitude * np.sin(i * 0.4) + noise

        else:
            new = prev + noise

        values.append(round(new, 4))

    return values


def generate_drift_series(
    baseline: float,
    span: float,
    steps: int = 30,
    noise_pct: float = 0.03,
) -> List[float]:
    """Generates a short stable random walk for control chart display."""
    noise_σ = span * noise_pct
    values  = [baseline]
    for _ in range(steps - 1):
        values.append(round(values[-1] + np.random.normal(0, noise_σ), 4))
    return values
