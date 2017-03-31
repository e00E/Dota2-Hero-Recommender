import argparse
import sqlite3
import time
import json
import logging
from pathlib import Path
from threading import Thread


import dota2api
import requests

def create_db(filename):
	"""Create a sqlite3 database in which we can store matches from the dota2 api."""
	connection = sqlite3.connect(filename)
	connection.execute(
		"CREATE TABLE matches\
		(\
		match_id INTEGER PRIMARY KEY,\
		start_time INTEGER NOT NULL,\
		lobby_type INTEGER NOT NULL,\
		radiant_hero_1 INTEGER NOT NULL,\
		radiant_hero_2 INTEGER NOT NULL,\
		radiant_hero_3 INTEGER NOT NULL,\
		radiant_hero_4 INTEGER NOT NULL,\
		radiant_hero_5 INTEGER NOT NULL,\
		dire_hero_1 INTEGER NOT NULL,\
		dire_hero_2 INTEGER NOT NULL,\
		dire_hero_3 INTEGER NOT NULL,\
		dire_hero_4 INTEGER NOT NULL,\
		dire_hero_5 INTEGER NOT NULL,\
		game_mode INTEGER,\
		has_leaver INTEGER,\
		duration INTEGER,\
		radiant_win INTEGER\
		)")
	connection.commit()
	connection.close()
	
def do_match_history(database, lobby_types=[0, 2, 5, 6, 7], skill=3, tournament_games_only=False):
	"""Gather information about recent matches as returned by GetMatchHistory."""
	def add_match_to_db(match):
		radiant_heroes = list()
		dire_heroes = list()
		assert(len(match["players"]) == 10)
		for p in match["players"]:
			slot = p["player_slot"]
			if slot < 128:
				radiant_heroes.append(p["hero_id"])
			else:
				dire_heroes.append(p["hero_id"])
		assert(len(radiant_heroes) == 5)
		assert(len(dire_heroes) == 5)
		# Skip matches where a player didnt pick a hero
		if 0 in radiant_heroes or 0 in dire_heroes:
			logging.info("Skipping {} because of 0 hero.".format(match["match_id"]))
			return
		connection = sqlite3.connect(database, timeout=10)
		connection.execute("INSERT OR IGNORE INTO matches values (?,?,?,?,?,?,?,?,?,?,?,?,?,null,null,null,null)",
		(match["match_id"], match["start_time"], match["lobby_type"]) + tuple(radiant_heroes) + tuple(dire_heroes))
		connection.commit()
		connection.close()

	start_at_match_id = None
	matches = 0
	while True:
		tries = 0
		while tries < 3:
			tries += 1
			try:
				result = api.get_match_history(skill=skill, min_players=10, tournament_games_only="1" if tournament_games_only else "0", matches_requested=100, start_at_match_id=start_at_match_id,)
				break
			except (requests.exceptions.ConnectionError, json.decoder.JSONDecodeError, dota2api.src.exceptions.APIError, dota2api.src.exceptions.APITimeoutError):
				logging.warning("Api or timeout error in MatchHistory on try {}.".format(tries))
				time.sleep(30)
				continue
		if tries == 3:
			return
		if result["results_remaining"] == 0:
			break
		start_at_match_id = result["matches"][-1]["match_id"] - 1
		for match in result["matches"]:
			if len(match["players"]) == 10 and match["lobby_type"] in lobby_types:
				add_match_to_db(match)
				matches += 1
	print("Added", matches, "matches.")

def do_match_details(database):
	"""Updated match ids which have incomplete information in the database. This is needed because GetMatchHistory does not deliver all needed information."""
	def update_match_in_db(match):
		has_leavers = False
		for p in match["players"]:
			if p["leaver_status"] in [2, 3, 4, 5, 6]: has_leavers = True
		connection = sqlite3.connect(database, timeout=10)
		connection.execute("UPDATE OR IGNORE matches SET game_mode=?, has_leaver=?, duration=?, radiant_win=? WHERE match_id=?", (match["game_mode"], has_leavers, match["duration"], match["radiant_win"], match["match_id"]))
		connection.commit()
		connection.close()
	connection = sqlite3.connect(database, timeout=10)
	matches = connection.execute("SELECT match_id FROM matches WHERE radiant_win IS NULL").fetchall()
	connection.close()
	for (match_id,) in matches:
		try:
			result = api.get_match_details(match_id=match_id)
		except (requests.exceptions.ConnectionError, json.decoder.JSONDecodeError, dota2api.src.exceptions.APIError, dota2api.src.exceptions.APITimeoutError):
			logging.warning("Api or timeout error in MatchDetails on matchid {}.".format(match_id))
			time.sleep(30)
			continue
		print("Added details for {}.".format(result["match_id"]))
		update_match_in_db(result)
		time.sleep(1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Continually gather new matches from the dota2 api and store them in an sqlite3 database. Use ctrl-c to quite the program at any time.")
	parser.add_argument("--database", help="Database to store matches in. Will be created if file doesnt already exist.", required=True)
	parser.add_argument("--api-key", help="Steam api key used for the api requests. Get one at https://steamcommunity.com/dev/apikey .", required=True)
	args = parser.parse_args()
	
	path = Path(args.database)
	if not path.exists():
		logging.info("Creating database because it does not exist.")
		create_db(args.database)
	elif not path.is_file():
		raise RuntimeError("Database is not a file.")
	else:
		logging.info("Using existing database.")

	api = dota2api.Initialise(args.api_key, raw_mode=True)
	
	
	def match_history():
		while True:
			do_match_history(args.database)
			time.sleep(60)
	match_history_thread = Thread(target=match_history)
	match_history_thread.daemon = True
	
	def match_details():
		while True:
			do_match_details(args.database)
			time.sleep(60)
	match_details_thread = Thread(target=match_details)
	match_details_thread.daemon = True
	
	print("Starting MatchHistory and MatchDetails threads.")
	match_history_thread.start()
	match_details_thread.start()
	# This is needed (instead of joining the threads) to respond to crl-c
	while True:
		time.sleep(1)