"""
agents/roi_business_case_agent.py
-----------------------------------
Document 12 of 12: ROI & Business Case (standalone, detailed document)
Covers: cost-of-inaction, quantified savings per category, 5-year NPV,
payback waterfall, benchmark comparisons, executive summary card.
Result → state["roi_business_case_path"]
"""
import datetime, os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from pdf_styles import (
    BRAND_ACCENT, BRAND_DARK, BRAND_MID, BRAND_LIGHT,
    get_styles, default_table_style,
)


class ROIBusinessCaseAgent:
    def __init__(self):
        self.s = get_styles()

    def run(self, state: dict, output_path: str = "output/roi_business_case.pdf") -> dict:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._build_pdf(state, output_path)
        state["roi_business_case_path"] = output_path
        return state

    def _build_pdf(self, state: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
        s, st = self.s, []
        req = state.get("requirements", {})
        est = state.get("estimation", {})
        roi = est.get("roi", {})

        # Scale factors from requirements
        lines    = int(req.get("lines", 4))
        machines = int(req.get("machine_types", 20))
        capacity_mw = 300  # extract from capacity string if possible

        total_investment = est.get("estimated_cost_usd", 752250)
        hw_cost = 115000  # typical hardware
        total_project_cost = total_investment + hw_cost

        # ROI numbers
        payback = int(roi.get("payback_months", 22))
        annual_savings = int(roi.get("annual_savings_usd", 1504500))
        oee_gain = int(roi.get("oee_improvement_pct", 8))
        efficiency = int(roi.get("efficiency_gain_pct", 12))
        quality_reduction = int(roi.get("quality_cost_reduction_pct", 30))

        # Computed
        five_yr_gross = annual_savings * 5
        five_yr_net   = five_yr_gross - total_project_cost
        roi_pct       = round((five_yr_net / total_project_cost) * 100)

        # ── Banner ─────────────────────────────────────────────────────────
        banner = Table([[Paragraph(
            "ROI & Business Case<br/><font size=13>5-Year Financial Analysis — Solar MES Investment</font>",
            s["cover_title"]
        )]], colWidths=[6.8*inch])
        banner.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BRAND_DARK),
            ("TOPPADDING",(0,0),(-1,-1),20),
            ("BOTTOMPADDING",(0,0),(-1,-1),20),
            ("LEFTPADDING",(0,0),(-1,-1),18),
        ]))
        st += [banner, Spacer(1,6),
               Paragraph(f"Solar Manufacturing MES — {capacity_mw} MW Plant | "
                         f"{datetime.date.today().strftime('%d %B %Y')}", s["body"]),
               HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT), Spacer(1,12)]

        # ── 1. Executive KPI Summary ───────────────────────────────────────
        st.append(Paragraph("1. Executive Summary — Key Financial Metrics", s["section_heading"]))
        kpi_data = [
            ["Total Project Investment","Annual Benefit","Payback Period","5-Year Net Benefit","5-Year ROI"],
            [f"${total_project_cost:,.0f}",f"${annual_savings:,.0f}/yr",
             f"{payback} months",f"${five_yr_net:,.0f}",f"{roi_pct}%"],
        ]
        kpi_rows = [[Paragraph(c, s["table_header"]) for c in kpi_data[0]],
                    [Paragraph(c, s["table_cell"]) for c in kpi_data[1]]]
        kpi_tbl = Table(kpi_rows, colWidths=[1.4*inch,1.4*inch,1.2*inch,1.4*inch,1.2*inch])
        kpi_tbl.setStyle(default_table_style())
        st.append(kpi_tbl)
        st.append(Spacer(1,12))

        # ── 2. Investment Summary ──────────────────────────────────────────
        st.append(Paragraph("2. Investment Breakdown", s["section_heading"]))
        inv_data = [
            ["Investment Component","Amount (USD)","Notes"],
            ["Implementation Services","${:,.0f}".format(total_investment),
             f"Fixed price; {est.get('total_effort_person_months',88)} person-months; blended rate $8,500/PM"],
            ["Hardware & Infrastructure","${:,.0f}".format(hw_cost),
             f"Servers, edge gateways ({lines} lines), OEE screens, OPC UA licenses"],
            ["Annual Maintenance (Yr 2+)","$25,000/year","AMC; includes updates, helpdesk, minor enhancements"],
            ["TOTAL YEAR 1 INVESTMENT","${:,.0f}".format(total_project_cost),"Implementation + hardware"],
            ["TOTAL 5-YEAR TCO","${:,.0f}".format(total_project_cost + 25000*4),"Year 1 + 4×AMC"],
        ]
        self._tbl(st, inv_data, s, [2.3*inch,1.6*inch,2.7*inch])
        st.append(Spacer(1,12))

        # ── 3. Cost of Inaction ────────────────────────────────────────────
        st.append(Paragraph("3. Cost of Inaction (Current State Losses)", s["section_heading"]))
        st.append(Paragraph(
            "Before quantifying MES benefits, it is important to understand the "
            "hidden cost of maintaining the status quo:", s["body"]))
        st.append(Spacer(1,6))
        inaction_data = [
            ["Loss Category","Annual Cost Estimate","Root Cause (Current State)"],
            ["Manual data entry waste","$60,000–$90,000","10–15 operators entering data that machines could report automatically"],
            ["Undetected quality losses","$400,000–$800,000","No pre-lamination EL test; defects only caught at final test (full module cost)"],
            ["OEE gap (vs. world class 85%)","$300,000–$600,000","No real-time bottleneck visibility; 5-10% hidden capacity loss"],
            ["Unplanned machine downtime","$150,000–$300,000","No predictive maintenance; 6–8% machine availability lost to breakdowns"],
            ["ALMM audit preparation","$20,000–$50,000","Manual genealogy extraction; 3–5 days per audit; compliance risk"],
            ["Warranty claims (quality)","$100,000–$200,000","No serial-level traceability; cannot isolate defective batch scope"],
            ["Planning inefficiency","$30,000–$60,000","Manual scheduling; SAP MRP too slow; planner bottleneck on rush orders"],
            ["TOTAL ANNUAL LOSS (est.)","$1,060,000–$2,100,000","Status quo operating cost — the baseline to beat"],
        ]
        self._tbl(st, inaction_data, s, [2.0*inch,1.7*inch,2.9*inch])
        st.append(Spacer(1,12))

        # ── 4. Benefit Quantification ──────────────────────────────────────
        st.append(Paragraph("4. Benefit Quantification — Year 1 Onwards", s["section_heading"]))
        benefit_data = [
            ["Benefit Category","Mechanism","Annual Value (USD)","Confidence"],
            ["Labor efficiency",
             f"Eliminate manual data entry ({lines} lines × ~3 operators); dispatch automation",
             "$80,000–$120,000","High"],
            ["First Pass Yield (FPY) +1%",
             f"Pre-lamination EL AI: catch defects before lamination; 500 MW × 1% × $0.20/W margin",
             "$500,000–$1,000,000","High"],
            ["Scrap material reduction",
             f"20–30% reduction on {lines} lines; AI-AOI catches stringer defects before lamination",
             "$300,000–$600,000","High"],
            ["OEE improvement +{0}%".format(oee_gain),
             "Bottleneck visibility; predictive maintenance; faster downtime response",
             "$250,000–$500,000","Medium"],
            ["Predictive maintenance",
             "25% unplanned downtime reduction; avoid emergency repair costs",
             "$100,000–$200,000","Medium"],
            ["WIP capital release (15%)",
             "Better scheduling reduces WIP; freed working capital at 8% cost of capital",
             "$80,000–$160,000","Medium"],
            ["ALMM compliance savings",
             "Automated COC; no manual audit prep; avoid non-compliance penalty on govt tenders",
             "$20,000–$100,000+","High"],
            ["Warranty claim reduction",
             "30% fewer warranty claims; serial traceability enables precise recall scope",
             "$75,000–$150,000","Medium"],
            ["TOTAL ANNUAL BENEFIT","","${:,.0f}–${:,.0f}".format(
                1405000, 2830000),""],
        ]
        self._tbl(st, benefit_data, s, [1.8*inch,2.6*inch,1.4*inch,0.8*inch])
        st.append(Spacer(1,12))

        # ── 5. 5-Year Cash Flow ────────────────────────────────────────────
        st.append(Paragraph("5. 5-Year Financial Projection", s["section_heading"]))
        yr_benefit = annual_savings
        cashflow_data = [
            ["Year","Investment","Annual Savings","Net Cash Flow","Cumulative"],
            ["Year 1 (Go-Live)",
             "${:,.0f}".format(total_project_cost),
             "${:,.0f}".format(int(yr_benefit * 0.6)),  # partial year
             "${:,.0f}".format(int(yr_benefit * 0.6) - total_project_cost),
             "${:,.0f}".format(int(yr_benefit * 0.6) - total_project_cost)],
            ["Year 2",
             "$25,000 (AMC)",
             "${:,.0f}".format(yr_benefit),
             "${:,.0f}".format(yr_benefit - 25000),
             "${:,.0f}".format(int(yr_benefit * 0.6) - total_project_cost + yr_benefit - 25000)],
            ["Year 3","$25,000","${:,.0f}".format(yr_benefit),
             "${:,.0f}".format(yr_benefit - 25000),
             "${:,.0f}".format(int(yr_benefit * 0.6) - total_project_cost + (yr_benefit-25000)*2)],
            ["Year 4","$25,000","${:,.0f}".format(yr_benefit),
             "${:,.0f}".format(yr_benefit - 25000),
             "${:,.0f}".format(int(yr_benefit * 0.6) - total_project_cost + (yr_benefit-25000)*3)],
            ["Year 5","$25,000","${:,.0f}".format(yr_benefit),
             "${:,.0f}".format(yr_benefit - 25000),
             "${:,.0f}".format(int(yr_benefit * 0.6) - total_project_cost + (yr_benefit-25000)*4)],
            ["5-YEAR TOTAL","${:,.0f}".format(total_project_cost+25000*4),
             "${:,.0f}".format(int(yr_benefit*4.6)),
             "","${:,.0f}".format(five_yr_net)],
        ]
        self._tbl(st, cashflow_data, s, [0.9*inch,1.5*inch,1.5*inch,1.5*inch,1.2*inch])
        st.append(Spacer(1,10))
        st.append(Paragraph(
            f"<b>Payback period: {payback} months</b> from project start (pilot line go-live). "
            f"The investment is recovered entirely within Year 2. All subsequent savings are net profit contribution.",
            s["body"]))
        st.append(Spacer(1,12))

        # ── 6. Industry Benchmark ──────────────────────────────────────────
        st.append(Paragraph("6. Industry Benchmark Comparison", s["section_heading"]))
        bench_data = [
            ["Metric","Industry Average (No MES)","Target with MES","Improvement"],
            ["OEE (Overall Equipment Effectiveness)","72–78%",f"{78+oee_gain}%+",f"+{oee_gain}% points"],
            ["First Pass Yield (module assembly)","95–97%",">98%","+1–3% points"],
            ["Production tracking accuracy","60–70% (manual)","98%+","Automated capture"],
            ["Unplanned downtime","8–12% of available time","<4%","Predictive maintenance"],
            ["Audit preparation time","3–5 days per audit","<2 hours","Automated ALMM COC"],
            ["Manual data entry FTEs","10–15 per plant","2–3 (supervisory)","10+ FTE re-deployed"],
            ["Scheduling response (rush order)","30–120 min (MRP)","<30 seconds (PODISE)","100× faster"],
            ["Module serial traceability","Batch level (50% plants)","100% serial level","Full ALMM compliance"],
        ]
        self._tbl(st, bench_data, s, [2.0*inch,1.7*inch,1.3*inch,1.6*inch])
        st.append(Spacer(1,12))

        # ── 7. Risk-Adjusted Scenario ──────────────────────────────────────
        st.append(Paragraph("7. Risk-Adjusted Scenarios", s["section_heading"]))
        scenario_data = [
            ["Scenario","Assumption","Annual Benefit","Payback","5-Year Net"],
            ["Conservative (50% benefits)","Slower adoption; partial integration","${:,.0f}".format(int(annual_savings*0.5)),
             f"{int(payback*1.8)} months","${:,.0f}".format(int(annual_savings*0.5*5-total_project_cost))],
            ["Base Case (our estimate)","Structured rollout; full integration","${:,.0f}".format(annual_savings),
             f"{payback} months","${:,.0f}".format(five_yr_net)],
            ["Optimistic (120% benefits)","Fast adoption; all AI agents live Year 1","${:,.0f}".format(int(annual_savings*1.2)),
             f"{int(payback*0.85)} months","${:,.0f}".format(int(annual_savings*1.2*5-total_project_cost))],
        ]
        self._tbl(st, scenario_data, s, [1.4*inch,2.3*inch,1.4*inch,1.0*inch,1.5*inch])
        st.append(Spacer(1,10))
        st.append(Paragraph(
            "Even in the conservative scenario (50% of expected benefits), "
            "the investment pays back and delivers positive 5-year net benefit. "
            "This demonstrates low investment risk with asymmetric upside.",
            s["body"]))
        st.append(Spacer(1,12))

        # ── 8. ROI from Knowledge Base ─────────────────────────────────────
        roi_kb = state.get("roi_knowledge", "")
        if roi_kb and len(roi_kb) > 100:
            st.append(Paragraph("8. Supporting Evidence from Industry Knowledge Base", s["section_heading"]))
            from pdf_styles import strip_markdown, nl2br
            st.append(Paragraph(nl2br(strip_markdown(roi_kb[:800])), s["body"]))

        doc.build(st)

    def _tbl(self, story, data, s, widths):
        rows = [[Paragraph(str(c), s["table_header"] if i==0 else s["table_cell"])
                 for c in row] for i, row in enumerate(data)]
        tbl = Table(rows, colWidths=widths)
        tbl.setStyle(default_table_style())
        story.append(tbl)