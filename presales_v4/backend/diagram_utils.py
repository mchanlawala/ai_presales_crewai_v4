"""
diagram_utils.py
----------------
Send PlantUML source to the free Kroki.io API and save the PNG.
Falls back gracefully if the API is unreachable.
"""
import os
import requests


KROKI_URL = "https://kroki.io/plantuml/png"


def render_plantuml(
    plantuml_code: str,
    output_dir: str = "output",
    filename: str = "architecture_diagram.png",
) -> str:
    """
    Render *plantuml_code* to a PNG file and return its path.
    Raises RuntimeError on failure so callers can catch and skip the diagram.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    resp = requests.post(
        KROKI_URL,
        json={"diagram_source": plantuml_code},
        timeout=30,
    )

    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    else:
        raise RuntimeError(
            f"Kroki API returned {resp.status_code}: {resp.text[:200]}"
        )
