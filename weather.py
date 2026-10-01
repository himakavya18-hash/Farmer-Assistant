"""Weather lookups for the crop advisor dashboard."""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Fog", "🌫️"), 48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌦️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"), 81: ("Heavy showers", "🌧️"), 82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
}


def _get_json(url: str, params: dict) -> dict:
    """Fetch JSON with a short timeout."""
    with urlopen(f"{url}?{urlencode(params)}", timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather(location: str) -> dict:
    """Return current conditions and a three-day forecast for *location*."""
    location = location.strip()
    if not location:
        raise ValueError("Enter a town, city, or village to get the weather.")
    try:
        places = _get_json(GEOCODING_URL, {"name": location, "count": 1, "language": "en", "format": "json"})
        result = (places.get("results") or [None])[0]
        if not result:
            raise ValueError(f"No location found for '{location}'. Try a nearby city or add the state.")
        forecast = _get_json(FORECAST_URL, {
            "latitude": result["latitude"], "longitude": result["longitude"],
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
            "timezone": "auto", "forecast_days": 3,
        })
    except ValueError:
        raise
    except Exception as error:
        raise ValueError("Weather data is temporarily unavailable. Please try again shortly.") from error

    current, daily = forecast["current"], forecast["daily"]
    description, icon = WEATHER_CODES.get(current["weather_code"], ("Unknown conditions", "🌡️"))
    place_name = ", ".join(filter(None, [result.get("name"), result.get("admin1"), result.get("country")]))
    return {
        "location": place_name, "updated_at": current.get("time"),
        "current": {"temperature": round(current["temperature_2m"]), "humidity": current["relative_humidity_2m"], "rain": current["precipitation"], "wind": round(current["wind_speed_10m"]), "description": description, "icon": icon},
        "forecast": [{
            "date": daily["time"][i], "description": WEATHER_CODES.get(daily["weather_code"][i], ("Unknown conditions", "🌡️"))[0],
            "icon": WEATHER_CODES.get(daily["weather_code"][i], ("Unknown conditions", "🌡️"))[1],
            "high": round(daily["temperature_2m_max"][i]), "low": round(daily["temperature_2m_min"][i]),
            "rain_chance": daily["precipitation_probability_max"][i], "rain_total": daily["precipitation_sum"][i],
        } for i in range(len(daily["time"]))],
    }
