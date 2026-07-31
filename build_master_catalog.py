import os
import pandas as pd

# 1. Clean existing 1904 (IMG_1442+) dataset
df_1904_part2 = pd.read_csv("catalog_1904_extracted.csv")
phantom_currencies = ['Δρχ.', 'Δρ.', 'drachmas', 'Δραχμαί', 'δρχ.', '₯']
df_1904_part2.loc[df_1904_part2['currency'].isin(phantom_currencies), 'currency'] = pd.NA

# 2. Load newly extracted Part 1 (IMG_1359–1441) once run
if os.path.exists("catalog_1904_part1.csv"):
    df_1904_part1 = pd.read_csv("catalog_1904_part1.csv")
    df_1904_full = pd.concat([df_1904_part1, df_1904_part2], ignore_index=True)
else:
    df_1904_full = df_1904_part2

# 3. Load 1895 dataset
df_1895 = pd.read_csv("catalog_1895_extracted.csv")

# 4. Export final unified master CSV
master_df = pd.concat([df_1895, df_1904_full], ignore_index=True)
master_df.to_csv("master_catalogs_combined.csv", index=False)
print(f"Master dataset built successfully! Total records: {len(master_df)}")