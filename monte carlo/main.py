import argparse

import mcts
import mcts_transpositions
import util
from gamestate import State

def ask_question(question, answers):
	while True:
		answer = input("{} + ({})".format(question, answers))
		if answer not in answers:
			print("Invalid answer")
		else:
			return answer
			
def get_pick(state, pick_ban, count):
	while True:
		skip = False
		hero_names = input('{} {} hero: '.format('Choose', count)).split(',')
		heroes = list()
		for name in hero_names:
			id = util.simple_heroes.approximate_name_to_ordered(name)
			if id is None:
				print('Could not find hero {}'.format(name))
				skip = True
				break
			elif id in state.radiant_heroes or id in state.dire_heroes or id in state.banned_heroes:
				print("Hero {} already picked or banned.".format(name))
				skip = True
				break
			else:
				heroes.append(id)
		if skip: continue
		if len(heroes) != count:
			print('Wrong number of heroes')
			continue
		return tuple(heroes)

def print_state(state):
		print('Banned:', [util.simple_heroes.ordered_to_name(i) for i in state.banned_heroes])
		print('Radiant:', [util.simple_heroes.ordered_to_name(i) for i in state.radiant_heroes])
		print('Dire:', [util.simple_heroes.ordered_to_name(i) for i in state.dire_heroes])

def real_game(modelname, time_limit, recommendation_count):
	mode = ask_question("What gamemode are you playing?", ["ap", "cm"])
	side = ask_question("Which side are you playing on?", ["radiant", "dire"])
	first = ask_question("Do you have first pick / ban?", ["y", "n"])
	
	if mode == "ap":
		util.pick_ban_order = util.allpick_order
	else:
		util.pick_ban_order = util.cm_order
		
	radiant_goes_first = (side == "radiant" and first == "y") or (side == "dire" and first == "n")
	node = mcts_transpositions.Node(mcts.State(radiant_goes_first))
	transpositions = dict()
	model = util.load_model(modelname)
	players_turn = (side == "radiant" and node.state.radiant_moves_next) or (side == "dire" and not node.state.radiant_moves_next)
	while not node.state.is_terminal():
		print_state(node.state)
		choices = node.state.get_actions()
		choices_sets = [set(i) for i in choices]
		
		(pick_ban, count) = util.pick_ban_order[node.state.pick_ban_position]
		subject = 'pick' if pick_ban == util.pick else 'ban'
		print("The next action is a", subject, "of", count, "heroes.")
		
		if players_turn:
			print("It is your turn. MCTS recommends the following heroes: ...")
			(_, root_node, transpositions) = mcts_transpositions.uct_search(model,initial_node=node, time_limit=time_limit, transpositions=transpositions)
			node = root_node
			def to_transpo(n): return transpositions[mcts_transpositions.state_to_key(n.state)]
			children = sorted(root_node.children, key=lambda n: to_transpo(n).total_simulated_reward / to_transpo(n).visit_count, reverse=True)
			for c in children[:recommendation_count]:
				print([util.simple_heroes.ordered_to_name(i) for i in c.incoming_action], to_transpo(c).total_simulated_reward / to_transpo(c).visit_count, to_transpo(c).visit_count)
		else:
			print("It is the other team's turn. What did they do?")
		players_turn = not players_turn
		choice = get_pick(node.state, pick_ban, count)
		
		print()
		assert(set(choice) in choices_sets)
		found = False
		for n in node.children:
			if n.incoming_action == choice:
				node = n
				node.parent = None
				node.incoming_action = None
				found = True
		if not found:
			node = mcts.Node(node.state.get_next_state(choice))
	print('Done!')
	print_state(node.state)
	print('Predicting Radiant win probability with all models:')
	for model_name in util.all_models:
		model = util.load_model(model_name)
		print(model_name,':', util.predict_radiant_win_probability(util.state_to_feature(node.state), model))

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--time-limit", type=float, default=1.0)
	parser.add_argument("--recommendation-count", type=int, default=10)
	parser.add_argument("models", nargs="+", help="Available previously generated models. First one will be used by MCTS, and the others to compare the final team composition.")
	args = parser.parse_args()
	util.all_models = args.models
	real_game(args.models[0], args.time_limit, args.recommendation_count)