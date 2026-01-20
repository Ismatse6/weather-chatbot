from __future__ import annotations

from typing import Any, Dict

import requests
from decouple import config
from langchain_core.tools import StructuredTool

from core.models import CurrentWeatherInput, ForecastWeatherInput

WEATHER_API_BASE = "http://api.weatherapi.com/v1"
DEFAULT_TIMEOUT_S = 10


def _get_api_key() -> str | None:
    return config("WEATHER_API_KEY", default=None)


def _request_weather(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    api_key = _get_api_key()
    if not api_key:
        return {"error": "WEATHER_API_KEY is not set in .env"}

    full_params = dict(params)
    full_params["key"] = api_key
    full_params["aqi"] = "yes"
    url = f"{WEATHER_API_BASE}/{endpoint}.json"

    try:
        response = requests.get(url, params=full_params, timeout=DEFAULT_TIMEOUT_S)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return {"error": f"Weather API request failed: {exc}"}
    except ValueError:
        return {"error": "Weather API returned invalid JSON"}

    if isinstance(data, dict) and "error" in data:
        err = data.get("error", {})
        message = err.get("message") if isinstance(err, dict) else str(err)
        return {"error": message or "Weather API error"}

    return data


def current_weather(city: str) -> Dict[str, Any]:
    data = _request_weather("current", {"q": city})
    if "error" in data:
        return data

    current = data.get("current", {})
    location = data.get("location", {})

    return {
        "location": {
            "name": location.get("name"),
            "region": location.get("region"),
            "country": location.get("country"),
        },
        "temperature_c": current.get("temp_c"),
        "humidity": current.get("humidity"),
        "wind_kph": current.get("wind_kph"),
        "air_quality": current.get("air_quality"),
    }


def forecast_weather(city: str, days: int = 3) -> Dict[str, Any]:
    safe_days = max(1, min(int(days), 10))
    data = _request_weather("forecast", {"q": city, "days": safe_days})
    if "error" in data:
        return data

    location = data.get("location", {})
    forecast_days = []
    for item in data.get("forecast", {}).get("forecastday", []):
        day = item.get("day", {})
        forecast_days.append(
            {
                "date": item.get("date"),
                "temperature_c": day.get("avgtemp_c"),
                "humidity": day.get("avghumidity"),
                "wind_kph": day.get("maxwind_kph"),
                "air_quality": day.get("air_quality"),
            }
        )

    return {
        "location": {
            "name": location.get("name"),
            "region": location.get("region"),
            "country": location.get("country"),
        },
        "days": safe_days,
        "forecast": forecast_days,
    }


current_weather_tool = StructuredTool.from_function(
    current_weather,
    name="current_weather",
    description=(
        "Get current weather and air quality for a city. "
        "Input: city name. Output includes temperature_c, humidity, wind_kph, air_quality."
    ),
    args_schema=CurrentWeatherInput,
)

forecast_weather_tool = StructuredTool.from_function(
    forecast_weather,
    name="forecast_weather",
    description=(
        "Get forecast weather and air quality for a city over a number of days. "
        "Input: city name and days (default 3). Output includes temperature_c, humidity, "
        "wind_kph, air_quality for each day."
    ),
    args_schema=ForecastWeatherInput,
)

WEATHER_TOOLS = [current_weather_tool, forecast_weather_tool]
