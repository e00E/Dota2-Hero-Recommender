import math
import random
import time
from copy import copy

from gamestate import State
import util

"""
This code is inspired by:

@article{mctssurvey,
    author = "Cameron Browne and Edward Powley and Daniel Whitehouse and Simon Lucas and Peter I. Cowling and Stephen Tavener and Diego Perez and Spyridon Samothrakis and Simon Colton",
    title = "A Survey of Monte Carlo Tree Search Methods",
    journal = "IEEE TRANSACTIONS ON COMPUTATIONAL INTELLIGENCE AND AI",
	volume = "4",
    year = {2012}
}

Readable online here: http://www.cameronius.com/cv/mcts-survey-master.pdf
"""

def uct_search(model, initial_state=None, initial_node=None, time_limit=None, iteration_limit=None, Cp=2**-3):
	assert((initial_state is None) ^ (initial_node is None))
	if not initial_node is None:
		root_node = initial_node
	else:
		root_node = Node(initial_state)
	assert((time_limit is None) ^ (iteration_limit is None))
	start_time = time.time()
	iteration_count = 0
	while (time.time() - start_time) < time_limit if iteration_limit is None else iteration_count < iteration_limit:
		node = tree_policy(root_node, Cp)
		reward = default_policy(node.state, model)
		backup(node, reward)
		iteration_count += 1
	#print('finished', iteration_count, 'iterations in', time_limit, 'seconds.')
	best = best_child(root_node, 0)
	return (best, root_node)

def tree_policy(node, Cp):
	while not node.state.is_terminal():
		if len(node.remaining_actions) != 0:
			return node.expand()
		else:
			node = best_child(node, Cp)
	return node

def best_child(node, Cp):
	constant = math.log(node.visit_count)
	return max(node.children, key=lambda n:
		n.total_simulated_reward / n.visit_count + Cp * math.sqrt( constant / n.visit_count))

def default_policy(state, model):
	for_radiant = state.radiant_moved()
	while not state.is_terminal():
		action = state.choose_random_action()
		state = state.get_next_state(action)
	return compute_reward(state, for_radiant, model)
	
# Reward is the probability of winning
def compute_reward(state, for_radiant, model):
	feature = util.state_to_feature(state)
	radiant_win = util.predict_radiant_win_probability(feature, model)
	if for_radiant: return radiant_win
	else: return 1 - radiant_win

def backup(node, reward):
	while node != None:
		node.visit_count += 1
		node.total_simulated_reward += reward
		reward = 1 - reward
		node = node.parent		

class Node:
	def __init__(self, state=State(), incoming_action=None, parent=None, total_simulated_reward=0, visit_count=0):
		self.state = state # s(v)
		self.incoming_action = incoming_action # a(v)
		self.parent = parent
		self.total_simulated_reward  = total_simulated_reward # Q(v)
		self.visit_count = visit_count # N(v)
		self.children = list()
		self.remaining_actions = copy(self.state.get_actions())
	def expand(self):
		action = random.choice(self.remaining_actions)
		self.remaining_actions.remove(action)
		child = Node(self.state.get_next_state(action), action, self)
		self.children.append(child)
		return child