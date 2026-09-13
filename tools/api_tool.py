import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_current_temp_from_api(city: str) -> dict:
    """
    Fetch today's current temperature for a city from a real external API
    (Open-Meteo, no API key required).

    Same contract as get_avg_temp_from_db: always returns a dict with
    'success', never raises, so the agent can reason about failures
    (e.g. city not found) instead of crashing.
    """
    try:
        # Step 1: turn city name into lat/lon
        geo_resp = requests.get(GEOCODE_URL, params={"name": city, "count": 1}, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        results = geo_data.get("results")
        if not results:
            return {"success": False, "error": f"Could not geocode city '{city}'"}

        lat = results[0]["latitude"]
        lon = results[0]["longitude"]

        # Step 2: fetch current weather for those coordinates
        weather_resp = requests.get(
            WEATHER_URL,
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=10,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        current = weather_data.get("current_weather")
        if current is None:
            return {"success": False, "error": "API response missing current_weather"}

        return {
            "success": True,
            "city": city,
            "temp_celsius": current["temperature"],
        }

    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # quick manual test — run this file directly before wiring into the agent
    print(get_current_temp_from_api("Ahmedabad"))
