"""
agents/estimator_agent.py
--------------------------
Rule-based effort + cost estimator with an LLM-generated ROI overlay.
Result → state["estimation"]
"""
import json
import os

from langchain_core.messages import HumanMessage

from json_utils import parse_json
from llm_factory import get_llm


class EstimatorAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.rate_per_pm = int(os.getenv("RATE_PER_PERSON_MONTH", 8500))

    def run(self, state: dict) -> dict:
        req = state.get("requirements", {})

        # ── Extract numeric parameters safely ────────────────────────────────
        num_lines    = self._safe_int(req.get("lines"), 2)
        num_machines = self._safe_int(req.get("machine_types"), 5)
        has_erp      = self._safe_bool(req.get("erp"), True)
        custom       = str(req.get("customization", "medium")).lower()

        # ── Rule-based effort (person-months) ────────────────────────────────
        base_effort    = num_lines * 4
        machine_effort = num_machines * 2
        erp_effort     = 3 if has_erp else 0
        total_pm       = base_effort + machine_effort + erp_effort

        multiplier = {"high": 1.5, "low": 0.8}.get(custom, 1.0)
        total_pm   = round(total_pm * multiplier, 1)

        # ── Timeline (months) ────────────────────────────────────────────────
        disc   = 1.5
        config = round(max(3, num_lines * 1.5), 1)
        integ  = round(max(2, num_machines * 0.5), 1)
        test   = 2.0
        supp   = 1.0
        total_months = disc + config + integ + test + supp

        # ── Cost ─────────────────────────────────────────────────────────────
        total_cost = round(total_pm * self.rate_per_pm)

        # ── Phase breakdown ───────────────────────────────────────────────────
        phases = {
            "Discovery & Blueprint":    f"{disc} months",
            "Core MES Configuration":   f"{config} months",
            "Equipment Integration":    f"{integ} months",
            "Testing & Go-Live":        f"{test} months",
            "Post Go-Live Support":     f"{supp} months",
        }

        # ── ROI via LLM ──────────────────────────────────────────────────────
        roi = self._estimate_roi(num_lines, num_machines, has_erp, total_cost)

        state["estimation"] = {
            "num_lines":                num_lines,
            "num_machine_types":        num_machines,
            "erp_integration":          has_erp,
            "customization":            custom,
            "total_effort_person_months": total_pm,
            "total_duration_months":    total_months,
            "estimated_cost_usd":       total_cost,
            "phase_breakdown":          phases,
            "roi":                      roi,
        }
        return state

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _estimate_roi(self, lines, machines, has_erp, total_cost) -> dict:
        prompt = f"""
You are a manufacturing finance analyst. Estimate realistic ROI for an MES implementation.

Project parameters:
- Production lines: {lines}
- Machine types: {machines}
- ERP integration: {has_erp}
- Total investment: ${total_cost:,}

Return ONLY a JSON object with these keys:
{{
  "payback_months": <integer>,
  "annual_savings_usd": <integer>,
  "efficiency_gain_pct": <integer>,
  "oee_improvement_pct": <integer>,
  "quality_cost_reduction_pct": <integer>
}}
"""
        try:
            resp = self.llm.invoke([HumanMessage(content=prompt)])
            roi = parse_json(resp.content, fallback={})
        except Exception:
            roi = {}

        # Safe fallbacks
        roi.setdefault("payback_months", 24)
        roi.setdefault("annual_savings_usd", round(total_cost * 0.15))
        roi.setdefault("efficiency_gain_pct", 8)
        roi.setdefault("oee_improvement_pct", 5)
        roi.setdefault("quality_cost_reduction_pct", 20)
        return roi

    @staticmethod
    def _safe_int(value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_bool(value, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in ("", "none", "null", "false", "no")
        return default if value is None else bool(value)
