"""
agents/solar_process_sequence_agent.py
---------------------------------------
Failsafe sequence diagram for solar manufacturing.
Uses only simple actors/participants and one‑line messages.
"""
from diagram_utils import render_plantuml

_SEQUENCE_DIAGRAM = """@startuml
actor Supplier
participant "Ingot & Wafer" as IW
participant "Cell Fab" as CF
participant "Module Assembly" as MA
participant "Quality Assurance" as QA
participant "Packaging & Shipping" as PS

Supplier -> IW : Polysilicon
IW -> IW : Ingot Production (Czochralski)
IW -> IW : Wafer Slicing (160-200 um)
IW -> CF : Wafers
CF -> CF : Texturisation & Doping
CF -> CF : ARC Coating (SiN)
CF -> CF : Contact Formation
CF -> MA : Sorted cells
MA -> MA : Cell Sorting & Testing
MA -> MA : Stringing + Soldering
MA -> MA : Junction Box & Frame
MA -> QA : Laminated panel
QA -> QA : Flash, EL, Hi-Pot Testing
QA -> PS : Approved panel
PS -> PS : Packaging & Shipping
PS -> Customer : Finished module delivery
@enduml"""


class SolarProcessSequenceAgent:
    def run(self, state: dict) -> dict:
        try:
            path = render_plantuml(
                _SEQUENCE_DIAGRAM,
                filename="solar_manufacturing_sequence.png"
            )
            state["solar_sequence_diagram_path"] = path
            print("   ✓ Solar manufacturing sequence diagram generated")
        except Exception as exc:
            print(f"   ⚠️  Solar process sequence diagram failed: {exc}")
            state["solar_sequence_diagram_path"] = None
        return state