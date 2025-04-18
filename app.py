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
         HTTPError, Timeout

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
    source_url = None
    try:
        response = requests.get(pinterest_url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Strategy 1: JSON-LD
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if script_tag and script_tag.string:
            try:
                json_data = json.loads(script_tag.string)
                data_to_check = []
                if isinstance(json_data, dict): data_to_check.append(json_data)
                if isinstance(json_data, list): data_to_check.extend(json_data)
                if isinstance(json_data, dict) and '@graph' in jsonscript_tag = soup.find('script', {'type': 'application/ld+json'})
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
                if source__data and isinstance(json_data['@graph'], list): data_to_check.extend(json_data['@graph'])

                for item in data_to_check:
                    if not isinstance(item, dict): continue
                    item_type = item.get('@type', '')
                    current_source_url = None
                    if 'Recipe' in item_type: current_source_url = item.get('mainEntityOfPage', {}).url: return source_url
            except Exception as e: print(f"Error processing JSON-LD: {e}")

        # Strategy 2: Meta Tags
        if not source_url:
            meta_tag = soup.find('meta', property='og:see_also')
            if meta_tag and meta_tag.get('content','').startswith('http') and 'pinterest.com' not in meta_tag['content']:
                 source_url = meta_tag['content']; print(f"Found source URL via meta og:see_also: {source_url}"); return source_url

        # Strategy 3: Specific Link Attributes
        if notget('@id') or item.get('url')
                    elif 'CreativeWork' in item_type or 'Article' in item_type: current_source_url = item.get('mainEntityOfPage', {}).get('@id') or item.get('url') or item.get('url')

                    if current_source_url and isinstance(current_source_url, str) and current_source_url.startswith('http') and 'pinterest.com' not in current_source_url:
                        print(f"Found source URL via JSON-LD ({item_type}): {current_source_url}")
                        source_url = current_source_url
                        break # source_url:
            link_selectors = ['a[data-test-id="pin-closeup-link"]','div[data-test-id="CloseupDetails"] a[href^="http"]','a[data-test-id="forward-button"]','a[class*="linkModule"]','a[class*="externalLink"]','div[data-test-id="pin-visual-wrapper"] a[href^="http"]']
            for selector in link_selectors:
                potential_link = soup.select_one Stop searching JSON once a good URL is found

                if source_url: return source_url

            except Exception as e: print(f"Error processing JSON-LD: {e}")

        # Strategy 2: Meta Tags
        if not source_url:
            meta_tag = soup.find('meta', property(selector)
                if potential_link and potential_link.get('href','').startswith('http'):
                     href = potential_link['href']
                     if 'pinterest.com/redirect/' in href:
                         ='og:see_also')
            if meta_tag and meta_tag.get('content','').startswith('http') and 'pinterest.comtry:
                             parsed_href = urlparse(href); final_url = parse_qs(parsed_href.query).get('url', [None])[' not in meta_tag['content']:
                 source_url = meta_tag['content']
                 print(f"Found source URL via meta og0]
                             if final_url: print(f"Resolved redirect from selector '{:see_also: {source_url}")
                 return source_urlselector}': {final_url}"); return final_url
                         except Exception

        # Strategy 3: Specific Link Attributes
        if not source_: pass
                     elif 'pinterest.com' not in href:
                         url:
            link_selectors = ['a[data-test-idprint(f"Found potential source URL via selector '{selector}': {href="pin-closeup-link"]','div[data-test-id="}"); return href

        print("--- Could not find a reliable source URL on the PinterestCloseupDetails"] a[href^="http"]','a[data-test page via known methods. ---")
        return None
    except RequestException as e:-id="forward-button"]','a[class*="linkModule"]','a[class*="externalLink"]','div[data-test- print(f"Failed to fetch Pinterest URL {pinterest_url}: {e}"); raise ValueError(f"Could not fetch the Pinterest page (URL: {pinterest_id="pin-visual-wrapper"] a[href^="http"]']
            for selector in link_selectors:
                potential_link = soupurl}). Error: {e}")
    except Exception as e: print(.select_one(selector)
                if potential_link and potential_f"Error parsing Pinterest page {pinterest_url}: {e}"); traceback.link.get('href','').startswith('http'):
                     href = potentialprint_exc(); raise ValueError(f"An error occurred while trying to analyze_link['href']
                     if 'pinterest.com/redirect/' in the Pinterest page.")


# --- Scraping Logic Function: Using recipe-sc href:
                         try:
                             parsed_href = urlparse(hrefrapers library ---
def scrape_ingredients_with_library(url, headers)
                             final_url = parse_qs(parsed_href.query):
    """Attempts scraping using the recipe-scrapers library."""
    scraper =).get('url', [None])[0]
                             if final_url None
    try:
        print(f"--- Attempting scraping with: print(f"Resolved redirect from selector '{selector}': {final_ recipe-scrapers library for: {url} ---")
        scraper =url}"); return final_url
                         except Exception: pass
                     elif 'pinterest.com scrape_me(url) # Removed wild_mode argument
        print(f"Initialized scraper: {type(scraper).__name__}")
        if' not in href:
                         print(f"Found potential source URL via scraper:
            ingredients_list = scraper.ingredients()
            if ingredients selector '{selector}': {href}")
                         return href

        # If loop_list:
                print(f"--- recipe-scrapers successful: Found {len completes and source_url is still None
        print("--- Could not find(ingredients_list)} ingredients ---")
                cleaned_list = []; junk_keywords_library = ["advertisement","nutrition","subscribe","related","you may also like","jump to","print recipe","rate this","leave a comment","serving size","calories"," a reliable source URL on the Pinterest page via known methods. ---")
        video","instructions","notes","equipment","expert tips", "recipe developer", "return None

    except RequestException as e: print(f"Failed to fetch Pinterestphotographer"]
                for item in ingredients_list:
                    item_ URL {pinterest_url}: {e}"); raise ValueError(f"Could not fetch thelower = item.lower(); item_strip = item.strip()
                    if item_strip and not any(keyword in item_lower for keyword in junk_ Pinterest page (URL: {pinterest_url}). Error: {e}")
    except Exception as e: print(f"Error parsing Pinterest page {pinterestkeywords_library):
                         if len(item_strip.split()) >_url}: {e}"); traceback.print_exc(); raise ValueError(f 1 or any(char.isdigit() for char in item_strip):"An error occurred while trying to analyze the Pinterest page.")


# --- Scrap cleaned_list.append(item_strip)
                return "\n".ing Logic Function: Using recipe-scrapers library ---
def scrape_ingredientsjoin(cleaned_list) if cleaned_list else None
            else:_with_library(url, headers):
    """Attempts scraping using the print("--- recipe-scrapers found scraper but no ingredients method result. --- recipe-scrapers library."""
    scraper = None
    try:
        print"); return None
        else: print("--- recipe-scrapers library could not initialize scraper(f"--- Attempting scraping with recipe-scrapers library for: { object. ---"); return None
    except WebsiteNotImplementedError: print(url} ---")
        scraper = scrape_me(url) # Removedf"--- recipe-scrapers does not support this specific website: {url} ---"); return None
    except (RequestException, ConnectionError, HTTPError, Timeout) as req_err: print(f"--- Network error wild_mode argument
        print(f"Initialized scraper: {type( during recipe-scrapers processing: {req_err} ---"); return Nonescraper).__name__}")

        if scraper:
            ingredients_list =
    except Exception as e: print(f"--- Unexpected error during recipe scraper.ingredients()
            if ingredients_list:
                print(f-scrapers processing: {e}"); traceback.print_exc(); return None"--- recipe-scrapers successful: Found {len(ingredients_list)}


# --- Scraping Logic Function: Using BeautifulSoup (Fallback) ---
def ingredients ---")
                cleaned_list = []; junk_keywords_library = scrape_ingredients_with_bs(url, headers):
    """Fallback scraping ["advertisement","nutrition","subscribe","related","you may also like","jump to","print using BeautifulSoup (custom logic for NON-PINTEREST URLs)."""
     recipe","rate this","leave a comment","serving size","calories","video","instructions","print(f"--- Falling back to BeautifulSoup scraping for: {url} ---")
notes","equipment","expert tips", "recipe developer", "photographer"]
    if 'pinterest.com' in url.lower() and '/pin/'                for item in ingredients_list:
                    item_lower = item. in url.lower():
         print("BS Scraper - Error: BSlower(); item_strip = item.strip()
                    if item_strip fallback should not be called directly for Pinterest URLs.")
         return None

     and not any(keyword in item_lower for keyword in junk_keywords_library):ingredients = []; processed_elements = set()
    try:
        response
                         if len(item_strip.split()) > 1 or any = requests.get(url, headers=headers, timeout=15);(char.isdigit() for char in item_strip): cleaned_list. print(f"BS Scraper - Received status code: {response.statusappend(item_strip)
                return "\n".join(cleaned__code}"); response.raise_for_status()
        try: importlist) if cleaned_list else None
            else: print("--- recipe-scrapers lxml; parser = 'lxml'
        except ImportError: parser = found scraper but no ingredients method result. ---"); return None
        else: print 'html.parser'
        print(f"BS Scraper - Using("--- recipe-scrapers library could not initialize scraper object. ---"); return None

 HTML parser: {parser}"); soup = BeautifulSoup(response.content, parser)    except WebsiteNotImplementedError: print(f"--- recipe-scrapers does

        # --- BS Strategy 1: Specific item classes ---
        common not support this specific website: {url} ---"); return None
    except_item_classes=['wprm-recipe-ingredient','tasty-recipes-ingredient','mv-recipe-ingredient','ingredients-item-name','recipe (RequestException, ConnectionError, HTTPError, Timeout) as req_err-ingredient','ingredient']
        print("BS Scraper - Running Strategy 1: Specific Item Classes")
        # *** CORRECTED Syntax HERE ***
        for: print(f"--- Network error during recipe-scrapers processing: { class_name in common_item_classes:
            elements=soup.find_req_err} ---"); return None
    except Exception as e: printall(class_=re.compile(r'\b' + re.escape(class_name) + r'\b', re.I))
            (f"--- Unexpected error during recipe-scrapers processing: {e}");if elements:
                for el in elements:
                    el_id=str(el traceback.print_exc(); return None


# --- Scraping Logic Function: Using BeautifulSoup (Fallback) ---
def scrape_ingredients_with_bs()
                    if el_id not in processed_elements:
                        texturl, headers):
    """Fallback scraping using BeautifulSoup (custom logic for NON_parts=[part.strip() for part in el.stripped_strings];-PINTEREST URLs)."""
    print(f"--- Falling back text=' '.join(filter(None, text_parts));
                        if to BeautifulSoup scraping for: {url} ---")
    if 'pinterest. text:
                            ingredients.append(text)
                            processed_elements.add(elcom' in url.lower() and '/pin/' in url.lower():_id)
        # *** END Correction ***

        # --- BS Strategy 
         print("BS Scraper - Error: BS fallback should not be called2: Lists near headings ---
        print("BS Scraper - Running Strategy 2: Lists (ul/ol)")
        list_containers = []; potential_list_classes directly for Pinterest URLs.")
         return None

    ingredients = []; processed_elements = set()
    try:
        response = requests.get(=['ingredients','ingredient-list','recipe-ingredients']
        for list_class in potentialurl, headers=headers, timeout=15); print(f"BS_list_classes:
             found_lists=soup.find_all(['ul', Scraper - Received status code: {response.status_code}"); response.raise_for_status()
        try: import lxml; parser = 'ol'], class_=re.compile(r'\b' + re.escape(list_class) + r'\b', re.I));
 'lxml'
        except ImportError: parser = 'html.parser'
        print(f"BS Scraper - Using HTML parser: {parser             if found_lists: list_containers.extend(found_lists)}"); soup = BeautifulSoup(response.content, parser)

        # --- BS Strategy 1: Specific item classes ---
        common_item_classes=['wprm-
        headings=soup.find_all(['h2','h3','recipe-ingredient','tasty-recipes-ingredient','mv-recipe-ingredienth4','h5','strong','p'], string=re.compile(','ingredients-item-name','recipe-ingredient','ingredient']
        print("BS Scraper - Running Strategy 1: Specific Item Classes")
        r'(ingredients|for the\b|\btips\b|\bnotes# *** CORRECTED SYNTAX/INDENTATION FOR THIS BLOCK ***
        for class_\b)', re.I))
        for heading in headings:
            name in common_item_classes:
            elements = soup.find_all(classheading_text=heading.get_text(strip=True); is_relevant_heading=2 < len(heading_text) < 60_=re.compile(r'\b' + re.escape(class_; is_likely_paragraph=len(heading_text.split()) >name) + r'\b', re.I))
            if elements: 10 and '.' in heading_text
            if is_relevant_
                for el in elements:
                    el_id = str(elheading and not is_likely_paragraph:
                 is_already_added=False
)
                    if el_id not in processed_elements:
                        text                 if ingredients:
                     clean_heading = heading_text.lower()._parts=[part.strip() for part in el.stripped_strings]rstrip(':').strip()
                     clean_last_item = ingredients[-1].lower().rstrip(':').strip()
                     if clean_heading == clean
                        text=' '.join(filter(None, text_parts))
_last_item: is_already_added = True
                 if not is_already_added:
                     heading_id=str(heading)                        if text:
                            ingredients.append(text)
                            processed_
                     if heading_id not in processed_elements:
                         ingredients.elements.add(el_id)

        # --- BS Strategy 2append(heading_text)
                         processed_elements.add(heading_: Lists near headings ---
        print("BS Scraper - Running Strategy 2:id)
            list_element=heading.find_next_sibling([' Lists (ul/ol)")
        list_containers = []; potential_list_classesul','ol']);
            if list_element and len(list_element=['ingredients','ingredient-list','recipe-ingredients']
        for list_class in.find_all('li')) < 50:
                 if list potential_list_classes:
             found_lists=soup.find__element not in list_containers: list_containers.append(list_all(['ul', 'ol'], class_=re.compile(r'\belement)
            list_element_inside=heading.find_next(['' + re.escape(list_class) + r'\b', reul','ol']);
            if list_element_inside and len(list_element_inside.find_all('li')) < 50:.I))
             if found_lists:
                 list_containers.extend(found
                 if list_element_inside not in list_containers: list__lists)
        headings=soup.find_all(['h2','containers.append(list_element_inside)
        processed_lists=h3','h4','h5','strong','p'], string=reset(); unique_list_containers=[]
        for lst in list_containers.compile(r'(ingredients|for the\b|\btips\b:
            list_id=str(lst)
            if list_|\bnotes\b)', re.I))
        for heading in headingsid not in processed_lists:
                unique_list_containers.append:
            heading_text=heading.get_text(strip=True(lst)
                processed_lists.add(list_id)

); is_relevant_heading=2 < len(heading_text) < 60; is_likely_paragraph=len(heading_text.        if unique_list_containers:
             print(f"BS Scsplit()) > 10 and '.' in heading_text
            if israper - Processing {len(unique_list_containers)} unique lists.")
             for lst in unique_list_containers:
                 possible_items=_relevant_heading and not is_likely_paragraph:
                 is_lst.find_all('li')
                 for item in possible_itemsalready_added=False
                 if ingredients:
                     clean_heading =:
                     item_id=str(item)
                     if item_ heading_text.lower().rstrip(':').strip()
                     clean_lastid not in processed_elements:
                        text_parts=[part.strip_item = ingredients[-1].lower().rstrip(':').strip()
                     () for part in item.stripped_strings]; text=' '.join(filterif clean_heading == clean_last_item:
                         is_already(None,text_parts)); has_number=any(char.isdigit_added = True
                 if not is_already_added:
                     () for char in text); is_reasonable_length=0<len(heading_id=str(heading)
                     if heading_id not intext.split())<25; is_not_just_link= processed_elements:
                         ingredients.append(heading_text)
                         not item.find('a') or len(item.find_all('a'))<len(text.split())/2; looks_like_processed_elements.add(heading_id)
            list_element=heading.find_next_sibling(['ul','ol']);
            if listjunk=any(jp in text.lower() for jp in["related posts_element and len(list_element.find_all('li')) < 50:
                 if list_element not in list_containers:","you may also like","leave a reply","share this recipe","email recipe
                     list_containers.append(list_element)
            list_"])or text.lower().strip()=='ingredients'
                        if text andelement_inside=heading.find_next(['ul','ol']);
            if list_element_inside and len(list_element_inside.find is_reasonable_length and is_not_just_link and not looks_all('li')) < 50:
                 if list_element_like_junk: ingredients.append(text); processed_elements.add_inside not in list_containers:
                     list_containers.append((item_id)
                        elif text and has_number and len(list_element_inside)
        processed_lists=set(); unique_text.split())<25 and not looks_like_junk: ingredientslist_containers=[]
        for lst in list_containers:
            list.append(text); processed_elements.add(item_id)

_id=str(lst)
            if list_id not in processed        # --- BS Cleaning Stage ---
        if not ingredients: print("BS_lists:
                unique_list_containers.append(lst)
                processed_lists.add(list_id)

        if unique_ Scraper - No potential ingredients found."); return None
        print(f"BS Scraperlist_containers:
             print(f"BS Scraper - Processing { - Found {len(ingredients)} raw lines before cleaning.")
        junk_len(unique_list_containers)} unique lists.")
             for lst inphrases_exact=["scale","usm","units","ingredients"]; junk_phrases_ unique_list_containers:
                 possible_items=lst.find_contain=["cook mode","prevent your screen","nutrition information","optional","equipment","instructionsall('li')
                 for item in possible_items:
                     item","recipe notes","serving size","calories","related posts","jump to recipe","print_id=str(item)
                     if item_id not in processed recipe","pin recipe","advertisement","share this","you may also like","_elements:
                        text_parts=[part.strip() for part inleave a reply","reader interactions","expert tips","variations","storage","make item.stripped_strings]; text=' '.join(filter(None, text ahead","about","contact","partner with us","privacy policy","terms of service","careers","media kit","advertising","subscribe","newsletter","all rights reserved","back to top","more_parts)); has_number=any(char.isdigit() for char in recipes","shop","similar recipes","faq","frequently asked questions","sponsored","disclosure","affiliate links","this post may contain","skip to content","skip to main content text); is_reasonable_length=0<len(text.split())","search","log in","register","about at media","image","photo","video","recipe originally published","sign up","follow us","get the book","free trial<25; is_not_just_link=not item.find"]; junk_patterns_regex=[r'^\d+/\d+x\d('a') or len(item.find_all('a'))<len+x\d+x$',r'^\d+x$',r'(text.split())/2; looks_like_junk=any(jp in text.lower() for jp in["related posts","you may alsoclick here',r'print recipe',r'pin recipe',r'jump like","leave a reply","share this recipe","email recipe"])or text.lower().strip to recipe',r'advertisement',r'^\s*▢\s()=='ingredients'
                        if text and is_reasonable_length and is*',r'^\d+\s+comments?$',r'^\d+\s+minutes?$',r'(?i)Course:',r'(?i)Cuisine_not_just_link and not looks_like_junk:
                             ingredients.append:',r'(?i)Keyword:',r'(?i)Prep time:',(text)
                             processed_elements.add(item_id)
                        elif textr'(?i)Cook time:',r'(?i)Total time:', and has_number and len(text.split())<25 and not looks_like_junk:
                             ingredients.append(text)
                             r'(?i)Servings:',r'^\©?\s*\dprocessed_elements.add(item_id)

        # --- BS Cleaning{4}',r'(?i)facebook',r'(?i)instagram Stage ---
        if not ingredients: print("BS Scraper - No potential ingredients found.");',r'(?i)twitter',r'(?i)pinterest',r return None
        print(f"BS Scraper - Found {len('(?i)youtube',r'(?i)tiktok',r'(?ingredients)} raw lines before cleaning.")
        junk_phrases_exact=["i)read more',r'^\s*posted on',r'^\s*updatedscale","usm","units","ingredients"]; junk_phrases_contain=["cook mode","prevent your screen","nutrition information","optional","equipment","instructions","recipe notes","serving size","calories","related posts","jump to recipe","print on',r'^\s*by\s+[A-Za-z recipe","pin recipe","advertisement","share this","you may also like","\s.-]+',r'^\s*(previous|next)\s+(leave a reply","reader interactions","expert tips","variations","storage","makepost|recipe)',r'\.{3,}','★|☆',r'^(watch|view)\s+video',r'(?i)link in ahead","about","contact","partner with us","privacy policy","terms of service","careers"," bio',r'(?i)featured in']
        cleaned_ingredients=[];media kit","advertising","subscribe","newsletter","all rights reserved","back to top
        for item in ingredients:
            original_item_stripped=item.strip(); temp_item_lower=original_item_stripped.lower(); is","more recipes","shop","similar recipes","faq","frequently asked questions","_junk=False; word_count=len(original_item_strippedsponsored","disclosure","affiliate links","this post may contain","skip to content",".split())
            if word_count > 35: is_junk=True
            if not is_junk and word_count == 1 and notskip to main content","search","log in","register","about at media","image"," any(char.isdigit() for char in original_item_stripped):
                allowed_single_words = {'salt','pepper','oil','sugar','photo","video","recipe originally published","sign up","follow us","get theflour','water','milk','eggs','butter','onion','garlic'};
                if temp_item_lower not in allowed_single_words: book","free trial"]; junk_patterns_regex=[r'^\d+
                    is_junk = True
            if not is_junk and temp_item_/\d+x\d+x\d+x$',r'^\lower in junk_phrases_exact: is_junk=True
            d+x$',r'click here',r'print recipe',r'pin recipe',if not is_junk:
                for junk in junk_phrases_r'jump to recipe',r'advertisement',r'^\s*contain:
                    if junk in temp_item_lower:
                         if word_count▢\s*',r'^\d+\s+comments?$',r'^\d>4 or len(junk.split())<=2 : is_junk=+\s+minutes?$',r'(?i)Course:',r'(?True; break
            if not is_junk:
                for pattern ini)Cuisine:',r'(?i)Keyword:',r'(?i)Prep time:',r'(?i)Cook time:',r'(?i)Total time:',r'(?i)Servings:',r'^\© junk_patterns_regex:
                    if re.search(pattern, original?\s*\d{4}',r'(?i)facebook',r'(_item_stripped, re.I): is_junk=True; break?i)instagram',r'(?i)twitter',r'(?i
            if not is_junk and original_item_stripped:
                 )pinterest',r'(?i)youtube',r'(?i)tiktokif item.isupper() and 1<word_count<6: cleaned_ingredients.append(original_item_stripped.title())
                 else: cleaned',r'(?i)read more',r'^\s*posted on',r'_ingredients.append(original_item_stripped)

        seen=set(); final_^\s*updated on',r'^\s*by\s+[Aingredients=[]
        for item in cleaned_ingredients:
            item_lower-Za-z\s.-]+',r'^\s*(previous|=item.lower().strip().rstrip(':').strip()
            if itemnext)\s+(post|recipe)',r'\.{3,}','★|_lower and item_lower not in seen:
                final_ingredients.☆',r'^(watch|view)\s+video',r'(?append(item)
                seen.add(item_lower)

        i)link in bio',r'(?i)featured in']
        if not final_ingredients: print("BS Scraper - Cleaning removed all itemscleaned_ingredients=[];
        for item in ingredients:
            original_item."); return None
        print(f"BS Scraper - Returning {len(final__stripped=item.strip(); temp_item_lower=original_item_stripped.ingredients)} cleaned ingredients.")
        return "\n".join(final_ingredientslower(); is_junk=False; word_count=len(original_item_stripped.split())
            if word_count > 35)

    # --- BS Error Handling ---
    except RequestException as e:: is_junk=True
            if not is_junk and word_
        print(f"BS Scraper - Request failed for URL {urlcount == 1 and not any(char.isdigit() for char in original}: {e}")
        status_code = None
        if hasattr(e, '_item_stripped):
                allowed_single_words = {'salt','pepper','oilresponse') and e.response is not None: status_code = e.','sugar','flour','water','milk','eggs','butter','onion','response.status_code
        if isinstance(e, HTTPError) andgarlic'}
                if temp_item_lower not in allowed_single_words: status_code == 403: msg = f"Access Forbidden (
                    is_junk = True
            if not is_junk and temp_item_403). The website blocked the request."
        elif isinstance(elower in junk_phrases_exact: is_junk=True
            , HTTPError): msg = f"Website error (Status {status_code}). Pageif not is_junk:
                for junk in junk_phrases_ might be missing or restricted."
        elif isinstance(e, ConnectionError):contain:
                    if junk in temp_item_lower:
                         if word_count msg = f"Could not connect to the website at {url}."
        elif isinstance>4 or len(junk.split())<=2 : is_junk=(e, Timeout): msg = f"The request to {url} timedTrue; break
            if not is_junk:
                for pattern in out."
        else: msg = f"Could not fetch URL for scraping ({status_code if status_code else 'Network Error'})."
        raise ValueError(msg)
    except Exception as e:
        print(f"BS Scraper - Error during BeautifulSoup processing for URL {url}: { junk_patterns_regex:
                    if re.search(pattern, originale}")
        traceback.print_exc()
        raise ValueError(_item_stripped, re.I): is_junk=True; breakf"An error occurred while parsing the recipe content (fallback method).")


# --- Main API Endpoint (v3.10.5 - Final Syntax Fix) ---
            if not is_junk and original_item_stripped:
                 if item.isupper() and 1<word_count<6: cleaned_ingredients
@app.route('/api/rip-recipe', methods=['POST']).append(original_item_stripped.title())
                 else: cleaned
def rip_recipe_api():
    if not request.is__ingredients.append(original_item_stripped)

        seen=set(); final_json: return jsonify({"error": "Request format must be JSON"}), ingredients=[]
        for item in cleaned_ingredients:
            item_lower415
    data = request.get_json()
    original=item.lower().strip().rstrip(':').strip()
            if item_url = data.get('url')
    if not original_url_lower and item_lower not in seen:
                final_ingredients.: return jsonify({"error": "Missing required 'url' field in JSON requestappend(item)
                seen.add(item_lower)

        "}), 400
    if not re.match(r'^if not final_ingredients: print("BS Scraper - Cleaning removed all items."); return None
        print(f"BS Scraper - Returning {lenhttps?://', original_url): return jsonify({"error": "Invalid URL(final_ingredients)} cleaned ingredients.")
        return "\n".join(final_ingredients)

    # --- BS Error Handling (Corrected Structure) provided. Please include http:// or https://"}), 400

     ---
    except RequestException as e:
        print(f"BStarget_url = original_url # Default target
    headers = { # Scraper - Request failed for URL {url}: {e}")
        status Standard headers
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)_code = None
        if hasattr(e, 'response') and e AppleWebKit/537.36 (KHTML, like Gecko) Chrome/.response is not None: status_code = e.response.status_110.0.0.0 Safari/537.3code
        if isinstance(e, HTTPError) and status_code ==6',
        'Accept': 'text/html,application/xhtml+ 403: msg = f"Access Forbidden (403).xml,application/xml;q=0.9,image/avif The website blocked the request."
        elif isinstance(e, HTTPError):,image/webp,image/apng,*/*;q=0. msg = f"Website error (Status {status_code}). Page might be missing8,application/signed-exchange;v=b3;q=0 or restricted."
        elif isinstance(e, ConnectionError): msg = f"Could not connect to the website at {url}."
        elif isinstance(e.9',
        'Accept-Language': 'en-US,en, Timeout): msg = f"The request to {url} timed out.";q=0.9', 'Accept-Encoding': 'gzip, deflate
        else: msg = f"Could not fetch URL for scraping ({status, br', 'DNT': '1',
        'Upgrade-In_code if status_code else 'Network Error'})."
        raise ValueError(msg)
    except Exception as e:
        print(f"secure-Requests': '1', 'Referer': 'https://www.BS Scraper - Error during BeautifulSoup processing for URL {url}: {e}")google.com/',
        'Sec-Fetch-Dest': 'document', 'Sec-
        traceback.print_exc()
        raise ValueError(f"Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'crossAn error occurred while parsing the recipe content (fallback method).")


# ----site',
        'Sec-Fetch-User': '?1', ' Main API Endpoint (v3.10.5 - Final Syntax Check) ---
Sec-Ch-Ua': '"Chromium";v="110@app.route('/api/rip-recipe', methods=['POST'])
", "Not A(Brand";v="24", "Google Chrome";def rip_recipe_api():
    if not request.is_json: return jsonify({"error": "Request format must be JSON"}), 4v="110"',
        'Sec-Ch-Ua-15
    data = request.get_json()
    original_url = data.get('url')
    if not original_url:Mobile': '?0', 'Sec-Ch-Ua-Platform': '" return jsonify({"error": "Missing required 'url' field in JSON request"}), 400
    if not re.match(r'^https?://', original_url): return jsonify({"error": "Invalid URL providedWindows"'
    }

    try:
        print(f"Received. Please include http:// or https://"}), 400

    target_url = original_url # Default target
    headers = { # Standard URL for processing: {original_url}")
        is_pinterest = ' headers
        'User-Agent': 'Mozilla/5.0 (Windowspinterest.com' in original_url.lower() and '/pin/' in NT 10.0; Win64; x64) AppleWebKit original_url.lower()
        ingredients_text = None

        # Determine target URL
        if is_pinterest:
            print("Pinterest URL detected. Attempt/537.36 (KHTML, like Gecko) Chrome/1ing to find source URL...")
            source_url = extract_source_url_from_pinterest(original_url, headers)
            if source_url:
                 target_url = source_url
                 print(10.0.0.0 Safari/537.36f"Found source URL, proceeding to scrape: {target_url}")
            else:
                 print("Could not find source URL on Pinterest page.',
        'Accept': 'text/html,application/xhtml+xml Aborting.")
                 raise ValueError("Could not find the source recipe link on,application/xml;q=0.9,image/avif, the Pinterest page. Please provide the direct recipe URL.")
        # else: # Noimage/webp,image/apng,*/*;q=0.8 need for else, target_url is already original_url

        target_info_for_frontend = target_url

        # Scrape the final target,application/signed-exchange;v=b3;q=0. URL
        print(f"Attempting scrape on final target: {target9',
        'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate,_url}")
        ingredients_text = scrape_ingredients_with_library br', 'DNT': '1',
        'Upgrade-Insecure(target_url, headers)

        # Fallback to BeautifulSoup (only if not Pinterest-Requests': '1', 'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'document', ')
        if ingredients_text is None:
            print("Library scraping failed or unsupportedSec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site':, trying BeautifulSoup fallback...")
            if 'pinterest.com' in target_url.lower 'cross-site',
        'Sec-Fetch-User': '?1() and '/pin/' in target_url.lower():
                 print("BS', 'Sec-Ch-Ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google fallback skipped for Pinterest URL.")
            else:
                 ingredients_text = scrape_ingredients_with_bs(target_url, headers)

         Chrome";v="110"',
        'Sec-Ch-U# Process results
        if ingredients_text:
            print("--- Successfully obtained ingredients ---")
            return jsonify({
                "ingredients": ingredients_a-Mobile': '?0', 'Sec-Ch-Ua-Platformtext,
                "source_url_scraped": target_info_': '"Windows"'
    }

    try:
        print(ffor_frontend
            })
        else:
            print(f"--- All"Received URL for processing: {original_url}")
        is_pinterest scraping methods failed for {target_info_for_frontend} ---")
 = 'pinterest.com' in original_url.lower() and '/pin            error_msg = f"Could not automatically find ingredients for the target URL: {target_info_for_frontend}. The site structure may be unsupported/' in original_url.lower()
        ingredients_text = None

 or blocked."
            return jsonify({"error": error_msg}), 4        # Determine target URL
        if is_pinterest:
            print("Pinterest URL detected00

    except ValueError as e:
        print(f"--- Handled. Attempting to find source URL...")
            source_url = extract_ Value Error: {e} ---")
        return jsonify({"error": strsource_url_from_pinterest(original_url, headers)
            if source_url:
                 target_url = source_url # Sc(e)}), 400
    except Exception as e:
        print(f"--- Unexpected Server Error in API handler: {e}rape the external link if found
                 print(f"Found source URL, ---")
        traceback.print_exc()
        return jsonify({" proceeding to scrape: {target_url}")
            else:
                 # If no external link FOUND -> ERROR
                 print("Could not find source URL on Pinterest pageerror": "An unexpected server error occurred."}), 500


# --- Run the App ---
if __name__ == '__main__':
    print("----------------. Aborting.")
                 raise ValueError("Could not find the source recipe link---------------------------------------")
    print("Starting Flask DEVELOPMENT server (for local testing)...")
 on the Pinterest page. Please provide the direct recipe URL.")
        else:    print("DO NOT use this server for production deployment.")
    print("-------------------------------------------------------")
    local_port = 5000
            target_url = original_url # Not Pinterest

        target_info_for_frontend = target_url # The URL we will actually attempt to scrape


    print(f"Local access: http://127.0.0.1:{local_port}")
    try:
         app.run(        # Scrape the final target URL
        print(f"Attempting scrape on finaldebug=True, host='127.0.0.1', target: {target_url}")
        ingredients_text = scrape_ingredients port=local_port)
    except OSError as e:
         print(f_with_library(target_url, headers)

        # Fallback to BeautifulSoup (only if not Pinterest)
        if ingredients_text is None"\nERROR: Could not start development server on port {local_port}."):
            print("Library scraping failed or unsupported, trying BeautifulSoup fallback...")
            
         if "address already in use" in str(e).lower():if 'pinterest.com' in target_url.lower() and '/pin
              print("       Another application might be using this port.")
         print/' in target_url.lower():
                 print("BS fallback skipped for Pinterest("       Try stopping the other application or choosing a different port.")
