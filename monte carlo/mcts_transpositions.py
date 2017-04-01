import math
import random
import time
from copy import copy

from gamestate import State
from mcts import default_policy
import util

"""
The transposition code is inspired by:

@INPROCEEDINGS{mctstranspositions,
    author={B. E. Childs and J. H. Brodeur and L. Kocsis},
	booktitle={2008 IEEE Symposium On Computational Intelligence and Games},
	title={Transpositions and move groups in Monte Carlo tree search},
	year={2008},
	pages={389-395},
	keywords={Monte Carlo methods;computer games;trees (mathematics);Monte Carlo tree search;artificial trees;effective branching factor;game programs;graph structure;upper confidence bounds;Algorithm design and analysis;Automation;Computer science;Electronic mail;History;Monte Carlo methods;Statistics;Tree data structures;Tree graphs},
	doi={10.1109/CIG.2008.5035667},
	ISSN={2325-4270},
	month={Dec}
}
"""


class Transposition:
	def __init__(self, total_simulated_reward=0, visit_count=0):
		self.total_simulated_reward = total_simulated_reward
		self.visit_count = visit_count
		
def state_to_key(state):
	return (state.radiant_heroes, state.dire_heroes, state.banned_heroes)

def uct_search(model, initial_state=None, initial_node=None, transpositions=dict(), time_limit=None, iteration_limit=None, Cp=2**-5):
	assert((initial_state is None) ^ (initial_node is None))
	if not initial_node is None:
		root_node = initial_node
	else:
		root_node = Node(initial_state)
	assert((time_limit is None) ^ (iteration_limit is None))
		
	# keys type is (set(radiant_heroes), set(dire_heroes), set(banned_heroes))
	# value type is Transposition
	transpositions[state_to_key(root_node.state)] = Transposition()

	start_time = time.time()
	iteration_count = 0
	while (time.time() - start_time) < time_limit if iteration_limit is None else iteration_count < iteration_limit:
		node = tree_policy(root_node, Cp, transpositions)
		reward = default_policy(node.state, model)
		backup(node, reward, transpositions)
		iteration_count += 1
	#print('finished', iteration_count, 'iterations in', time_limit, 'seconds.')
	best = best_child(root_node, 0, transpositions)
	return (best, root_node, transpositions)

def tree_policy(node, Cp, transpositions):
	while not node.state.is_terminal():
		if len(node.remaining_actions) != 0:
			return node.expand()
		else:
			node = best_child(node, Cp, transpositions)
	return node

def best_child(node, Cp, transpositions):
	constant = math.log(node.visit_count)
	def value(n):
		transpo = transpositions[state_to_key(n.state)]
		return transpo.total_simulated_reward / transpo.visit_count + Cp * math.sqrt( constant / n.visit_count)
	return max(node.children, key=value)		

def backup(node, reward, transpositions):
	while node != None:
		node.visit_count += 1
		
		key = state_to_key(node.state)
		transposition = transpositions.get(key)
		if transposition == None:
			transposition = Transposition()
			transpositions[key] = transposition
		transposition.visit_count += 1
		transposition.total_simulated_reward += reward
		
		reward = 1 - reward
		node = node.parent
		
class Node:
	def __init__(self, state=State(), incoming_action=None, parent=None, visit_count=0):
		self.state = state # s(v)
		self.incoming_action = incoming_action # a(v)
		self.parent = parent
		self.visit_count = visit_count # N(v)
		self.children = list()
		self.remaining_actions = copy(self.state.get_actions()) if not state.is_terminal() else list()
	def expand(self):
		action = random.choice(self.remaining_actions)
		self.remaining_actions.remove(action)
		child = Node(self.state.get_next_state(action), action, self)
		self.children.append(child)
		return child