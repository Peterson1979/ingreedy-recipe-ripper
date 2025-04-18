import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import traceback
import json
from urllib.parse import urlparse, parse_qs, unquote # Added unquote

# --- Environment Variable Loading ---
from dotenv import load_dotenv
load_dotenv() # Load variables from .env file into environment

# --- Pinterest API Credentials ---
PINTEREST_APP_ID = os.getenv('PINTEREST_APP_ID')
PINTEREST_APP_SECRET = os.getenv('PINTEREST_APP_SECRET')
PINTEREST_ACCESS_TOKEN = os.getenv('PINTEREST_ACCESS_TOKEN') # Using manually generated token for now

# Check if essential Pinterest creds are missing (only if using the API path)
PINTEREST_API_ENABLED = bool(PINTEREST_ACCESS_TOKEN) # Enable API path only if token exists
if not PINTEREST_API_ENABLED:
     print("WARNING: PINTEREST_ACCESS_TOKEN not found in environment/.env. Pinterest API calls disabled.")


# Import recipe-scrapers library & specific error types
from recipe_scrapers import scrape_me, WebsiteNotImplementedError, NoSchemaFoundInWildMode
# Import requests exceptions separately for better handling
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout

# Basic configuration
DEBUG = False # Set to False for production deployment

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(__name__)

# Enable CORS
CORS(app, resources={r'/api/*': {'origins': '*'}}) # Adjust origins for production


# --- NEW: Pinterest API Helper Function ---
def get_pin_data_from_api(pin_id):
    """Fetches Pin data using Pinterest API v5."""
    if not PINTEREST_API_ENABLED:
        print("Pinterest API is disabled (missing access token).")
        return None # Cannot proceed without token

    api_url = f"https://api.pinterest.com/v5/pins/{pin_id}"
    headers = {
        "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    print(f"--- Calling Pinterest API: GET {api_url} ---")
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        pin_data = response.json()
        print("--- Pinterest API Response Received ---")
        # print(json.dumps(pin_data, indent=2)) # Optional: Log full response for debugging
        return pin_data
    except HTTPError as http_err:
         # Handle specific API errors (e.g., 401 Unauthorized, 404 Not Found)
         print(f"HTTP error occurred calling Pinterest API: {http_err} - Response: {http_err.response.text}")
         if http_err.response.status_code == 401:
              raise ValueError("Pinterest API authentication failed. Check your Access Token.")
         elif http_err.response.status_code == 404:
              raise ValueError(f"Pin with ID {pin_id} not found via Pinterest API.")
         else:
              raise ValueError(f"Pinterest API returned an error (Status {http_err.response.status_code}).")
    except RequestException as req_err:
        print(f"Network error occurred calling Pinterest API: {req_err}")
        raise ValueError("Could not connect to the Pinterest API.")
    except json.JSONDecodeError as json_err:
         print(f"Error decoding Pinterest API response: {json_err}")
         raise ValueError("Received an invalid response from the Pinterest API.")
    except Exception as e:
        print(f"Unexpected error during Pinterest API call: {e}")
        traceback.print_exc()
        raise ValueError("An unexpected error occurred while fetching data from Pinterest API.")


# --- Helper: Extract Pin ID from URL ---
def extract_pin_id(pinterest_url):
    match = re.search(r'/pin/(\d+)/?', pinterest_url)
    return match.group(1) if match else None


# --- Scraping Logic Functions (scrape_ingredients_with_library, scrape_ingredients_with_bs) ---
# (These remain unchanged from v3.10.2)
def scrape_ingredients_with_library(url, headers): /* ... Same as v3.10.2 ... */
def scrape_ingredients_with_bs(url, headers): /* ... Same as v3.10.2 ... */


# --- Main API Endpoint (v3.11 - Uses Pinterest API) ---
@app.route('/api/rip-recipe', methods=['POST'])
def rip_recipe_api():
    if not request.is_json: return jsonify({"error": "Request format must be JSON"}), 415
    data = request.get_json()
    original_url = data.get('url')
    if not original_url: return jsonify({"error": "Missing required 'url' field in JSON request"}), 400
    if not re.match(r'^https?://', original_url): return jsonify({"error": "Invalid URL provided. Please include http:// or https://"}), 400

    target_url = original_url # Default target
    is_pinterest = 'pinterest.com' in original_url.lower() and '/pin/' in original_url.lower()
    headers = { # Standard headers for scraping external sites
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate, br', 'DNT': '1',
        'Upgrade-Insecure-Requests': '1', 'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1', 'Sec-Ch-Ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
        'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': '"Windows"'
    }

    try:
        print(f"Received URL for processing: {original_url}")
        ingredients_text = None

        # --- Determine target URL ---
        if is_pinterest:
            if not PINTEREST_API_ENABLED:
                 raise ValueError("Pinterest API is not configured (missing Access Token). Cannot process Pinterest links.")

            print("Pinterest URL detected. Attempting to use Pinterest API...")
            pin_id = extract_pin_id(original_url)
            if not pin_id:
                 raise ValueError("Could not extract Pin ID from the provided Pinterest URL.")

            pin_data = get_pin_data_from_api(pin_id) # Call API helper

            if pin_data and pin_data.get('link'): # Check if link exists in API response
                 link = pin_data.get('link')
                 # Clean the link (sometimes has tracking)
                 parsed_link = urlparse(link)
                 cleaned_link = f"{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path}"
                 if parsed_link.query: # Keep query params if they exist
                     cleaned_link += f"?{parsed_link.query}"

                 # Ensure it's not linking back to Pinterest
                 if cleaned_link and 'pinterest.com' not in urlparse(cleaned_link).netloc:
                      target_url = cleaned_link # Use the link from the API!
                      print(f"Found source URL via Pinterest API: {target_url}")
                 else:
                      print(f"API returned a link, but it points back to Pinterest or is invalid: {link}")
                      raise ValueError("The link found on Pinterest points back to Pinterest itself. Please provide the direct recipe URL.")
            else:
                 # API didn't return a link field
                 print("Pinterest API did not provide a source link for this Pin.")
                 # Optionally try to get ingredients from description field if needed?
                 # desc_ingredients = pin_data.get('description') # Handle this text if desired
                 raise ValueError("Could not find a source recipe link via the Pinterest API for this Pin.")
        else:
            target_url = original_url # Not Pinterest, scrape directly

        target_info_for_frontend = target_url # The URL we will actually attempt to scrape

        # --- Scrape the final target URL ---
        print(f"Attempting scrape on final target: {target_url}")
        ingredients_text = scrape_ingredients_with_library(target_url, headers)

        if ingredients_text is None:
            print("Library scraping failed or unsupported, trying BeautifulSoup fallback...")
            # Check again: don't run BS fallback on a Pinterest URL
            if 'pinterest.com' in target_url.lower() and '/pin/' in target_url.lower():
                 print("BS fallback skipped for Pinterest URL.")
                 # Should not happen based on logic above, but safety check
            else:
                 ingredients_text = scrape_ingredients_with_bs(target_url, headers)

        # --- Process results ---
        if ingredients_text:
            print("--- Successfully obtained ingredients ---")
            return jsonify({
                "ingredients": ingredients_text,
                "source_url_scraped": target_info_for_frontend
            })
        else:
            # If all applicable methods failed
            print(f"--- All scraping methods failed for {target_info_for_frontend} ---")
            error_msg = f"Could not automatically find ingredients for the target URL: {target_info_for_frontend}. The site structure may be unsupported or blocked."
            return jsonify({"error": error_msg}), 400

    except ValueError as e: # Catch user-friendly errors (including API/Pinterest issues)
        print(f"--- Handled Value Error: {e} ---")
        return jsonify({"error": str(e)}), 400
    except Exception as e: # Catch any other unexpected errors
        print(f"--- Unexpected Server Error in API handler: {e} ---")
        traceback.print_exc()
        return jsonify({"error": "An unexpected server error occurred."}), 500


# --- Run the App ---
if __name__ == '__main__':
    # (Local dev server block remains the same as v3.10.1)
    print("-------------------------------------------------------")
    print("Starting Flask DEVELOPMENT server (for local testing)...")
    print("DO NOT use this server for production deployment.")
    print("-------------------------------------------------------")
    local_port = 5000
    print(f"Local access: http://127.0.0.1:{local_port}")
    try:
         app.run(debug=True, host='127.0.0.1', port=local_port)
    except OSError as e:
         print(f"\nERROR: Could not start development server on port {local_port}.")
         if "address already in use" in str(e).lower():
              print("       Another application might be using this port.")
         print("       Try stopping the other application or choosing a different port.")
