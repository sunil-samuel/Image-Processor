# -*- coding: utf-8 -*-
"""
@File    :   geopy-lat-lon.py
@Time    :   2025/07/18
@Author  :   Sunil Samuel
@Version :   1.0
@Contact :   sgs@sunilsamuel.com
@Desc    :   Given a latitude and longitude coordinates, use geopy module
             to convert it to an address.
"""

from geopy.geocoders import Nominatim

# 1. Initialize the geolocator
#    The user_agent can be any name you choose for your application.
geolocator = Nominatim(user_agent="location_finder_app")

# 2. Provide the latitude and longitude
#    Example: Coordinates for the Eiffel Tower
latitude = 48.8584
longitude = 2.2945

coordinates = f"{latitude}, {longitude}"

# 3. Perform the reverse geocoding
try:
    location = geolocator.reverse(coordinates)

    if location:
        print(location.address)
    else:
        print("No address found for the given coordinates.")

except Exception as e:
    print(f"An error occurred: {e}")
