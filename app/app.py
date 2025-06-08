from flask import Flask, render_template,request, jsonify
import requests
import json
import random
from predictions import get_predictions

app = Flask(__name__)

API_KEY = '-'
CITY = 'Bengaluru'
URL = f'http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather')
def get_weather():
    city = "Bengaluru"
    lat = 12.9716
    lon = 77.5946

    # Current weather
    weather_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    temperature = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    windspeed = weather_data['wind']['speed']

    # Air quality
    aqi_url = f'https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}'
    aqi_response = requests.get(aqi_url)
    aqi_data = aqi_response.json()

    aqi_value = aqi_data['list'][0]['main']['aqi']
    aqi_status = {
        1: 'Good',
        2: 'Fair',
        3: 'Moderate',
        4: 'Poor',
        5: 'Very Poor'
    }.get(aqi_value, 'Unknown')
    
     # UV index
    uv_url = f'https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={API_KEY}'
    uv_response = requests.get(uv_url)
    uv_data = uv_response.json()

    uv_index = uv_data['value']

    # Sunscreen advice based on UV index
    if uv_index == 0:
        sunscreen_advice = "No"
    elif 1 <= uv_index <= 2:
        sunscreen_advice = "Optional"
    elif 3 <= uv_index <= 10:
        sunscreen_advice = "Yes"
    else:
        sunscreen_advice = "Compuslory"

    # Load song suggestions
    with open('D:/skicast_project/data/songs.json') as f:
        song_data = json.load(f)
        song_suggestion = {"title": "No suggestion", "artist": "--"}
        
        for temp_range in song_data:
            lower, upper = map(int, temp_range.split('-'))
            
            if lower <= temperature <= upper:
                full_song = random.choice(song_data[temp_range]).strip()

                if ' - ' in full_song:
                    title, artist = map(str.strip, full_song.split(' - ', 1))
                    song_suggestion = {"title": title, "artist": artist}
                else:
                    song_suggestion = {"title": full_song, "artist": "--"}
                break
        
        with open('D:/skicast_project/data/quotes.json', encoding='utf-8') as f:
            quote_data = json.load(f)
            quote = ''
            
            for temp_range in quote_data:  
                lower, upper = map(int, temp_range.split('-'))
                if lower <= temperature <= upper:
                    quote = random.choice(quote_data[temp_range])
                    break


        result = {
            'temperature': temperature,
            'humidity': humidity,
            'windspeed': windspeed,
            'aqi': aqi_value,
            'aqi_status': aqi_status,
            'uv_index': uv_index,
            'sunscreen': sunscreen_advice,
            'song': song_suggestion,
            'quote':quote
        }
        
        return jsonify(result)

@app.route('/forecast')
def forecast():
    forecast_data = get_predictions()
    return jsonify(forecast_data)

if __name__ == "__main__":
    app.run(debug=True)
