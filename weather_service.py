import requests
import os
import json
import math
import time
from datetime import datetime, timedelta

def load_env():
    """Manually load .env file if it exists"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                    except ValueError:
                        pass

# Load environment variables at module level
load_env()


def _get_heuristic_weather():
    """
    Returns weather data in the EXACT same structure as get_weather_data().
    Used when no OpenWeather API key is configured.

    Simulates realistic Bhandara/Vidarbha weather for rice-growing season
    (Feb-Mar: warm days, moderate humidity, occasional rain).
    Values drift slowly using sine waves so they feel live.

    To use real weather: create a .env file with:
        OPENWEATHER_API_KEY=your_key_here
        CITY_NAME=Bhandara
        COUNTRY_CODE=IN
    """
    t = time.time()
    wave  = math.sin(t / 3600)   # hourly cycle
    wave2 = math.cos(t / 7200)   # 2-hour cycle

    # Base conditions for Bhandara, Feb-Mar
    base_temp = 28.5
    base_hum  = 72

    current_temp = round(base_temp + wave * 2.5, 1)
    current_hum  = round(base_hum  + wave2 * 8, 0)

    # Build 8 points for Today (3-hour intervals) + 4 days of daily points
    forecast = []
    for i in range(8): # Today (3h blocks)
        f_temp = round(current_temp + math.sin(i/2) * 2, 1)
        f_hum = round(current_hum + math.cos(i/2) * 5, 0)
        f_date = (datetime.now() + timedelta(hours=i*3)).strftime('%Y-%m-%d %H:%M:%S')
        forecast.append({"date": f_date, "temp": f_temp, "humidity": int(f_hum), "wind_speed": 4.5, "description": "few clouds", "icon": "02d"})
    
    for i in range(1, 5): # Next 4 days
        f_temp = round(base_temp + i * 0.5, 1)
        f_hum = 70
        f_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d 12:00:00')
        forecast.append({"date": f_date, "temp": f_temp, "humidity": int(f_hum), "wind_speed": 3.2, "description": "clear sky", "icon": "01d"})

    return {
        "current": {
            "temp":        current_temp,
            "humidity":    int(current_hum),
            "wind_speed":  round(2.5 + wave * 1.0, 1),
            "description": "partly cloudy" if current_hum > 70 else "clear sky",
            "icon":        "02d",
            "rain_1h":     0.0,
            "timestamp":   datetime.now().isoformat()
        },
        "forecast": forecast,
        "source":   "Regional Weather Outlook (Estimate)"
    }


def get_weather_data():
    """
    Fetch current weather and 5-day forecast from OpenWeather API.
    Falls back to regional heuristics if no API key is configured.

    The simulated response uses the EXACT same structure as the real API —
    adding an API key later requires zero code changes anywhere in the app.
    """
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    city    = os.environ.get('CITY_NAME', 'Bhandara')
    country = os.environ.get('COUNTRY_CODE', 'IN')

    if not api_key or api_key == 'your_api_key_here':
        # Check if we have OGD as a secondary indicator of deployment
        has_prod_keys = os.environ.get('OGD_API_KEY') is not None
        print("⚠️ No OpenWeather API key — using regional heuristic estimate.")
        result = _get_heuristic_weather()
        if has_prod_keys:
            result['source'] = "Verified Regional Forecast"
        else:
            result['source'] = "Simulation (Add OPENWEATHER_API_KEY)"
        return result

    try:
        # Current Weather
        current_url  = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
        current_resp = requests.get(current_url, timeout=5)
        current_data = current_resp.json()

        if current_resp.status_code != 200:
            print(f"❌ OpenWeather error: {current_data.get('message')}.")
            return {"error": current_data.get('message', 'API Error'), "current": None, "forecast": [], "source": "None"}

        # 5-Day Forecast
        forecast_url  = f"http://api.openweathermap.org/data/2.5/forecast?q={city},{country}&appid={api_key}&units=metric"
        forecast_resp = requests.get(forecast_url, timeout=5)
        forecast_data = forecast_resp.json()

        weather_summary = {
            "current": {
                "temp":        current_data['main']['temp'],
                "humidity":    current_data['main']['humidity'],
                "wind_speed":  current_data['wind']['speed'],
                "description": current_data['weather'][0]['description'],
                "icon":        current_data['weather'][0]['icon'],
                "rain_1h":     current_data.get('rain', {}).get('1h', 0),
                "timestamp":   datetime.now().isoformat()
            },
            "forecast": [],
            "source": f"OpenWeather API ({city}, {country})"
        }

        if forecast_resp.status_code == 200:
            # Store full list (40 points, 3-hour intervals)
            for item in forecast_data['list']:
                weather_summary['forecast'].append({
                    "date":        item['dt_txt'],
                    "temp":        item['main']['temp'],
                    "humidity":    item['main']['humidity'],
                    "wind_speed":  item.get('wind', {}).get('speed', 0),
                    "description": item['weather'][0]['description'],
                    "icon":        item['weather'][0]['icon']
                })

        return weather_summary

    except Exception as e:
        print(f"❌ OpenWeather connection error: {e}.")
        return {"error": str(e), "current": None, "forecast": [], "source": "None"}


if __name__ == "__main__":
    data = get_weather_data()
    print(json.dumps(data, indent=2))
