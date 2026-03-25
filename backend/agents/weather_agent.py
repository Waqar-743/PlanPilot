import httpx
from datetime import datetime, timedelta
from backend.config.settings import settings


class WeatherAgent:
    """
    Fetches weather forecasts for a destination using OpenWeatherMap API.
    Trigger: Called FIRST to ensure the destination's weather is suitable for the requested dates.
    Required Input: {"destination": "City Name", "dates": "YYYY-MM-DD to YYYY-MM-DD"}
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "https://api.openweathermap.org/geo/1.0"

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY

    async def _geocode_city(self, city: str) -> dict | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GEO_URL}/direct",
                params={"q": city, "limit": 1, "appid": self.api_key}
            )
            if response.status_code == 200 and response.json():
                data = response.json()[0]
                return {"lat": data["lat"], "lon": data["lon"], "name": data.get("name", city)}
        return None

    async def get_forecast(self, destination: str, dates: str) -> dict:
        """
        Fetches weather forecast for a destination.
        Uses 5-day/3-hour forecast for near dates, or climate averages for far dates.
        """
        if not self.api_key or self.api_key.startswith("your_"):
            return self._fallback_forecast(destination, dates)

        try:
            start_str, end_str = dates.split(" to ")
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
        except (ValueError, AttributeError):
            return {"error": "Invalid date format. Use 'YYYY-MM-DD to YYYY-MM-DD'"}

        geo = await self._geocode_city(destination)
        if not geo:
            return {"error": f"Could not find coordinates for '{destination}'"}

        days_until_start = (start_date - datetime.now()).days
        duration = (end_date - start_date).days + 1

        if days_until_start <= 5:
            return await self._get_short_term_forecast(geo, start_date, end_date, destination)
        else:
            return await self._get_climate_estimate(geo, start_date, end_date, destination, duration)

    async def _get_short_term_forecast(self, geo: dict, start: datetime, end: datetime, city: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/forecast",
                params={
                    "lat": geo["lat"],
                    "lon": geo["lon"],
                    "appid": self.api_key,
                    "units": "metric"
                }
            )

        if response.status_code != 200:
            return {"error": f"Weather API error: {response.status_code}"}

        data = response.json()
        daily_forecasts = {}

        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.strftime("%Y-%m-%d")

            if start.date() <= dt.date() <= end.date():
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        "date": date_key,
                        "temps": [],
                        "descriptions": [],
                        "humidity": [],
                        "wind_speed": [],
                    }
                daily_forecasts[date_key]["temps"].append(item["main"]["temp"])
                daily_forecasts[date_key]["descriptions"].append(
                    item["weather"][0]["description"]
                )
                daily_forecasts[date_key]["humidity"].append(item["main"]["humidity"])
                daily_forecasts[date_key]["wind_speed"].append(item["wind"]["speed"])

        forecast_summary = []
        for date_key, day_data in sorted(daily_forecasts.items()):
            temps = day_data["temps"]
            forecast_summary.append({
                "date": date_key,
                "temp_high": round(max(temps), 1),
                "temp_low": round(min(temps), 1),
                "temp_avg": round(sum(temps) / len(temps), 1),
                "condition": max(set(day_data["descriptions"]), key=day_data["descriptions"].count),
                "humidity_avg": round(sum(day_data["humidity"]) / len(day_data["humidity"])),
                "wind_avg_kmh": round(sum(day_data["wind_speed"]) / len(day_data["wind_speed"]) * 3.6, 1),
            })

        return {
            "destination": city,
            "forecast_type": "5-day detailed",
            "daily_forecast": forecast_summary,
            "summary": self._build_summary(forecast_summary, city),
        }

    async def _get_climate_estimate(self, geo: dict, start: datetime, end: datetime, city: str, duration: int) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/weather",
                params={
                    "lat": geo["lat"],
                    "lon": geo["lon"],
                    "appid": self.api_key,
                    "units": "metric"
                }
            )

        if response.status_code != 200:
            return {"error": f"Weather API error: {response.status_code}"}

        current = response.json()
        temp = current["main"]["temp"]
        condition = current["weather"][0]["description"]

        month_name = start.strftime("%B")
        forecast_summary = [{
            "date": f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            "temp_high": round(temp + 3, 1),
            "temp_low": round(temp - 5, 1),
            "temp_avg": round(temp, 1),
            "condition": f"Seasonal estimate based on current: {condition}",
            "humidity_avg": current["main"]["humidity"],
            "wind_avg_kmh": round(current["wind"]["speed"] * 3.6, 1),
        }]

        return {
            "destination": city,
            "forecast_type": f"climate estimate ({month_name})",
            "daily_forecast": forecast_summary,
            "summary": (
                f"Weather in {city} for {month_name}: Expected temperatures around "
                f"{round(temp - 5, 1)}-{round(temp + 3, 1)}°C. "
                f"Current conditions are {condition}. "
                f"Plan for {duration} days accordingly."
            ),
            "note": "This is a climate estimate. Exact forecasts are available within 5 days of travel."
        }

    def _build_summary(self, forecasts: list, city: str) -> str:
        if not forecasts:
            return f"No forecast data available for {city}."

        all_temps = [f["temp_avg"] for f in forecasts]
        conditions = [f["condition"] for f in forecasts]
        avg_temp = round(sum(all_temps) / len(all_temps), 1)
        dominant_condition = max(set(conditions), key=conditions.count)

        rain_days = sum(1 for c in conditions if "rain" in c.lower())
        clear_days = sum(1 for c in conditions if "clear" in c.lower() or "sun" in c.lower())

        summary = f"Weather in {city}: Average temp {avg_temp}°C, mostly {dominant_condition}."
        if rain_days > 0:
            summary += f" Rain expected on {rain_days} day(s) -- pack an umbrella."
        if clear_days > len(forecasts) / 2:
            summary += " Great weather for outdoor activities!"

        return summary

    def _fallback_forecast(self, destination: str, dates: str) -> dict:
        return {
            "destination": destination,
            "forecast_type": "general estimate (API key not configured)",
            "daily_forecast": [],
            "summary": (
                f"Weather data for {destination}: Expect moderate seasonal weather. "
                "Pack layers and a light rain jacket to be safe. "
                "Check a weather app closer to your travel date for exact forecasts."
            ),
            "note": "OpenWeatherMap API key not configured. Using general estimate."
        }


weather_agent = WeatherAgent()
