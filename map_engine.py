import os
import urllib.request
import urllib.error

def get_map_image(lat, lon, zoom, api_key):
    """
    Fetches a satellite image from Mapbox using built-in Python libraries. 
    Zero pip installations required.
    """
    # 1. Create the cache folder automatically if it doesn't exist
    if not os.path.exists("map_cache"):
        os.makedirs("map_cache")
        print("📁 Created 'map_cache' directory.")
        
    # 2. Define the exact filename based on the coordinates
    filename = f"map_cache/map_{lat}_{lon}_{zoom}.png"
    
    # 3. The Caching Layer: Check if we already have it
    if os.path.exists(filename):
        print(f"✅ Image found in cache! Loading local file: {filename}")
        return filename
        
    # 4. The Scraper: If not in cache, download it from Mapbox
    print(f"⬇️ Image not found in cache. Downloading from Mapbox...")
    
    url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},{zoom},0/600x600?access_token={api_key}"
    
    # 5. Save the image using built-in urllib
    try:
        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"✅ Success! Image saved to: {filename}")
        return filename
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error downloading image: {e.code}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ URL/Network Error: {e.reason}")
        return None

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # PASTE YOUR MAPBOX KEY HERE (It should start with 'pk.')
    MY_API_KEY = "pk.eyJ1IjoicmFodWwtMjM4OSIsImEiOiJjbXFjaG9xejkwMHBiMnNyNHcxajVlYnByIn0.lqQuRKDL5s4DlSBvhH0jBQ" 
    
    # Test coordinates (Vishwakarma University area)
    TEST_LAT = 18.4575  
    TEST_LON = 73.8508
    
    # Zoom level (18 is usually good for drone altitudes)
    TEST_ZOOM = 18 
    
    print("🚀 Starting Map Simulation Engine...")
    
    # Run the function
    image_path = get_map_image(TEST_LAT, TEST_LON, TEST_ZOOM, MY_API_KEY)
    
    print("\nTest complete. Check your project folder!")