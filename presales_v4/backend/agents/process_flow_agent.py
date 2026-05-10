"""
agents/process_flow_agent.py
-----------------------------
Failsafe AS‑IS and TO‑BE activity diagrams.
Always valid – no notes, no complex skinparams.
"""
from diagram_utils import render_plantuml

_ASIS = """@startuml
start
:Raw Material Arrival;
:Visual Inspection;
:Cell Stringing;
:Lamination;
:Framing;
:Manual Flash Test;
:Packaging & Labelling;
:Shipment;
stop
@enduml"""

_TOBE = """@startuml
start
:Raw Material Arrival;
:MES auto-creates inbound lot;
:Automated Quality Inspection;
:Cell Stringing (real-time data to MES);
:Lamination (Quality alerts);
:Framing;
:Automated Flash Test + EL Imaging;
:MES updates WIP & triggers packaging;
:Packaging & Serialisation (barcode by MES);
:SAP ERP updated (production confirmation);
:Shipment + Digital Certificate;
stop
@enduml"""


class ProcessFlowAgent:
    def run(self, state: dict) -> dict:
        for key, code, fname in (
                ("asis_diagram_path", _ASIS, "asis_process.png"),
                ("tobe_diagram_path", _TOBE, "tobe_process.png"),
        ):
            try:
                path = render_plantuml(code, filename=fname)
                state[key] = path
                print(f"   ✓ {fname} generated")
            except Exception as exc:
                print(f"   ⚠️  Could not render {fname}: {exc}")
                state[key] = None
        return state