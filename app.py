import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import traceback
import json
from urllib.parse import urlparse, parse_qs

# Import recipe-scrapers library & specific error types
from recipe_scrapers import scrape_me, WebsiteNotImplementedError
# Import requests exceptions separately for better handling
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout
# ** Import urllib error for library fallback **
import urllib.error

# Basic configuration
DEBUG = False # Set to False for production deployment

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(__name__)

# Enable CORS
CORS(app, resources={r'/api/*': {'origins': '*'}}) # Adjust origins for production

# --- Helper Function: Extract Source URL from Pinterest ---
# (No changes needed in this function from the last version)
def extract_source_url_from_pinterest(pinterest_url, headers):
    """
    Attempts to find the external source URL linked from a Pinterest pin page.
    Uses multiple strategies. Returns None if no external URL is reliably found.
    """
    print(f"--- Attempting to extract source URL from Pinterest: {pinterest_url} ---")
    source_url = None
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
                    item_type = item.get('@type', ''); current_source_url = None
                    if 'Recipe' in item_type: current_source_url = item.get('mainEntityOfPage', {}).get('@id') or item.get('url')
                    elif 'CreativeWork' in item_type or 'Article' in item_type: current_source_url = item.get('mainEntityOfPage', {}).get('@id') or item.get('url') or item.get('url')
                    if current_source_url and isinstance(current_source_url, str) and current_source_url.startswith('http') and 'pinterest.com' not in current_source_url:
                        print(f"Found source URL via JSON-LD ({item_type}): {current_source_url}"); source_url = current_source_url; break
                if source_url: return source_url
            except Exception as e: print(f"Error processing JSON-LD: {e}")

        # Strategy 2: Meta Tags
        if not source_url:
            meta_tag = soup.find('meta', property='og:see_also')
            if meta_tag and meta_tag.get('content','').startswith('http') and 'pinterest.com' not in meta_tag['content']:
                 source_url = meta_tag['content']; print(f"Found source URL via meta og:see_also: {source_url}"); return source_url

        # Strategy 3: Specific Link Attributes
        if not source_url:
            link_selectors = ['a[data-test-id="pin-closeup-link"]','div[data-test-id="CloseupDetails"] a[href^="http"]','a[data-test-id="forward-button"]','a[class*="linkModule"]','a[class*="externalLink"]','div[data-test-id="pin-visual-wrapper"] a[href^="http"]']
            for selector in link_selectors:
                potential_link = soup.select_one(selector)
                if potential_link and potential_link.get('href','').startswith('http'):
                     href = potential_link['href']
                     if 'pinterest.com/redirect/' in href:
                         try:
                             parsed_href = urlparse(href); final_url = parse_qs(parsed_href.query).get('url', [None])[0]
                             if final_url: print(f"Resolved redirect from selector '{selector}': {final_url}"); return final_url
                         except Exception: pass
                     elif 'pinterest.com' not in href:
                         print(f"Found potential source URL via selector '{selector}': {href}")
                         return href

        print("--- Could not find a reliable source URL on the Pinterest page via known methods. ---")
        return None
    except RequestException as e: print(f"Failed to fetch Pinterest URL {pinterest_url}: {e}"); raise ValueError(f"Could not fetch the Pinterest page (URL: {pinterest_url}). Error: {e}")
    except Exception as e: print(f"Error parsing Pinterest page {pinterest_url}: {e}"); traceback.print_exc(); raise ValueError(f"An error occurred while trying to analyze the Pinterest page.")


# --- Scraping Logic Function: Using recipe-scrapers library (REVISED Error Handling) ---
def scrape_ingredients_with_library(url, headers):
    """Attempts scraping using the recipe-scrapers library, handling network errors."""
    scraper = None
    try:
        print(f"--- Attempting scraping with recipe-scrapers library for: {url} ---")
        scraper = scrape_me(url) # Removed wild_mode argument
        print(f"Initialized scraper: {type(scraper).__name__}")

        if scraper:
            ingredients_list = scraper.ingredients() # This might trigger network request if not done before
            if ingredients_list:
                print(f"--- recipe-scrapers successful: Found {len(ingredients_list)} ingredients ---")
                cleaned_list = []; junk_keywords_library = ["advertisement","nutrition","subscribe","related","you may also like","jump to","print recipe","rate this","leave a comment","serving size","calories","video","instructions","notes","equipment","expert tips", "recipe developer", "photographer"]
                for item in ingredients_list:
                    item_lower = item.lower(); item_strip = item.strip()
                    if item_strip and not any(keyword in item_lower for keyword in junk_keywords_library):
                         if len(item_strip.split()) > 1 or any(char.isdigit() for char in item_strip): cleaned_list.append(item_strip)
                return "\n".join(cleaned_list) if cleaned_list else None
            else:
                print("--- recipe-scrapers found scraper but no ingredients method result. ---")
                return None
        else:
             print("--- recipe-scrapers library could not initialize scraper object. ---")
             return None

    # --- Catch Specific Errors from recipe-scrapers/urllib ---
    except WebsiteNotImplementedError:
        print(f"--- recipe-scrapers does not support this specific website: {url} ---")
        return None # Site not supported, allow fallback
    except urllib.error.HTTPError as http_err: # Catch HTTP errors (like 403) from internal request
         print(f"--- HTTP error during recipe-scrapers internal fetch: {http_err} ---")
         return None # Treat as failure, allow fallback
    except urllib.error.URLError as url_err: # Catch other URL errors (like connection refused)
         print(f"--- URL error during recipe-scrapers internal fetch: {url_err} ---")
         return None # Treat as failure, allow fallback
    except (RequestException, ConnectionError, HTTPError, Timeout) as req_err: # Catch potential requests errors if library uses it
        print(f"--- Network error during recipe-scrapers processing (requests): {req_err} ---")
        return None
    except Exception as e: # Catch other unexpected library errors
        print(f"--- Unexpected error during recipe-scrapers processing: {e} ---")
        traceback.print_exc()
        return None # Return None on errors to allow BS fallback


# --- Scraping Logic Function: Using BeautifulSoup (Fallback) ---
# (No changes needed in this function from v3.10.4)
def scrape_ingredients_with_bs(url, headers):
    """Fallback scraping using BeautifulSoup (custom logic for NON-PINTEREST URLs)."""
    print(f"--- Falling back to BeautifulSoup scraping for: {url} ---")
    if 'pinterest.com' in url.lower() and '/pin/' in url.lower(): print("BS Scraper - Error: BS fallback should not be called directly for Pinterest URLs."); return None
    ingredients = []; processed_elements = set()
    try:
        response = requests.get(url, headers=headers, timeout=15); print(f"BS Scraper - Received status code: {response.status_code}"); response.raise_for_status()
        try: import lxml; parser = 'lxml'
        except ImportError: parser = 'html.parser'
        print(f"BS Scraper - Using HTML parser: {parser}"); soup = BeautifulSoup(response.content, parser)
        # BS Strategy 1 & 2 and Cleaning (same as v3.10.4)
        common_item_classes=['wprm-recipe-ingredient','tasty-recipes-ingredient','mv-recipe-ingredient','ingredients-item-name','recipe-ingredient','ingredient']; print("BS Scraper - Running Strategy 1: Specific Item Classes")
        for class_name in common_item_classes: elements=soup.find_all(class_=re.compile(r'\b'+re.escape(class_name)+r'\b',re.I)); if elements:
            for el in elements: el_id=str(el); if el_id not in processed_elements: text_parts=[part.strip() for part in el.stripped_strings]; text=' '.join(filter(None,text_parts)); if text: ingredients.append(text); processed_elements.add(el_id)
        print("BS Scraper - Running Strategy 2: Lists (ul/ol)"); list_containers=[]; potential_list_classes=['ingredients','ingredient-list','recipe-ingredients']
        for list_class in potential_list_classes: found_lists=soup.find_all(['ul','ol'], class_=re.compile(r'\b'+re.escape(list_class)+r'\b',re.I)); if found_lists: list_containers.extend(found_lists)
        headings=soup.find_all(['h2','h3','h4','h5','strong','p'], string=re.compile(r'(ingredients|for the\b|\btips\b|\bnotes\b)',re.I))
        for heading in headings:
            heading_text=heading.get_text(strip=True); is_relevant_heading=2<len(heading_text)<60; is_likely_paragraph=len(heading_text.split())>10 and '.' in heading_text
            if is_relevant_heading and not is_likely_paragraph:
                 is_already_added=False
                 if ingredients: clean_heading=heading_text.lower().rstrip(':').strip(); clean_last_item=ingredients[-1].lower().rstrip(':').strip(); if clean_heading==clean_last_item: is_already_added=True
                 if not is_already_added: heading_id=str(heading); if heading_id not in processed_elements: ingredients.append(heading_text); processed_elements.add(heading_id)
            list_element=heading.find_next_sibling(['ul','ol']); if list_element and len(list_element.find_all('li'))<50: if list_element not in list_containers: list_containers.append(list_element)
            list_element_inside=heading.find_next(['ul','ol']); if list_element_inside and len(list_element_inside.find_all('li'))<50: if list_element_inside not in list_containers: list_containers.append(list_element_inside)
        processed_lists=set(); unique_list_containers=[]
        for lst in list_containers: list_id=str(lst); if list_id not in processed_lists: unique_list_containers.append(lst); processed_lists.add(list_id)
        if unique_list_containers:
             print(f"BS Scraper - Processing {len(unique_list_containers)} unique lists.")
             for lst in unique_list_containers:
                 possible_items=lst.find_all('li')
                 for item in possible_items:
                     item_id=str(item)
                     if item_id not in processed_elements:
                        text_parts=[part.strip() for part in item.stripped_strings]; text=' '.join(filter(None,text_parts)); has_number=any(char.isdigit() for char in text); is_reasonable_length=0<len(text.split())<25; is_not_just_link=not item.find('a') or len(item.find_all('a'))<len(text.split())/2; looks_like_junk=any(jp in text.lower() for jp in["related posts","you may also like","leave a reply","share this recipe","email recipe"])or text.lower().strip()=='ingredients'
                        if text and is_reasonable_length and is_not_just_link and not looks_like_junk: ingredients.append(text); processed_elements.add(item_id)
                        elif text and has_number and len(text.split())<25 and not looks_like_junk: ingredients.append(text); processed_elements.add(item_id)
        if not ingredients: print("BS Scraper - No potential ingredients found."); return None
        print(f"BS Scraper - Found {len(ingredients)} raw lines before cleaning."); junk_phrases_exact=["scale","usm","units","ingredients"]; junk_phrases_contain=["cook mode","prevent your screen","nutrition information","optional","equipment","instructions","recipe notes","serving size","calories","related posts","jump to recipe","print recipe","pin recipe","advertisement","share this","you may also like","leave a reply","reader interactions","expert tips","variations","storage","make ahead","about","contact","partner with us","privacy policy","terms of service","careers","media kit","advertising","subscribe","newsletter","all rights reserved","back to top","more recipes","shop","similar recipes","faq","frequently asked questions","sponsored","disclosure","affiliate links","this post may contain","skip to content","skip to main content","search","log in","register","about at media","image","photo","video","recipe originally published","sign up","follow us","get the book","free trial"]; junk_patterns_regex=[r'^\d+/\d+x\d+x\d+x$',r'^\d+x$',r'click here',r'print recipe',r'pin recipe',r'jump to recipe',r'advertisement',r'^\s*▢\s*',r'^\d+\s+comments?$',r'^\d+\s+minutes?$',r'(?i)Course:',r'(?i)Cuisine:',r'(?i)Keyword:',r'(?i)Prep time:',r'(?i)Cook time:',r'(?i)Total time:',r'(?i)Servings:',r'^\©?\s*\d{4}',r'(?i)facebook',r'(?i)instagram',r'(?i)twitter',r'(?i)pinterest',r'(?i)youtube',r'(?i)tiktok',r'(?i)read more',r'^\s*posted on',r'^\s*updated on',r'^\s*by\s+[A-Za-z\s.-]+',r'^\s*(previous|next)\s+(post|recipe)',r'\.{3,}','★|☆',r'^(watch|view)\s+video',r'(?i)link in bio',r'(?i)featured in']
        cleaned_ingredients=[];
        for item in ingredients:
            original_item_stripped=item.strip(); temp_item_lower=original_item_stripped.lower(); is_junk=False; word_count=len(original_item_stripped.split())
            if word_count > 35: is_junk=True
            if not is_junk and word_count==1 and not any(char.isdigit() for char in original_item_stripped): allowed_single_words={'salt','pepper','oil','sugar','flour','water','milk','eggs','butter','onion','garlic'}; if temp_item_lower not in allowed_single_words: is_junk=True
            if not is_junk and temp_item_lower in junk_phrases_exact: is_junk=True
            if not is_junk:
                for junk in junk_phrases_contain:
                    if junk in temp_item_lower:
                         if word_count>4 or len(junk.split())<=2 : is_junk=True; break
            if not is_junk:
                for pattern in junk_patterns_regex:
                    if re.search(pattern, original_item_stripped, re.I): is_junk=True; break
            if not is_junk and original_item_stripped:
                 if item.isupper() and 1<word_count<6: cleaned_ingredients.append(original_item_stripped.title())
                 else: cleaned_ingredients.append(original_item_stripped)
        seen=set(); final_ingredients=[]
        for item in cleaned_ingredients: item_lower=item.lower().strip().rstrip(':').strip(); if item_lower and item_lower not in seen: final_ingredients.append(item); seen.add(item_lower)
        if not final_ingredients: print("BS Scraper - Cleaning removed all items."); return None
        print(f"BS Scraper - Returning {len(final_ingredients)} cleaned ingredients."); return "\n".join(final_ingredients)
    except RequestException as e: print(f"BS Scraper - Request failed for URL {url}: {e}"); status_code=e.response.status_code if hasattr(e,'response')and e.response is not None else None; msg=f"Could not fetch URL for scraping ({status_code if status_code else 'Network Error'})."; if isinstance(e,HTTPError)and status_code==403:msg=f"Access Forbidden (403). The website blocked the request.";elif isinstance(e,HTTPError):msg=f"Website error (Status {status_code}). Page might be missing or restricted.";elif isinstance(e,ConnectionError):msg=f"Could not connect to the website at {url}.";elif isinstance(e,Timeout):msg=f"The request to {url} timed out."; raise ValueError(msg)
    except Exception as e: print(f"BS Scraper - Error during BeautifulSoup processing for URL {url}: {e}"); traceback.print_exc(); raise ValueError(f"An error occurred while parsing the recipe content (fallback method).")


# --- Main API Endpoint (v3.10.6 - Catch HTTPError in library call) ---
@app.route('/api/rip-recipe', methods=['POST'])
def rip_recipe_api():
    if not request.is_json: return jsonify({"error": "Request format must be JSON"}), 415
    data = request.get_json()
    original_url = data.get('url')
    if not original_url: return jsonify({"error": "Missing required 'url' field in JSON request"}), 400
    if not re.match(r'^https?://', original_url): return jsonify({"error": "Invalid URL provided. Please include http:// or https://"}), 400

    target_url = original_url # Default target
    headers = { # Standard headers
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
        is_pinterest = 'pinterest.com' in original_url.lower() and '/pin/' in original_url.lower()
        ingredients_text = None

        # Determine target URL
        if is_pinterest:
            print("Pinterest URL detected. Attempting to find source URL...")
            source_url = extract_source_url_from_pinterest(original_url, headers)
            if source_url: target_url = source_url; print(f"Found source URL, proceeding to scrape: {target_url}")
            else: print("Could not find source URL on Pinterest page. Aborting."); raise ValueError("Could not find the source recipe link on the Pinterest page. Please provide the direct recipe URL.")
        # else target_url remains original_url

        target_info_for_frontend = target_url

        # Scrape the final target URL
        print(f"Attempting scrape on final target: {target_url}")
        ingredients_text = scrape_ingredients_with_library(target_url, headers)

        # Fallback to BeautifulSoup (only if not Pinterest)
        if ingredients_text is None:
            print("Library scraping failed or unsupported, trying BeautifulSoup fallback...")
            if 'pinterest.com' in target_url.lower() and '/pin/' in target_url.lower():
                 print("BS fallback skipped for Pinterest URL.")
            else:
                 ingredients_text = scrape_ingredients_with_bs(target_url, headers)

        # Process results
        if ingredients_text:
            print("--- Successfully obtained ingredients ---")
            return jsonify({ "ingredients": ingredients_text, "source_url_scraped": target_info_for_frontend })
        else:
            print(f"--- All scraping methods failed for {target_info_for_frontend} ---")
            error_msg = f"Could not automatically find ingredients for the target URL: {target_info_for_frontend}. The site structure may be unsupported or blocked."
            return jsonify({"error": error_msg}), 400

    except ValueError as e: print(f"--- Handled Value Error: {e} ---"); return jsonify({"error": str(e)}), 400
    except Exception as e: print(f"--- Unexpected Server Error in API handler: {e} ---"); traceback.print_exc(); return jsonify({"error": "An unexpected server error occurred."}), 500


# --- Run the App ---
if __name__ == '__main__':
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
         if "address already in use" in str(e).lower(): print("       Another application might be using this port.")
         print("       Try stopping the other application or choosing a different port.")
