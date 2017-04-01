import itertools
import random
import util

class State:
	def __init__(self, radiant_moves_next=True, radiant_heroes=frozenset(), dire_heroes=frozenset(), banned_heroes=frozenset(), pick_ban_position=0):
		self.radiant_heroes = radiant_heroes
		self.dire_heroes = dire_heroes
		self.banned_heroes = banned_heroes
		self.radiant_moves_next = radiant_moves_next
		self.pick_ban_position = pick_ban_position
		self.actions = None
	def is_terminal(self):
		return len(self.radiant_heroes) == util.team_size and len(self.dire_heroes) == util.team_size
	# an action is just a tuple of hero ids
	# return a list of those actions
	def get_actions(self):
		if self.is_terminal(): return list()
		# cache actions
		if self.actions == None:
			(_, count) = util.pick_ban_order[self.pick_ban_position]
			self.actions = list(itertools.combinations(util.all_heroes.difference(self.radiant_heroes.union(self.dire_heroes).union(self.banned_heroes)), count))
		return self.actions
	def choose_random_action(self):
		actions = self.get_actions()
		return random.choice(actions)
	def radiant_moved(self):
		return not self.radiant_moves_next
	def get_next_state(self, action):
		(pick_ban, _) = util.pick_ban_order[self.pick_ban_position]
		state = State(not self.radiant_moves_next, self.radiant_heroes, self.dire_heroes, self.banned_heroes, self.pick_ban_position+1)
		if pick_ban == util.pick:
			if self.radiant_moved():
				state.dire_heroes = self.dire_heroes.union(action)
			else:
				state.radiant_heroes = self.radiant_heroes.union(action)
		else:
			state.banned_heroes = self.banned_heroes.union(action)
		return state
	def str(self):
		result = 'Banned: '
		for i in self.banned_heroes: result += str(i) + ' '
		result += 'Radiant: '
		for i in self.radiant_heroes: result += str(i) + ' '
		result += 'Dire: '
		for i in self.dire_heroes: result += str(i) + ' '
		result += 'Radiant moved: ' + str(self.radiant_moved())
		return result