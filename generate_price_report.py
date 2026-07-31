import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set visual style
sns.set_theme(style='whitegrid')
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.size': 10})

# 1. Load Data
df = pd.read_csv('catalog_analytics.csv')
df_clean = df.dropna(subset=['price_in_grosia']).copy()

print(f'Loaded {len(df_clean)} records with valid prices.')

# --- ANALYSIS 1: Overall Genre Statistics ---
genre_summary = (
    df_clean.groupby('main_category_english')
    .agg(
        total_books=('price_in_grosia', 'count'),
        mean_price_grosia=('price_in_grosia', 'mean'),
        median_price_grosia=('price_in_grosia', 'median'),
        min_price_grosia=('price_in_grosia', 'min'),
        max_price_grosia=('price_in_grosia', 'max'),
    )
    .reset_index()
)

# Filter categories with at least 5 books for reliable averages
genre_filtered = genre_summary[genre_summary['total_books'] >= 5].sort_values(
    by='mean_price_grosia', ascending=False
)
genre_filtered.to_csv('analytics_genre_summary.csv', index=False)

top_expensive_genres = genre_filtered.head(15)
top_cheapest_genres = genre_filtered.tail(15).sort_values(
    by='mean_price_grosia', ascending=True
)

# --- ANALYSIS 2: Top 50 Most Expensive & 50 Cheapest Books ---
cols_to_export = [
    'catalog_year',
    'main_category_english',
    'author',
    'title',
    'price_clean_display',
    'price_in_grosia',
    'price_in_paras',
]

top_50_expensive = df_clean.sort_values(
    by=['price_in_grosia', 'title'], ascending=[False, True]
).head(50)[cols_to_export]
top_50_cheapest = df_clean.sort_values(
    by=['price_in_grosia', 'title'], ascending=[True, True]
).head(50)[cols_to_export]

top_50_expensive.to_csv('analytics_top_50_expensive_books.csv', index=False)
top_50_cheapest.to_csv('analytics_top_50_cheapest_books.csv', index=False)

# --- ANALYSIS 3: 1895 vs 1904 Price Comparison ---
year_summary = (
    df_clean.groupby('catalog_year')['price_in_grosia']
    .agg(['count', 'mean', 'median', 'min', 'max'])
    .reset_index()
)
year_summary.to_csv('analytics_year_comparison.csv', index=False)

# --- VISUALIZATION 1: Genre Comparison Bar Charts ---
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

sns.barplot(
    data=top_expensive_genres,
    y='main_category_english',
    x='mean_price_grosia',
    ax=axes[0],
    palette='Reds_r',
)
axes[0].set_title(
    'Top 15 Most Expensive Genres (Avg. Grosia)', fontsize=12, fontweight='bold'
)
axes[0].set_xlabel('Average Price (Grosia)')
axes[0].set_ylabel('')

sns.barplot(
    data=top_cheapest_genres,
    y='main_category_english',
    x='mean_price_grosia',
    ax=axes[1],
    palette='Blues_r',
)
axes[1].set_title(
    'Top 15 Cheapest Genres (Avg. Grosia)', fontsize=12, fontweight='bold'
)
axes[1].set_xlabel('Average Price (Grosia)')
axes[1].set_ylabel('')

plt.tight_layout()
plt.savefig('genre_price_comparison.png', dpi=300)
plt.close()

# --- VISUALIZATION 2: Price Distribution by Catalog Year (1895 vs 1904) ---
df_years = df_clean[df_clean['catalog_year'].isin([1895, 1904])].copy()

plt.figure(figsize=(10, 6))
sns.boxplot(
    data=df_years,
    x='catalog_year',
    y='price_in_grosia',
    palette=['#3498db', '#e74c3c'],
    showfliers=False,
)
sns.stripplot(
    data=df_years,
    x='catalog_year',
    y='price_in_grosia',
    color='black',
    alpha=0.15,
    jitter=0.2,
    size=3,
)

plt.yscale('log')
plt.title(
    'Book Price Distribution: 1895 vs 1904 Catalog (Log Scale)',
    fontsize=13,
    fontweight='bold',
)
plt.xlabel('Catalog Year', fontsize=11)
plt.ylabel('Price in Grosia (Log Scale)', fontsize=11)
plt.grid(True, which='both', ls='--', linewidth=0.5)

plt.tight_layout()
plt.savefig('price_distribution_1895_vs_1904.png', dpi=300)
plt.close()

print('✅ Price analytics report and visual charts created successfully!')