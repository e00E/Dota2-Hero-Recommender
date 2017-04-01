import sqlite3
import simple_heroes
import random

class Winrates:
	def load_winrates(self, database="data/matches.sqlite"):
		connection = sqlite3.connect(database)
		self.radiant_winrates = dict()
		self.dire_winrates = dict()
		for hero in simple_heroes.dota_hero_ids:
			matches_on_radiant = connection.execute('SELECT COUNT(match_id) as wins FROM VeryHighSkillGames WHERE radiant_hero_1 = ? OR radiant_hero_2 = ? OR radiant_hero_3 = ? OR radiant_hero_4 = ? OR radiant_hero_5 = ? GROUP BY radiant_win', (hero,) * 5).fetchall()
			assert(len(matches_on_radiant) == 2)
			((dire_wins,), (radiant_wins,)) = matches_on_radiant
			total_matches = dire_wins + radiant_wins
			winrate_on_radiant = radiant_wins / total_matches

			matches_on_dire = connection.execute('SELECT COUNT(match_id) as wins FROM VeryHighSkillGames WHERE dire_hero_1 = ? OR dire_hero_2 = ? OR dire_hero_3 = ? OR dire_hero_4 = ? OR dire_hero_5 = ? GROUP BY radiant_win', (hero,) * 5).fetchall()
			assert(len(matches_on_dire) == 2)
			((dire_wins,), (radiant_wins,)) = matches_on_dire
			total_matches = dire_wins + radiant_wins
			winrate_on_dire = dire_wins / total_matches

			self.radiant_winrates[simple_heroes.real_to_ordered(hero)] = winrate_on_radiant
			self.dire_winrates[simple_heroes.real_to_ordered(hero)] = winrate_on_dire

		self.sorted_radiant_ids = sorted(self.radiant_winrates, key=lambda x: self.radiant_winrates[x])
		self.sorted_dire_ids = sorted(self.dire_winrates, key=lambda x: self.dire_winrates[x])
	def print_winrates(self):
		for hero in range(len(simple_heroes.dota_hero_ids)):
			print(simple_heroes.ordered_to_name(hero), self.radiant_winrates[hero], self.dire_winrates[hero])

# Load one global winrates instance
winrates = Winrates()
winrates.load_winrates()