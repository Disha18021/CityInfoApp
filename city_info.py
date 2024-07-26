import streamlit as st
import requests
from datetime import datetime
import pytz
from langchain import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# Constants for API keys and endpoints
WEATHER_API_KEY = '8672e9b9543f8d1ad5d4edf91f56c3b3'
WEATHER_ENDPOINT = 'http://api.openweathermap.org/data/2.5/weather'
NOMINATIM_ENDPOINT = 'https://nominatim.openstreetmap.org/search'
OVERPASS_ENDPOINT = 'https://overpass-api.de/api/interpreter'

# Define a function to fetch weather data using LangChain
def fetch_weather_data(city_name):
    prompt = f"Get the weather data for {city_name} using the OpenWeatherMap API."
    llm = OpenAI(temperature=0.7)
    template = PromptTemplate(input_variables=["city_name"], template=prompt)
    chain = LLMChain(llm=llm, prompt=template)
    
    result = chain.run(city_name=city_name)
    
    return result

# Function to get current weather, timezone, and city info
def get_city_info(city_name):
    params = {
        'q': city_name,
        'appid': WEATHER_API_KEY,
        'units': 'metric'  # or 'imperial' for Fahrenheit
    }
    
    response = requests.get(WEATHER_ENDPOINT, params=params)
    data = response.json()
    
    if response.status_code != 200 or 'main' not in data:
        return None, None, None, None, None, None
    
    temp = data['main']['temp']
    weather_description = data['weather'][0]['description']
    timezone_offset = data['timezone']
    
    # Calculate the timezone from the offset in seconds
    local_tz = pytz.FixedOffset(int(timezone_offset / 60))
    current_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

    # Get city coordinates
    lat = data['coord']['lat']
    lon = data['coord']['lon']
    
    # Fetch nearby places
    nearby_restaurants = get_nearby_places(lat, lon, 'restaurant')
    nearby_hotels = get_nearby_places(lat, lon, 'hotel')
    nearby_street_food = get_nearby_places(lat, lon, 'fast_food')
    
    return temp, weather_description, current_time, nearby_restaurants, nearby_hotels, nearby_street_food

# Function to get nearby places from Overpass API
def get_nearby_places(lat, lon, place_type):
    type_mapping = {
        'restaurant': 'node["amenity"="restaurant"]',
        'hotel': 'node["tourism"="hotel"]',
        'fast_food': 'node["amenity"="fast_food"]'
    }
    
    query = f"""
    [out:json];
    (
      {type_mapping.get(place_type)}(around:5000,{lat},{lon});
    );
    out body;
    """
    
    response = requests.get(OVERPASS_ENDPOINT, params={'data': query})
    data = response.json()
    
    places = data.get('elements', [])
    
    return [place['tags'].get('name', 'Unnamed') for place in places]

# Streamlit application
def main():
    st.title("City Information Finder")

    city_name = st.text_input("Enter City Name:")
    
    if st.button("Get Info"):
        if not city_name:
            st.write("Please enter a city name.")
        else:
            temp, weather_description, current_time, restaurants, hotels, street_food = get_city_info(city_name)
            if temp is None:
                st.write("City not found or API request failed.")
            else:
                st.write(f"City: {city_name}")
                st.write(f"Current Temperature: {temp}°C")
                st.write(f"Weather: {weather_description}")
                st.write(f"Date and Time: {current_time}")
                st.write("Nearby Restaurants:")
                st.write(", ".join(restaurants))
                st.write("Nearby Hotels:")
                st.write(", ".join(hotels))
                st.write("Nearby Street Food:")
                st.write(", ".join(street_food))

if __name__ == "__main__":
    main()
