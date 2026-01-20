from __future__ import annotations

from pydantic import BaseModel, Field


class CurrentWeatherInput(BaseModel):
    city: str = Field(..., description="City name to look up")


class ForecastWeatherInput(BaseModel):
    city: str = Field(..., description="City name to look up")
    days: int = Field(3, ge=1, le=10, description="Number of days for forecast")
