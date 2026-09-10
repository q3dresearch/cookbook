"""One definition of what a project IS, shared by every chart in this recipe.

Keyed on FUEL, never on turbine type. The two are separate columns in CAISO's
report and do not follow from each other: its "Steam Turbine" category is 99
solar-thermal, 35 geothermal, 15 biofuel and only 13 natural gas. Keying on type
put 149 non-gas plants into a gas family.

This lives in one file because it did not, and two charts in this recipe ended up
describing gas differently on the same page — one showing four turbine types as
separate technologies, the other showing 248 projects across five types as one
fuel. A reader comparing them would have concluded the data disagreed with itself.
"""
from __future__ import annotations

FAMILY = {
    "solar": "Solar", "photovoltaic": "Solar",
    "wind": "Wind", "wind turbine": "Wind",
    "battery": "Storage", "battery storage": "Storage", "storage": "Storage",
    "pumped-storage hydro": "Storage",
    "natural gas": "Gas", "gas": "Gas",
    "geothermal": "Geothermal",
    "hybrid": "Hybrid",
    "biofuel": "Biomass", "biomass": "Biomass",
    "water": "Hydro", "hydro": "Hydro",
    "nuclear": "Nuclear",
}

HUE = {"Solar": "#b5651d", "Wind": "#3f7d3a", "Storage": "#2361b0",
       "Gas": "#7a4fa3", "Geothermal": "#a8324a", "Hybrid": "#1f7a86",
       "Biomass": "#6b7a1f", "Hydro": "#1f5f8b", "Nuclear": "#8a6d1f"}


def family_of(row) -> str | None:
    """Fuel first, turbine type only as a fallback for rows with no fuel."""
    return (FAMILY.get((row.get("fuel") or "").strip().lower())
            or FAMILY.get((row.get("technology") or "").strip().lower()))
