import pandas as pd
import json
import re
from googletrans import Translator

# 1. Load your CSV file
print("📂 Loading master_catalogs_combined.csv...")
df = pd.read_csv('master_catalogs_combined.csv')

# Initialize the Google Translator
translator = Translator()

def translate_and_clean_subcategory(text):
    if pd.isna(text) or not str(text).strip():
        return "General / Uncategorized"
    
    text = str(text).strip()

    # Step 1: Remove Roman numerals (e.g., V. I., IV., III, etc.)
    text = re.sub(r'\b(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b\.?', '', text, flags=re.IGNORECASE)

    # Step 2: Remove standalone numbers and digits (e.g., 1., 2, etc.)
    text = re.sub(r'\b\d+\b\.?', '', text)

    # Step 3: Clean up lingering punctuation and extra spaces before translating
    text = re.sub(r'[\.\,\-\–\:]+', ' ', text)
    text = ' '.join(text.split())

    if not text:
        return "General / Uncategorized"

    # Step 4: Translate from Greek to English using Google Translate
    try:
        translation = translator.translate(text, src='el', dest='en')
        translated_text = translation.text
    except Exception as e:
        # Fallback if translation fails temporarily
        translated_text = text

    # Step 5: Format to clean Title Case
    translated_text = translated_text.title()
    
    return translated_text

print("🌍 Translating and cleaning subcategories via Google Translate (this may take a moment)...")

# Apply to your dataframe column
df['clean_subcategory'] = df['subcategory_or_series'].apply(translate_and_clean_subcategory)

# 3. Group and count records
grouped = df.groupby(['main_category_english', 'clean_subcategory']).size().reset_index(name='count')
grouped = grouped.sort_values(by=['main_category_english', 'count'], ascending=[True, False])

# 4. Export to CSV
grouped.to_csv('genres_summary.csv', index=False, encoding='utf-8')

# 5. Export to JSON for your web interface
taxonomy = {}
for _, row in grouped.iterrows():
    cat = row['main_category_english']
    sub = row['clean_subcategory']
    cnt = int(row['count'])
    
    if cat not in taxonomy:
        taxonomy[cat] = {"total_count": 0, "subcategories": []}
    
    taxonomy[cat]["total_count"] += cnt
    taxonomy[cat]["subcategories"].append({"name": sub, "count": cnt})

with open('genres_taxonomy.json', 'w', encoding='utf-8') as f:
    json.dump(taxonomy, f, ensure_ascii=False, indent=2)

print("✅ Success! 'genres_summary.csv' and 'genres_taxonomy.json' have been updated with translated, clean subcategories.")