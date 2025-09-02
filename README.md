## Random Cube Generator

#### Premise
After playing a few Mystery Booster 2 drafts, I got the idea: was it possible to make a chaos cube that could imitate that sort of randomness? That led to this cube, created via a python script utilizing [Pandas](https://pandas.pydata.org/docs/index.html#).

#### How It Works
The [script](https://github.com/NathanaelGass/random-cube/tree/main) takes the list of all cards, provided from the Scryfall [bulk data page](https://scryfall.com/docs/api/bulk-data). From there, it organizes, cleans the data a bit, trims it, and selects an appropriate sample of colors, creatures, two drops, and interaction with the goal of making a highly randomized but still playable limited environment.

#### Creating Your Own Version
The script can be run yourself if you'd like to generate your own. It runs with certain defaults, but if you'd like to generate a random cube of your own with different inputs, you can run it in interactive mode, and provide your own inputs; number of cards per color, allowed card cost, etc. If you want to tweak which sets are allowed, you'll need to add them directly to the script's set array.

At the end of execution, the script exports to a 'cube.csv' file that can be directly uploaded to a Cube Cobra via the List > Import/Export > Replace with CSV File Upload.

##### Prerequisites:
- Python installed.
- Pandas.
- The downloaded **Oracle Cards** bulk data from Scryfall.
- Rename the bulk data to oracle_cards.json
- This script downloaded or copied.

##### Running:
```
python .\RandomCubeGenerator.py
```
That easy. Enjoy!
