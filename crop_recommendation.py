"""Rule-based crop recommendations for common Indian growing conditions."""

from __future__ import annotations


SEASON_CROPS = {
    "kharif": [
        ("Rice", "Clay or loam soil with reliable standing water."),
        ("Maize", "Well-drained loam with moderate irrigation."),
        ("Soybean", "Well-drained black or loam soil; avoid waterlogging."),
        ("Pearl millet", "Sandy or light soil; suited to lower rainfall."),
    ],
    "rabi": [
        ("Wheat", "Fertile, well-drained loam with timely irrigation."),
        ("Chickpea", "Well-drained loam or black soil; needs limited water."),
        ("Mustard", "Loam or sandy loam with good drainage."),
        ("Barley", "Light to medium soil; more tolerant of salinity than wheat."),
    ],
    "zaid": [
        ("Watermelon", "Sandy loam, warm weather, and regular irrigation."),
        ("Cucumber", "Well-drained fertile soil with steady moisture."),
        ("Mung bean", "Light loam soil; short-duration crop with modest water needs."),
        ("Fodder maize", "Fertile soil and frequent irrigation."),
    ],
}


def recommend_crops(season: str, soil_type: str, water_level: str) -> list[dict]:
    """Return up to three suitable crops with practical growing notes."""
    season = season.lower().strip()
    soil_type = soil_type.lower().strip()
    water_level = water_level.lower().strip()
    if season not in SEASON_CROPS:
        raise ValueError("Select a growing season to get crop recommendations.")

    crops = list(SEASON_CROPS[season])
    if water_level == "low":
        crops = [crop for crop in crops if crop[0] not in {"Rice", "Watermelon", "Cucumber", "Fodder maize", "Wheat"}] or crops
    elif water_level == "high" and season == "kharif":
        crops.sort(key=lambda crop: crop[0] != "Rice")

    return [
        {
            "name": name,
            "note": note,
            "fit": f"Recommended for {season.title()} with {soil_type} soil and {water_level} water availability.",
        }
        for name, note in crops[:3]
    ]
