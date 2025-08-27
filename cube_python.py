import pandas as pd
import numpy as np
import json
import random

# Load data
cards = pd.read_json('oracle-cards.json')

# Declare labels for parsing
labels = [
    "oracle_id",
    "name",
    "lang", 
    "cmc",
    "color_identity", 
    "legalities",
    "reserved",
    "rarity",
    "prices"
]

# Filter for Vintage-legal cards
cards = cards[cards['legalities'].apply(lambda x: x.get('vintage') == 'legal')]

# Filter for cards under $1
cards = cards[cards['prices'].apply(lambda p: float(p.get('usd') or 0) < 1.00)]

# Add 'color_group' column based on color_identity
def get_color_group(ci):
    if not ci:
        return 'colorless'
    elif len(ci) == 1:
        return {
            'R': 'red',
            'G': 'green',
            'W': 'white',
            'B': 'black',
            'U': 'blue'
        }.get(ci[0], 'other')
    else:
        return 'multicolor'

cards['color_group'] = cards['color_identity'].apply(get_color_group)

# Add helper columns
cards['is_creature'] = cards['type_line'].str.contains('Creature', na=False)
cards['is_land'] = cards['type_line'].str.contains('Land', na=False)
cards['cmc_2'] = cards['cmc'] == 2

# Prepare final cube (excluding lands for now)
cube_list = []

color_groups = ['red', 'green', 'white', 'black', 'blue', 'multicolor', 'colorless']

for color in color_groups:
    subset = cards[cards['color_group'] == color]
    
    if len(subset) < 105:
        print(f"⚠️ Not enough cards in group {color}, found {len(subset)}")
        sample_size = len(subset)
    else:
        sample_size = 105

    num_creatures = int(sample_size * 0.75)
    num_noncreatures = sample_size - num_creatures

    # Creatures
    creatures = subset[subset['is_creature'] == True]
    cmc2_creatures = creatures[creatures['cmc_2'] == True]
    other_creatures = creatures[creatures['cmc_2'] == False]

    num_cmc2 = int(num_creatures * 0.5)
    num_other_cmc = num_creatures - num_cmc2

    creature_sample = pd.concat([
        cmc2_creatures.sample(n=min(num_cmc2, len(cmc2_creatures)), replace=False),
        other_creatures.sample(n=min(num_other_cmc, len(other_creatures)), replace=False)
    ])

    # Non-creatures (not creatures and not lands)
    noncreatures = subset[(subset['is_creature'] == False) & (subset['is_land'] == False)]
    noncreature_sample = noncreatures.sample(n=min(num_noncreatures, len(noncreatures)), replace=False)

    group_sample = pd.concat([creature_sample, noncreature_sample])
    
    cube_list.append(group_sample)

# Combine all non-land cards
nonland_cube = pd.concat(cube_list)

# Now sample 65 lands from all vintage-legal lands
land_pool = cards[cards['is_land'] == True]
land_sample = land_pool.sample(n=min(65, len(land_pool)), replace=False)

# Final cube
cube = pd.concat([nonland_cube, land_sample]).sample(frac=1).reset_index(drop=True)

# Save to CSV
cube.to_csv('cube.csv', index=False, columns=labels)

print(f"✅ Cube generated with {len(cube)} cards.")
