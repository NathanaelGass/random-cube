import pandas as pd
import numpy as np
import json
import random
import re
import sys

# Declare variables
MONO_COLOR_AMOUNT = 105
DUAL_COLOR_AMOUNT = 8
TRI_COLOR_AMOUNT = 2
FIVE_COLOR_AMOUNT = 5
LAND_AMOUNT = 65

INTERACTION_MINIMUM = 17 # This is per color

HIGHEST_PRICE = 1.00

EXCLUDE_PLANESWALKERS = True

CREATURE_RATIO = 0.75
TWO_DROP_RATIO =  0.5

run_default = input("Welcome to the random cube creator. Run with default color amounts and ratios? y/n:").strip().lower()

if(run_default == 'n'):
    MONO_COLOR_AMOUNT = int(input("Enter number of cards per single color:"))

    DUAL_COLOR_AMOUNT = int(input("Enter number of cards per dual color pair:"))

    TRI_COLOR_AMOUNT = int(input("Enter number of cards per tri color combination:"))

    INTERACTION_MINIMUM = int(input("Enter minimum amount of interaction spells per color:"))

    LAND_AMOUNT = int(input("Enter number of lands:"))

    HIGHEST_PRICE = float(input("Enter highest cost of card in USD as a two point decimal (ie, 1.00):"))

    CREATURE_RATIO = float(input("Enter the ratio of creatures you want as a decimal between 0.00 and 1.00 (ie, 0.50):"))

    TWO_DROP_RATIO = float(input("Enter the ratio of creatures you want to be two drops as a decimal between 0.00 and 1.00 (ie, 0.50):"))    

    response = input("Exclude planeswalkers? y/n").strip().lower()
    EXCLUDE_PLANESWALKERS = response == 'y'

print("Loading cards...")

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

# Remove bad sets
sets_to_exclude = [
    "who",
    "pip",
    "bot",
    "rex",
    "acr",
    "spm",
    "unf",
    "ltc",
    "sld"
]

print("Filtering cards by legality...")
cards = cards[cards['legalities'].apply(lambda x: x.get('vintage') == 'legal')]

print("Filtering cards by supertype...")
cards = cards[~cards['type_line'].str.contains('Planeswalker', na=False)]
cards = cards[~cards['type_line'].str.contains('Background', na=False)]
cards = cards[~cards['type_line'].str.contains('Snow', na=False)]
cards = cards[~cards['type_line'].str.contains('Lesson', na=False)]

def mentions_planeswalker_unqualified(text):
    if not isinstance(text, str):
        return False
    # Matches "planeswalker" not immediately preceded by "or "
    return re.search(r"(?<!or )planeswalker", text, re.IGNORECASE) is not None

cards = cards[~cards['oracle_text'].apply(mentions_planeswalker_unqualified)]

print("Removing cards that rely on other cards or multiples...")
cards = cards[~cards['oracle_text'].str.contains('named', na=False)]
cards = cards[~cards['oracle_text'].str.contains('same name', na=False)]
cards = cards[~cards['oracle_text'].str.contains('Enchant planeswalker', na=False)]
cards = cards[~cards['oracle_text'].str.contains('initiative', na=False)]
cards = cards[~cards['oracle_text'].str.contains('dungeon', na=False)]
cards = cards[~cards['oracle_text'].str.contains('Ripple 4', na=False)]
cards = cards[~cards['oracle_text'].str.contains('monarch', na=False)]
cards = cards[~cards['oracle_text'].str.contains('Partner with', na=False)]
cards = cards[~cards['oracle_text'].str.contains('Background', na=False)]

cards = cards[~cards['oracle_text'].str.contains('Mutate', na=False)]
cards = cards[~cards['oracle_text'].str.contains('Learn', na=False)]
cards = cards[~cards['oracle_text'].str.contains('tempts you', na=False)]

print("Applying price filter...")
cards = cards[cards['prices'].apply(
    lambda p: 0 < float(p.get('usd') or 0) < HIGHEST_PRICE
)]

print("Removing sets in the remove list...")
cards = cards[~cards['set'].isin(sets_to_exclude)]

print("Sorting by color identity...")
def get_color_group(ci):
    if not ci:
        return 'colorless'
    ci_set = frozenset(ci)
    
    mono = {
        frozenset(['R']): 'red',
        frozenset(['G']): 'green',
        frozenset(['W']): 'white',
        frozenset(['B']): 'black',
        frozenset(['U']): 'blue'
    }
    
    dual = {
        frozenset(['R', 'W']): 'boros',
        frozenset(['R', 'U']): 'izzet',
        frozenset(['R', 'B']): 'rakdos',
        frozenset(['R', 'G']): 'gruul',
        frozenset(['B', 'W']): 'orzhov',
        frozenset(['G', 'W']): 'selesnya',
        frozenset(['U', 'W']): 'azorious',
        frozenset(['U', 'B']): 'dimir',
        frozenset(['U', 'G']): 'simic',
        frozenset(['G', 'B']): 'golgari'
    }
    
    tri = {
        frozenset(['R', 'W', 'G']): 'naya',
        frozenset(['R', 'U', 'G']): 'temur',
        frozenset(['R', 'B', 'U']): 'grixis',
        frozenset(['R', 'G', 'B']): 'jund',
        frozenset(['B', 'W', 'U']): 'esper',
        frozenset(['G', 'W', 'B']): 'abzan',
        frozenset(['U', 'W', 'R']): 'jeskai',
        frozenset(['U', 'B', 'G']): 'sultai',
        frozenset(['R', 'B', 'W']): 'mardu',
        frozenset(['G', 'U', 'W']): 'bant'
    }
    
    if len(ci) == 1:
        return mono.get(ci_set, 'other')
    elif len(ci) == 2:
        return dual.get(ci_set, 'other')
    elif len(ci) == 3:
        return tri.get(ci_set, 'other')
    elif len(ci) == 5:
        return 'wubrg'
    else:
        return 'multicolor'

cards['color_group'] = cards['color_identity'].apply(get_color_group)

# Interaction is important, we need to make sure there's a critical mass available
print("Finding interaction...")
def is_interaction(text):
    if not isinstance(text, str):
        return False
    keywords = [
        r"destroy target", 
        r"exile target", 
        r"counter target spell", 
        r"return target .* to (its owner'?s|their) hand",
        r"deal[s]? (\d+|x) damage" 
        r"fight[s]?", 
        r"tap (target | all)", 
        r"gain control of",
        r"sacrifice .* creature",
        r"target creature gets [+-]\d+/-\d+",
        r"creature can't block",
        r"can't attack or block",
        r"stun counters?"
        r"deals damage equal to"
    ]
    pattern = re.compile('|'.join(keywords), re.IGNORECASE)
    return bool(pattern.search(text))

cards['is_interaction'] = cards['oracle_text'].apply(is_interaction)

print("Defining data...")
cards['is_creature'] = cards['type_line'].str.contains('Creature', na=False)
cards['is_land'] = cards['type_line'].str.contains(r'\bLand\b', na=False) & ~cards['type_line'].str.contains(r'\bBasic\b', na=False)
cards['cmc_2'] = cards['cmc'] == 2

print("Creating final list...")
cube_list = []

mono_color_groups = ['red', 'green', 'white', 'black', 'blue', 'colorless']

dual_color_groups = ['boros', 'izzet', 'rakdos', 'gruul', 'orzhov', 'selesnya', 'azorious', 'dimir', 'simic', 'golgari']

tri_color_groups = ['naya', 'temur', 'grixis', 'jund', 'esper', 'abzan', 'jeskai', 'sultai', 'mardu', 'bant']

five_color = ['wubrg']

for color in mono_color_groups:
    subset = cards[cards['color_group'] == color]
    interaction_cards = subset[subset['is_interaction']]
    
    if len(subset) < MONO_COLOR_AMOUNT:
        print(f"⚠️ Not enough cards in group {color}, found {len(subset)}")
        sample_size = len(subset)
    else:
        sample_size = MONO_COLOR_AMOUNT

    if len(interaction_cards) < INTERACTION_MINIMUM:
        print(f"⚠️ Not enough interaction in {color}, found {len(interaction_cards)}")
        interaction_sample = interaction_cards
    else:
        interaction_sample = interaction_cards.sample(INTERACTION_MINIMUM)

    num_creatures = int(sample_size * CREATURE_RATIO)
    num_noncreatures = sample_size - num_creatures

    # Creatures
    creatures = subset[subset['is_creature'] == True]
    cmc2_creatures = creatures[creatures['cmc_2'] == True]
    other_creatures = creatures[creatures['cmc_2'] == False]

    num_cmc2 = int(num_creatures * TWO_DROP_RATIO)
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

    print(f"Cards for {color} selected.")

# These serve as signposts; they do not need to be weighted.
for dual_color in dual_color_groups:
    subset = cards[cards['color_group'] == dual_color]

    if len(subset) < DUAL_COLOR_AMOUNT:
        print(f"⚠️ Not enough cards in group {dual_color}, found {len(subset)}")
        sample_size = len(subset)
    else:
        sample_size = DUAL_COLOR_AMOUNT

    dual_color_sample = subset.sample(sample_size)
    
    cube_list.append(dual_color_sample)

    print(f"Cards for {dual_color} selected.")

# Same as above. No weighting, just signposts and powerful cards.
for tri_color in tri_color_groups:
    subset = cards[cards['color_group'] == tri_color]

    if len(subset) < TRI_COLOR_AMOUNT:
        print(f"⚠️ Not enough cards in group {tri_color}, found {len(subset)}")
        sample_size = len(subset)
    else:
        sample_size = TRI_COLOR_AMOUNT

    tri_color_sample = subset.sample(sample_size)

    cube_list.append(tri_color_sample)

    print(f"Cards for {tri_color} selected.")

# These are five color payoffs, because drafters find these fun.
for all_colors in five_color:
    subset = cards[cards['color_group'] == all_colors]

    if len(subset) < FIVE_COLOR_AMOUNT:
        print(f"⚠️ Not enough cards in group {all_colors}, found {len(subset)}")
        sample_size = len(subset)
    else:
        sample_size = FIVE_COLOR_AMOUNT

    wubrg_color_sample = subset.sample(sample_size)

    cube_list.append(wubrg_color_sample) 

    print(f"Five color cards selected.")   

# Combine all non-land cards
nonland_cube = pd.concat(cube_list)

# Now sample LAND_AMOUNT lands from all vintage-legal lands
land_pool = cards[cards['is_land'] == True]
land_sample = land_pool.sample(n=min(LAND_AMOUNT, len(land_pool)), replace=False)

# Final cube
cube = pd.concat([nonland_cube, land_sample]).sample(frac=1).reset_index(drop=True)

print("Lands selected.")

# Save to CSV
cube.to_csv('cube.csv', index=False, columns=labels)

print(f"Cube generated with {len(cube)} cards.")
