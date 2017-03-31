import json
from difflib import SequenceMatcher

"""
The purpose of this module is to provde some utility functions related to hero ids.

It can convert the real hero ids as used in Dota2 into "minimial" or "ordered" ids as in ids starting at 0, with no gaps between.

It can retrieve the name of a hero given its real or ordered id.

I can find the hero id of a hero given its approximate name.

The module requires a simple_hero_list.json file which can be retrieved via the GetHeroes api method: https://wiki.teamfortress.com/wiki/WebAPI/GetHeroes .
This file only needs to be updated when a new hero is added to Dota2.
"""

# A list of all hero ids in ascending order. Ordered hero ids are defined by their index in this list.
dota_hero_ids = list()
# Maps real hero ids to their names
dota_hero_names = dict()

def real_to_ordered(id):
	return dota_hero_ids.index(id)
	
def ordered_to_real(id):
	return dota_hero_ids[id]
	
def ordered_to_name(id):
	return real_to_name(ordered_to_real(id))
	
def real_to_name(id):
	return dota_hero_names[id]
	
def approximate_name_to_real(name, min_ratio=0.9):
	def pre_format(string):
		return string.replace(' ', '').replace('_', '').lower()
	name = pre_format(name)
	current_best_id = None
	current_best_ratio = 0.0
	for id in dota_hero_ids:
		new_ratio = SequenceMatcher(None, pre_format(dota_hero_names[id]), name, False).ratio()
		if new_ratio > current_best_ratio:
			current_best_ratio = new_ratio
			current_best_id = id
	return current_best_id if current_best_ratio >= min_ratio else None
	
def approximate_name_to_ordered(name, min_ratio=0.9):
	result = approximate_name_to_real(name,min_ratio=min_ratio)
	return real_to_ordered(result) if result != None else None

with open('simple_hero_list.json') as f:
	j = json.load(f)
	heroes = j['result']['heroes']
	for i in sorted(heroes, key=lambda h: h['id']):
		dota_hero_ids.append(i['id'])
		dota_hero_names[i['id']] = i['name'][len('npc_dota_hero')+1:]