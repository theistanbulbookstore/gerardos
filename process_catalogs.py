import os
import pandas as pd

def format_price_display(row):
    """
    Standardizes price display across both 1895 and 1904 catalogs.
    Converts 1904 dot-dash notation (1.20 -> 1 γρ. 20 παρ. | 2.— -> 2 γρ.).
    Preserves 1895 explicit units (1 γρ. | 20 παρ.).
    """
    price = str(row['price']).strip() if pd.notna(row['price']) else ''
    currency = str(row['currency']).strip() if pd.notna(row['currency']) and str(row['currency']) != 'nan' else ''
    
    if not price:
        return ""

    # If currency is non-Ottoman (e.g., French Francs 'Fr.'), preserve as-is
    if currency in ['Fr.', 'Fr', 'franc']:
        return f"{price} {currency}"

    # Handle 1904 Dot Notation (e.g. '2.—', '1.20', '0.10')
    if '.—' in price or '.-' in price:
        main_unit = price.split('.')[0]
        return f"{main_unit} γρ."
    
    if '.' in price:
        parts = price.split('.')
        kurus, paras = parts[0], parts[1]
        
        if kurus in ['0', '']:
            return f"{paras} παρ."
        else:
            return f"{kurus} γρ. {paras} παρ."

    # Handle 1895 & Standardized Entries (already have explicit price + currency)
    if currency:
        return f"{price} {currency}"
    
    # Fallback default if only a whole number exists
    return f"{price} γρ."

def build_clean_master():
    print("--- Starting Master Catalog Consolidation & Price Normalization ---")
    
    # 1. Load 1904 Part 2 (IMG_1442+)
    if not os.path.exists("catalog_1904_extracted.csv"):
        print("❌ Error: catalog_1904_extracted.csv missing!")
        return
    df_1904_part2 = pd.read_csv("catalog_1904_extracted.csv")
    print(f"Loaded 1904 Part 2 ({len(df_1904_part2)} rows).")

    # 2. Load 1904 Part 1 (IMG_1359–1441)
    if os.path.exists("catalog_1904_part1.csv"):
        df_1904_part1 = pd.read_csv("catalog_1904_part1.csv")
        print(f"Loaded 1904 Part 1 ({len(df_1904_part1)} rows).")
        df_1904_complete = pd.concat([df_1904_part1, df_1904_part2], ignore_index=True)
        df_1904_complete = df_1904_complete.sort_values(by="source_file")
    else:
        print("⚠️ Warning: catalog_1904_part1.csv not found. Using Part 2 only.")
        df_1904_complete = df_1904_part2

    # Save complete 1904 dataset
    df_1904_complete.to_csv("catalog_1904_complete.csv", index=False)

    # 3. Load 1895 Catalog
    frames = []
    if os.path.exists("catalog_1895_extracted.csv"):
        df_1895 = pd.read_csv("catalog_1895_extracted.csv")
        print(f"Loaded 1895 catalog ({len(df_1895)} rows).")
        frames.append(df_1895)

    frames.append(df_1904_complete)

    # 4. Generate Combined Master CSV
    master_df = pd.concat(frames, ignore_index=True)

    # 5. Apply Unified Price Display Column
    master_df['price_display'] = master_df.apply(format_price_display, axis=1)

    master_df.to_csv("master_catalogs_combined.csv", index=False)
    
    print("\n✅ SUCCESS!")
    print(f"Generated 'master_catalogs_combined.csv' with {len(master_df)} total records.")
    print("\nSample Output preview:")
    print(master_df[['catalog_year', 'title', 'price', 'currency', 'price_display']].dropna(subset=['price']).head(10))

if __name__ == "__main__":
    build_clean_master()