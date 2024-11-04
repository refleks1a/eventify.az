from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from datetime import datetime


# Vars
latitude_regex = r"^(\+|-)?(90(\.0+)?|[1-8]?\d(\.\d+)?)$"
longitude_regex = r"^(\+|-)?(180(\.0+)?|((1[0-7]\d)|(\d{1,2}))(\.\d+)?)$"
time_regex = r"^(?:[01]?[0-9]|2[0-3]):[0-5]?[0-9](?::[0-5]?[0-9])?$"
link_regex = r"^https:\/\/(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(\/[^\s]*)?$"

event_types = ["theatre", "concert", "exhibition", "book_fare",
        "seminar","festival","dance"]

venue_types = ["museum", "theatre", "library", "cinema",
        "comedy_club","monument","cultural_space"]

# Functions

def get_country_from_coordinates(latitude, longitude):
    geolocator = Nominatim(user_agent="geoapiExercises")
    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        address = location.raw['address']

        country = address.get('country')
        city = address.get('city') or address.get('town') or address.get('village')

        return country, city
    except GeocoderTimedOut:
        return None
    

def is_past_date(input_date_str):
    date_format = "%Y-%m-%d %H:%M:%S"
    try:
        input_date = datetime.strptime(input_date_str, date_format)
    except ValueError:
        return True
    
    # Get the current date and time
    current_date = datetime.now()
    
    # Compare dates
    if input_date >= current_date:
        return False
    else:
        return True
