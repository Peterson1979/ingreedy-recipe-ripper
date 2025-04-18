import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import traceback
import json

# Import recipe-scrapers library
from recipe_scrapers import scrape_me, WebsiteNotImplementedError

# Basic configuration
DEBUG = False # Set to False for production deployment

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(__name__)

# Enable CORS
CORS(app, resources={r'/api/*': {'origins': '*'}}) # Adjust origins for production

# --- Helper Function: Extract Source URL from Pinterest ---
def extract_source_url_from_pinterest(pinterest_url, headers):
    """
    Attempts to find the external source URL linked from a Pinterest pin page.
    Uses multiple strategies. Returns None if no external URL is reliably found.
    """
    print(f"--- Attempting to extract source URL from Pinterest: {pinterest_url} ---")
    try:
        response = requests.get(pinterest_url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Strategy 1: JSON-LD
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if script_tag and script_tag.string:
            try:
                json_data = json.loads(script_tag.string); data_to_check = []
                if isinstance(json_data, dict): data_to_check.append(json_data)
                if isinstance(json_data, list): data_to_check.extend(json_data)
                if isinstance(json_data, dict) and '@graph' in json_data and isinstance(json_data['@graph'], list): data_to_check.extend(json_data['@graph'])
                for item in data_to_check:
                    if not isinstance(item, dict): continue
                    item_type = item.get('@type', ''); source_url = None
                    if 'Recipe' in item_type: source_url = item.get('mainEntityOfPage', {}).get('@id') or item.get('url')
                    elif 'CreativeWork' in item_type or 'Article' in item_type: source_url = item.get('mainEntityOfPage', {}).get('@id') or item.get('url') or item.get('url')
                    if source_url and isinstance(source_url, str) and source_url.startswith('http') and 'pinterest.com' not in source_url:
                        print(f"Found source URL via JSON-LD ({item_type}): {source_url}"); return source_url
            except Exception as e: print(f"Error processing JSON-LD: {e}")

        # Strategy 2: Meta Tags
        meta_tag = soup.find('meta', property='og:see_also')
        if meta_tag and meta_tag.get('content','').startswith('http') and 'pinterest.com' not in meta_tag['content']:
             source_url = meta_tag['content']; print(f"Found source URL via meta og:see_also: {source_url}"); return source_url

        # Strategy 3: Specific Link Attributes
        link_selectors = ['a[data-test-id="pin-closeup-link"]','div[data-test-id="CloseupDetails"] a[href^="http"]','a[data-test-id="forward-button"]','a[class*="linkModule"]','a[class*="externalLink"]','div[data-test-id="pin-visual-wrapper"] a[href^="http"]']
        for selector in link_selectors:
            potential_link = soup.select_one(selector)
            if potential_link and potential_link.get('href','').startswith('http'):
                 source_url = potential_link['href']
                 if 'pinterest.com' not in source_url or '/redirect/?' in source_url:
                      print(f"Found potential source URL via selector '{selector}': {source_url}"); return source_url

        print("--- Could not find a reliable source URL on the Pinterest page via known methods. ---")
        return None
    except requests.exceptions.RequestException as e: print(f"Failed to fetch Pinterest URL {pinterest_url}: {e}"); raise ValueError(f"Could not fetch the Pinterest page (URL: {pinterest_url}). Error: {e}")
    except Exception as e: print(f"Error parsing Pinterest page {pinterest_url}: {e}"); traceback.print_exc(); raise ValueError(f"An error occurred while trying to analyze the Pinterest page.")


# --- Scraping Logic Function: Using recipe-scrapers library ---
def scrape_ingredients_with_library(url, headers):
    """Attempts scraping using the recipe-scrapers library."""
    try:
        print(f"--- Attempting scraping with recipe-scrapers library for: {url} ---")
        scraper = scrape_me(url, wild_mode=True)
        ingredients_list = scraper.ingredients()
        if ingredients_list:
            print(f"--- recipe-scrapers successful: Found {len(ingredients_list)} ingredients ---")
            cleaned_list = []; junk_keywords_library = ["advertisement","nutrition","subscribe","related","you may also like","jump to","print recipe","rate this","leave a comment","serving size","calories","video","instructions","notes","equipment","expert tips"]
            for item in ingredients_list:
                item_lower = item.lower()
                if item and item.strip() and not any(keyword in item_lower for keyword in junk_keywords_library):
                     if len(item.split()) > 1 or any(char.isdigit() for char in item): cleaned_list.append(item.strip())
            return "\n".join(cleaned_list) if cleaned_list else None
        else: print("--- recipe-scrapers found no ingredients. ---"); return None
    except WebsiteNotImplementedError: print(f"--- recipe-scrapers does not support this specific website: {url} ---"); return None
    except Exception as e: print(f"--- Error during recipe-scrapers processing: {e}"); traceback.print_exc(); return None


# --- Scraping Logic Function: Using BeautifulSoup (Fallback) ---
def scrape_ingredients_with_bs(url, headers):
    """Fallback scraping using BeautifulSoup (custom logic for NON-PINTEREST URLs)."""
    print(f"--- Falling back to BeautifulSoup scraping for: {url} ---")
    ingredients = []
    processed_elements = set()
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"BS Scraper - Received status code: {response.status_code}")
        response.raise_for_status()
        try: import lxml; parser = 'lxml'
        except ImportError: parser = 'html.parser'
        print(f"BS Scraper - Using HTML parser: {parser}")
        soup = BeautifulSoup(response.content, parser)

        # --- BS Strategy 1: Specific item classes ---
        common_item_classes = ['wprm-recipe-ingredient', 'tasty-recipes-ingredient','mv-recipe-ingredient', 'ingredients-item-name','recipe-ingredient', 'ingredient']
        print("BS Scraper - Running Strategy 1: Specific Item Classes")
        for class_name in common_item_classes:
            elements = soup.find_all(class_=re.compile(r'\b' + re.escape(class_name) + r'\b', re.I))
            if elements:
                for el in elements:
                    el_id = str(el)
                    if el_id not in processed_elements:
                        text_parts=[part.strip() for part in el.stripped_strings]; text=' '.join(filter(None, text_parts));
                        if text: ingredients.append(text); processed_elements.add(el_id)

        # --- BS Strategy 2: Lists near headings ---
        print("BS Scraper - Running Strategy 2: Lists (ul/ol)")
        list_containers = []
        potential_list_classes = ['ingredients', 'ingredient-list', 'recipe-ingredients']
        for list_class in potential_list_classes:
             found_lists = soup.find_all(['ul', 'ol'], class_=re.compile(r'\b' + re.escape(list_class) + r'\b', re.I));
             if found_lists: list_containers.extend(found_lists)
        headings = soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'p'], string=re.compile(r'(ingredients|for the\b|\btips\b|\bnotes\b)', re.I))
        for heading in headings:
            heading_text = heading.get_text(strip=True); is_relevant_heading = 2 < len(heading_text) < 60; is_likely_paragraph = len(heading_text.split()) > 10 and '.' in heading_text
            if is_relevant_heading and not is_likely_paragraph:
                 is_already_added = False
                 if ingredients:
                     clean_heading = heading_text.lower().rstrip(':').strip()
                     clean_last_item = ingredients[-1].lower().rstrip(':').strip()
                     if clean_heading == clean_last_item: is_already_added = True
                 if not is_already_added:
                     heading_id = str(heading)
                     if heading_id not in processed_elements:
                         ingredients.append(heading_text)
                         processed_elements.add(heading_id)
            list_element = heading.find_next_sibling(['ul', 'ol']);
            if list_element and len(list_element.find_all('li')) < 50:
                 if list_element not in list_containers: list_containers.append(list_element)
            list_element_inside = heading.find_next(['ul','ol']);
            if list_element_inside and len(list_element_inside.find_all('li')) < 50:
                 if list_element_inside not in list_containers: list_containers.append(list_element_inside)
        processed_lists = set(); unique_list_containers = []
        for lst in list_containers:
            list_id = str(lst)
            if list_id not in processed_lists:
                unique_list_containers.append(lst)
                processed_lists.add(list_id)

        if unique_list_containers:
             print(f"BS Scraper - Processing {len(unique_list_containers)} unique lists.")
             for lst in unique_list_containers:
                 possible_items = lst.find_all('li')
                 for item in possible_items:
                     item_id = str(item)
                     if item_id not in processed_elements:
                        text_parts=[part.strip() for part in item.stripped_strings]; text=' '.join(filter(None, text_parts)); has_number=any(char.isdigit() for char in text); is_reasonable_length=0 < len(text.split()) < 25; is_not_just_link=not item.find('a') or len(item.find_all('a'))<len(text.split())/2; looks_like_junk=any(jp in text.lower() for jp in["related posts","you may also like","leave a reply","share this recipe","email recipe"])or text.lower().strip()=='ingredients'
                        if text and is_reasonable_length and is_not_just_link and not looks_like_junk: ingredients.append(text); processed_elements.add(item_id)
                        elif text and has_number and len(text.split()) < 25 and not looks_like_junk: ingredients.append(text); processed_elements.add(item_id)

        # --- BS Cleaning Stage ---
        if not ingredients: print("BS Scraper - No potential ingredients found."); return None
        print(f"BS Scraper - Found {len(ingredients)} raw lines before cleaning.")
        junk_phrases_exact = [ "scale", "usm", "units", "ingredients" ]
        junk_phrases_contain = ["cook mode","prevent your screen","nutrition information","optional","equipment","instructions","recipe notes","serving size","calories","related posts","jump to recipe","print recipe","pin recipe","advertisement","share this","you may also like","leave a reply","reader interactions","expert tips","variations","storage","make ahead","about","contact","partner with us","privacy policy","terms of service","careers","media kit","advertising","subscribe","newsletter","all rights reserved","back to top","more recipes","shop","similar recipes","faq","frequently asked questions","sponsored","disclosure","affiliate links","this post may contain","skip to content","skip to main content","search","log in","register","about at media","image","photo","video","recipe originally published","sign up","follow us","get the book","free trial"]
        junk_patterns_regex = [r'^\d+/\d+x\d+x\d+x$',r'^\d+x$',r'click here',r'print recipe',r'pin recipe',r'jump to recipe',r'advertisement',r'^\s*▢\s*',r'^\d+\s+comments?$',r'^\d+\s+minutes?$',r'(?i)Course:',r'(?i)Cuisine:',r'(?i)Keyword:',r'(?i)Prep time:',r'(?i)Cook time:',r'(?i)Total time:',r'(?i)Servings:',r'^\©?\s*\d{4}',r'(?i)facebook',r'(?i)instagram',r'(?i)twitter',r'(?i)pinterest',r'(?i)youtube',r'(?i)tiktok',r'(?i)read more',r'^\s*posted on',r'^\s*updated on',r'^\s*by\s+[A-Za-z\s.-]+',r'^\s*(previous|next)\s+(post|recipe)',r'\.{3,}','★|☆',r'^(watch|view)\s+video',r'(?i)link in bio',r'(?i)featured in']
        cleaned_ingredients = []
        for item in ingredients:
            original_item_stripped = item.strip(); temp_item_lower = original_item_stripped.lower(); is_junk = False; word_count = len(original_item_stripped.split())
            if word_count > 35: is_junk = True
            if not is_junk and word_count == 1 and not any(char.isdigit() for char in original_item_stripped):
                 allowed_single_words = {'salt','pepper','oil','sugar','flour','water','milk','eggs','butter','onion','garlic'};
                 if temp_item_lower not in allowed_single_words: is_junk = True
            if not is_junk and temp_item_lower in junk_phrases_exact: is_junk = True
            if not is_junk:
                for junk in junk_phrases_contain:
                    if junk in temp_item_lower:
                         if word_count > 4 or len(junk.split()) <= 2 : is_junk = True; break
            if not is_junk:
                for pattern in junk_patterns_regex:
                    if re.search(pattern, original_item_stripped, re.I): is_junk = True; break
            if not is_junk and original_item_stripped:
                 if item.isupper() and 1 < word_count < 6: cleaned_ingredients.append(original_item_stripped.title())
                 else: cleaned_ingredients.append(original_item_stripped)

        seen = set(); final_ingredients = []
        for item in cleaned_ingredients:
            item_lower = item.lower().strip().rstrip(':').strip()
            if item_lower and item_lower not in seen:
                final_ingredients.append(item)
                seen.add(item_lower)

        if not final_ingredients: print("BS Scraper - Cleaning removed all items."); return None
        print(f"BS Scraper - Returning {len(final_ingredients)} cleaned ingredients.")
        return "\n".join(final_ingredients)

    # --- BS Error Handling (Corrected Structure) ---
    except requests.exceptions.RequestException as e:
        print(f"BS Scraper - Request failed for URL {url}: {e}")
        status_code = None
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code

        if isinstance(e, requests.exceptions.HTTPError) and status_code == 403:
            msg = f"Access Forbidden (403). The website blocked the request."
        elif isinstance(e, requests.exceptions.HTTPError):
            msg = f"Website error (Status {status_code}). Page might be missing or restricted."
        elif isinstance(e, requests.exceptions.ConnectionError):
            msg = f"Could not connect to the website at {url}."
        elif isinstance(e, requests.exceptions.Timeout):
            msg = f"The request to {url} timed out."
        else:
            msg = f"Could not fetch URL for scraping ({status_code if status_code else 'Network Error'})."
        raise ValueError(msg) # Raise the determined message

    except Exception as e:
        print(f"BS Scraper - Error during BeautifulSoup processing for URL {url}: {e}")
        traceback.print_exc()
        raise ValueError(f"An error occurred while parsing the recipe content (fallback method).")


# --- Main API Endpoint ---
@app.route('/api/rip-recipe', methods=['POST'])
def rip_recipe_api():
    if not request.is_json: return jsonify({"error": "Request format must be JSON"}), 415
    data = request.get_json()
    original_url = data.get('url')
    if not original_url: return jsonify({"error": "Missing required 'url' field in JSON request"}), 400
    if not re.match(r'^https?://', original_url): return jsonify({"error": "Invalid URL provided. Please include http:// or https://"}), 400

    target_url = original_url # Default target
    headers = { # Standard headers
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate, br', 'DNT': '1',
        'Upgrade-Insecure-Requests': '1', 'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1', 'Sec-Ch-Ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': '"Windows"'
    }

    try:
        print(f"Received URL for processing: {original_url}")
        is_pinterest = 'pinterest.com' in original_url.lower() and '/pin/' in original_url.lower()
        ingredients_text = None

        # --- Try extracting from URL ---
        if is_pinterest:
            print("Pinterest URL detected. Attempting to find source URL...")
            source_url = extract_source_url_from_pinterest(original_url, headers)
            if source_url:
                 target_url = source_url # Scrape the external link
                 print(f"Found source URL, proceeding to scrape: {target_url}")
                 # Scrape target_url using library->BS fallback
                 ingredients_text = scrape_ingredients_with_library(target_url, headers)
                 if ingredients_text is None:
                     print("Library scraping failed/unsupported for external link, trying BS fallback...")
                     ingredients_text = scrape_ingredients_with_bs(target_url, headers)
            else:
                 # *** If no external link FOUND -> ERROR ***
                 print("Could not find source URL on Pinterest page. Aborting.")
                 raise ValueError("Could not find the source recipe link on the Pinterest page. Please provide the direct recipe URL.")
        else:
            # --- Not a Pinterest URL, scrape directly ---
            target_url = original_url
            print(f"Standard URL detected. Scraping: {target_url}")
            ingredients_text = scrape_ingredients_with_library(target_url, headers)
            if ingredients_text is None:
                print("Library scraping failed or unsupported, trying BS fallback...")
                ingredients_text = scrape_ingredients_with_bs(target_url, headers)

        # --- Process results ---
        target_info_for_frontend = target_url # The URL we actually attempted to scrape

        if ingredients_text:
            print("--- Successfully obtained ingredients ---")
            return jsonify({
                "ingredients": ingredients_text,
                "source_url_scraped": target_info_for_frontend
            })
        else:
            # If all methods failed for the target_url
            print(f"--- All scraping methods failed for {target_info_for_frontend} ---")
            error_msg = f"Could not automatically find ingredients for the target URL: {target_info_for_frontend}. The site structure may be unsupported or blocked."
            # No longer check scraped_from_pinterest_desc as we don't attempt it
            return jsonify({"error": error_msg}), 400

    except ValueError as e: # Catch user-friendly errors
        print(f"--- Handled Value Error: {e} ---")
        return jsonify({"error": str(e)}), 400
    except Exception as e: # Catch any other unexpected errors
        print(f"--- Unexpected Server Error in API handler: {e} ---")
        traceback.print_exc()
        return jsonify({"error": "An unexpected server error occurred."}), 500


# --- Run the App ---
if __name__ == '__main__':
    # This block is primarily for LOCAL development testing using Flask's built-in server.
    # Hosting platforms (like Render) will typically use a WSGI server (like Waitress/Gunicorn)
    # and import the 'app' object directly or via wsgi.py, bypassing this block.
    print("-------------------------------------------------------")
    print("Starting Flask DEVELOPMENT server (for local testing)...")
    print("DO NOT use this server for production deployment.")
    print("-------------------------------------------------------")
    # Use a port common for local dev, Render provides its own port via ENV variable usually
    local_port = 5000
    print(f"Local access: http://127.0.0.1:{local_port}")
    # debug=True enables auto-reload during local development
    # Use host='0.0.0.0' ONLY if you need to access it from other devices on your local network during testing
    try:
         app.run(debug=True, host='127.0.0.1', port=local_port) # Keep debug=True for easy local testing restart
    except OSError as e:
         print(f"\nERROR: Could not start development server on port {local_port}.")
         if "address already in use" in str(e).lower():
              print("       Another application might be using this port.")
         print("       Try stopping the other application or choosing a different port.")