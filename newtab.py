import pandas as pd
import json
import re

# 1. Load your CSV file
df = pd.read_csv('master_catalogs_combined.csv')

# 2. Function to clean and format subcategories
def clean_subcategory(text):
    if pd.isna(text) or not str(text).strip():
        return "General / Uncategorized"
    
    text = str(text).strip()

    # Remove Roman numerals (e.g., V. I., IV., III, etc.)
    text = re.sub(r'\b(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b\.?', '', text, flags=re.IGNORECASE)

    # Remove standalone numbers and digits (e.g., 1., 2, etc.)
    text = re.sub(r'\b\d+\b\.?', '', text)

    # Clean up lingering punctuation and extra spaces
    text = re.sub(r'[\.\,\-\–\:]+', ' ', text)
    text = ' '.join(text.split())

    # Format from ALL CAPS to clean Title Case
    if text:
        text = text.title()
    else:
        text = "General / Uncategorized"

    return text

# 3. Apply cleaning to your subcategory column
df['clean_subcategory'] = df['subcategory_or_series'].apply(clean_subcategory)

# 4. Group and count records based on your exact column names
grouped = df.groupby(['main_category_english', 'clean_subcategory']).size().reset_index(name='count')
grouped = grouped.sort_values(by=['main_category_english', 'count'], ascending=[True, False])

# 5. Export to CSV (Your Summary File)
grouped.to_csv('genres_summary.csv', index=False, encoding='utf-8')

# 6. Export to JSON (For your web interface)
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

print("✅ Success! 'genres_summary.csv' and 'genres_taxonomy.json' have been created.")