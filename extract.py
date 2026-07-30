import os
import json
import glob
import time
import pandas as pd
from google import genai
from google.genai import types

# Configuration
API_KEY = "AQ.Ab8RN6KfFY1m8tcLPzPj_guyZDU5fU2EdgB3pN3D9O9OHQI-FQ"
MODEL_NAME = "gemini-flash-latest"

client = genai.Client(api_key=API_KEY)

# Global Active State Tracker
active_state = {
    "main_category": "N/A",
    "main_category_english": "N/A",
    "subcategory_or_series": "N/A",
    "author": "N/A",
    "author_transcribed": "N/A"
}

# Only processing 1895 and 1904
FOLDERS = ["gerardos 1895", "gerardos 1904"]
MASTER_CSV = "master_catalogs_combined.csv"

def extract_page_data(image_path, year, max_retries=5):
    global active_state
    
    prompt = f"""
    You are an expert archivist extracting structured catalog data from this page image.

    === CONTEXT FROM PREVIOUS PAGE (USE AS FALLBACK IF NOT PRINTED ON THIS PAGE) ===
    - Active Main Category: "{active_state['main_category']}" ({active_state['main_category_english']})
    - Active Subcategory / Series: "{active_state['subcategory_or_series']}"
    - Active Author: "{active_state['author']}" ({active_state['author_transcribed']})

    === EXTRACTION RULES ===
    1. COMPLETE EXTRACTION: Extract EVERY single book item or entry visible on this page. Do not summarize or combine entries.
    2. MAIN CATEGORY: If a clear header appears (e.g., 'ΚΛΑΣΙΚΟΙ ΕΛΛΗΝΕΣ'), update 'main_category' and provide 'main_category_english'. If NO new header is printed, use the Active Main Category context above.
    3. SUBCATEGORY / SERIES: Extract parent collections or publisher series in 'subcategory_or_series'. If none, use the Active Subcategory context above (or set to null if standalone).
    4. AUTHOR & TRANSCRIBED AUTHOR: Extract the author in 'author'. In 'author_transcribed', provide the Latin/English transliteration (e.g. 'Πλούταρχος' -> 'Plutarch', 'Σοφοκλῆς' -> 'Sophocles').
    5. TITLE & TRANSLATION: Extract the original title in 'title'. In 'title_english', provide an accurate English translation of the title.
    6. FORMAT & PRICE: Extract volume/pages in 'pages_format', numerical price in 'price', and currency symbol/text in 'currency'.

    Respond STRICTLY with a JSON array of objects with these exact keys:
    [
      {{
        "catalog_year": "{year}",
        "source_file": "{os.path.basename(image_path)}",
        "main_category": "string",
        "main_category_english": "string",
        "subcategory_or_series": "string or null",
        "author": "string",
        "author_transcribed": "string",
        "title": "string",
        "title_english": "string",
        "pages_format": "string",
        "price": "string",
        "currency": "string",
        "notes": "string"
      }}
    ]
    """

    for attempt in range(1, max_retries + 1):
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[image_part, prompt]
            )
            
            # Clean response text
            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(text)
            
            # Update running state using the last item extracted on this page
            if data and isinstance(data, list):
                for item in reversed(data):
                    if item.get("main_category") and str(item["main_category"]).lower() != "null":
                        active_state["main_category"] = item["main_category"]
                        active_state["main_category_english"] = item.get("main_category_english", "N/A")
                        break
                for item in reversed(data):
                    if item.get("subcategory_or_series") and str(item["subcategory_or_series"]).lower() != "null":
                        active_state["subcategory_or_series"] = item["subcategory_or_series"]
                        break
                for item in reversed(data):
                    if item.get("author") and str(item["author"]).lower() != "null":
                        active_state["author"] = item["author"]
                        active_state["author_transcribed"] = item.get("author_transcribed", "N/A")
                        break
                        
            return data if isinstance(data, list) else []

        except Exception as e:
            err_str = str(e)
            if "503" in err_str or "UNAVAILABLE" in err_str:
                print(f"  ⚠️ 503 Busy Server on {os.path.basename(image_path)} (Attempt {attempt}/{max_retries}). Retrying in 4s...")
                time.sleep(4)
            else:
                print(f"  ❌ Error processing {os.path.basename(image_path)}: {e}")
                return []
                
    print(f"❌ Failed after {max_retries} attempts: {image_path}")
    return []

def main():
    all_extracted_rows = []

    for folder in FOLDERS:
        if not os.path.exists(folder):
            print(f"⚠️ Folder '{folder}' not found. Skipping...")
            continue
        
        # Reset state memory per folder/catalog year
        global active_state
        active_state = {
            "main_category": "N/A", 
            "main_category_english": "N/A", 
            "subcategory_or_series": "N/A", 
            "author": "N/A", 
            "author_transcribed": "N/A"
        }

        year = folder.replace("gerardos ", "").strip()
        
        # Case-insensitive image discovery (.jpg, .JPG, .jpeg, .png)
        image_files = sorted(
            [f for f in glob.glob(os.path.join(folder, "*")) 
             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        )
        
        print(f"\n--- Starting Extraction for {folder} ({len(image_files)} pages) ---")
        folder_rows = []
        
        for img in image_files:
            print(f"Processing: {img}...")
            page_data = extract_page_data(img, year)
            print(f"   ↳ Extracted {len(page_data)} items.")
            folder_rows.extend(page_data)
            all_extracted_rows.extend(page_data)

        # Save individual year CSV with Excel-friendly UTF-8 BOM encoding
        if folder_rows:
            df_year = pd.DataFrame(folder_rows)
            year_csv = f"catalog_{year}_extracted.csv"
            df_year.to_csv(year_csv, index=False, encoding='utf-8-sig')
            print(f"✅ Saved {len(df_year)} items to {year_csv}")

    # Save master combined CSV
    if all_extracted_rows:
        df_master = pd.DataFrame(all_extracted_rows)
        df_master.to_csv(MASTER_CSV, index=False, encoding='utf-8-sig')
        print(f"\n🎉 SUCCESS! All catalogs compiled into '{MASTER_CSV}' with {len(df_master)} total rows.")

if __name__ == "__main__":
    main()