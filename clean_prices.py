import re
import pandas as pd


def parse_price(row):
    price_disp = str(row.get('price_display', '') or '').strip()
    price_val = str(row.get('price', '') or '').strip()
    curr = str(row.get('currency', '') or '').strip()

    # 1. Pick primary string (do not concatenate duplicate values!)
    raw = price_disp if (price_disp and price_disp != 'nan') else price_val
    if not raw or raw in ['—', 'nan', 'None']:
        raw = price_val
    if not raw or raw in ['—', 'nan', 'None']:
        return pd.Series([None, None, '—'])

    # 2. Strip hallucinated Drachma labels
    raw_clean = re.sub(
        r'(?:Δρχ|Δρ|drachmas|Δραχμαί|δρχ|₯)', '', raw, flags=re.IGNORECASE
    ).strip()

    if not raw_clean or raw_clean in ['—', 'nan', 'None']:
        return pd.Series([None, None, '—'])

    grosia = 0.0
    paras = 0.0

    # 3. Match standard decimals (e.g., 1.20 -> 1 grosi, 20 paras)
    decimal_match = re.match(r'^(\d+)[\.,](\d+)$', raw_clean)
    if decimal_match:
        grosia = float(decimal_match.group(1))
        p_str = decimal_match.group(2)
        paras = float(p_str + '0' if len(p_str) == 1 else p_str)
    else:
        nums = [float(n) for n in re.findall(r'\d+', raw_clean)]

        has_paras = bool(
            re.search(r'παρ|π', raw_clean, re.IGNORECASE)
            or re.search(r'παρ|π', curr, re.IGNORECASE)
        )
        has_grosia = bool(
            re.search(r'γρ', raw_clean, re.IGNORECASE)
            or re.search(r'γρ', curr, re.IGNORECASE)
        )

        # 4. Handle "1 γρ. 20 παρ." strings
        if len(nums) == 2 and has_paras and has_grosia:
            grosia = nums[0]
            paras = nums[1]
        # 5. Handle single numbers (paras vs grosia)
        elif len(nums) == 1:
            if has_paras and not has_grosia:
                paras = nums[0]
            else:
                grosia = nums[0]
        elif len(nums) == 2 and not has_grosia and not has_paras:
            grosia = nums[0]
            paras = nums[1]
        else:
            return pd.Series([None, None, '—'])

    total_grosia = round(grosia + (paras / 40.0), 3)
    total_paras = int((grosia * 40) + paras)

    int_g = int(grosia)
    int_p = int(paras)

    if int_g > 0 and int_p > 0:
        clean_display = f'{int_g} γρ. {int_p} παρ.'
    elif int_g > 0:
        clean_display = f'{int_g} γρ.'
    elif int_p > 0:
        clean_display = f'{int_p} παρ.'
    else:
        clean_display = '—'

    return pd.Series([total_grosia, total_paras, clean_display])


# Load data and run parser
df = pd.read_csv('master_catalogs_combined.csv')
df[['price_in_grosia', 'price_in_paras', 'price_clean_display']] = df.apply(
    parse_price, axis=1
)
df.to_csv('catalog_analytics.csv', index=False)

print('✅ Fixed dataset generated successfully in catalog_analytics.csv!')
print(f'Total rows parsed: {df["price_in_grosia"].notna().sum()} / {len(df)}')