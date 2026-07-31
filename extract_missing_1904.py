import os
import glob
import json
import time
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image

# Initialize Gemini Client (uses GEMINI_API_KEY from environment)
client = genai.Client()

def extract_page_with_retry(image_path, max_retries=5, retry_delay=5):
    """
    Extracts catalog entries from an image with built-in exponential/delay retry 
    logic to handle temporary server spikes (503) and rate limits (429).
    """
    prompt = """
    You are an expert archivist. Analyze this page scan from the 1904 Gerardos Bookstore catalog.
    Extract all catalog items into a JSON array of objects.
    
    CRITICAL RULE FOR CURRENCY:
    Extract currency ONLY if an explicit currency symbol or abbreviation (like γρ., παρ.) 
    is physically printed next to the price or header. 
    If only numbers or dashes (e.g., 2.—, 3.20, 7.20) are printed, leave 'currency' as null/blank. 
    DO NOT default to or infer 'drachmas' or 'Δρχ.'.

    Required JSON Keys for each item object:
    - catalog_year: 1904
    - source_file: (string)
    - main_category: (string in original Greek if present)
    - main_category_english: (string translation)
    - subcategory_or_series: (string or null)
    - author: (string in Greek or null)
    - author_transcribed: (string or null)
    - title: (string in original Greek)
    - title_english: (string translation)
    - pages_format: (string or null, e.g. 8vo, σ. 120)
    - price: (string, e.g. "2.—", "3.20")
    - currency: (string or null)
    - notes: (string or null)
    """

    for attempt in range(1, max_retries + 1):
        try:
            img = Image.open(image_path)
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=[img, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            return json.loads(response.text.strip())
            
        except Exception as e:
            print(f"⚠️ [Attempt {attempt}/{max_retries}] Error processing {image_path}: {e}")
            if attempt < max_retries:
                wait_time = retry_delay * attempt  # Gradual backoff (5s, 10s, 15s...)
                print(f"   Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed {image_path} after {max_retries} attempts. Skipping file.")
                return []

def main():
    image_folder = "images_1904" 
    all_images = sorted(glob.glob(f"{image_folder}/IMG_*.jpeg") + glob.glob(f"{image_folder}/IMG_*.jpg"))
    
    # Target full missing range: IMG_1359 through IMG_1441
    target_files = []
    for img in all_images:
        num_str = ''.join(filter(str.isdigit, os.path.basename(img)))
        if num_str and 1359 <= int(num_str) <= 1441:
            target_files.append(img)

    print(f"🚀 Found {len(target_files)} target images to extract from scratch (IMG_1359 to IMG_1441).")

    records = []
    for index, img_path in enumerate(target_files, start=1):
        print(f"[{index}/{len(target_files)}] Extracting: {img_path}...")
        
        page_records = extract_page_with_retry(img_path)
        for r in page_records:
            r['source_file'] = os.path.basename(img_path)
        records.extend(page_records)
        
        # Brief 1.5s pause between standard requests to avoid rate limits
        time.sleep(1.5)

    df_part1 = pd.DataFrame(records)
    df_part1.to_csv("catalog_1904_part1.csv", index=False)
    print("\n✅ Extraction finished from scratch! Saved output to 'catalog_1904_part1.csv'.")

if __name__ == "__main__":
    main()