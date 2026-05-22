"""
Risk engine — industry-agnostic scoring and deviation detection.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def score_chemicals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "risk_score" not in df.columns:
        return df
    df = df.copy()
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(50).clip(0, 100)
    df["risk_band"] = df["risk_score"].apply(
        lambda s: "High" if s >= 70 else "Medium" if s >= 40 else "Low"
    )
    return df


def score_parameters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "risk_score" not in df.columns:
        return df
    df = df.copy()
    for col in ["soc_min","soc_max","sol_min","sol_max","risk_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["sol_bandwidth"] = (df["sol_max"] - df["sol_min"]).abs()
    df["soc_bandwidth"] = (df["soc_max"] - df["soc_min"]).abs()
    df["margin_tightness"] = df.apply(
        lambda r: r["soc_bandwidth"] / r["sol_bandwidth"] if r["sol_bandwidth"] > 0 else 1.0, axis=1
    )
    df["risk_score"] = (df["risk_score"].clip(0, 100)).round(1)
    return df


def get_deviation_status(
    value: float,
    soc: Tuple[float, float],
    sol: Tuple[float, float],
) -> Tuple[str, str]:
    soc_min, soc_max = sorted(soc)
    sol_min, sol_max = sorted(sol)
    if sol_min <= value <= sol_max:
        if soc_min <= value <= soc_max:
            return "Normal", "#38a169"
        return "SOC breach — take corrective action", "#dd6b20"
    return "SOL breach — STOP LINE", "#e53e3e"


def generate_alerts(parameters: pd.DataFrame, current_readings: dict) -> list:
    alerts = []
    for _, row in parameters.iterrows():
        param = row["parameter"]
        if param not in current_readings:
            continue
        v = current_readings[param]
        soc = (float(row.get("soc_min", 0)), float(row.get("soc_max", 100)))
        sol = (float(row.get("sol_min", 0)), float(row.get("sol_max", 100)))
        status, color = get_deviation_status(v, soc, sol)
        if status != "Normal":
            alerts.append({
                "parameter":  param,
                "process":    row.get("process", "—"),
                "value":      v,
                "unit":       row.get("uom", ""),
                "status":     status,
                "color":      color,
                "consequence":row.get("consequence", "—"),
                "risk_score": int(row.get("risk_score", 50)),
            })
    return sorted(alerts, key=lambda x: x["risk_score"], reverse=True)


def compute_plant_risk_index(processes: pd.DataFrame, parameters: pd.DataFrame) -> float:
    if processes.empty:
        if parameters.empty:
            return 0.0
        return round(float(parameters["risk_score"].mean()), 1)
    if "risk_score" not in processes.columns:
        return 0.0
    w_map = {"HHO": 1.5, "LHO": 0.8, "Safe": 0.3}
    weights = processes.get("classification", pd.Series(["LHO"]*len(processes))).map(w_map).fillna(1.0)
    scores  = pd.to_numeric(processes["risk_score"], errors="coerce").fillna(50)
    return round(float((scores * weights).sum() / weights.sum()), 1)
