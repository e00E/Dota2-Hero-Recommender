from sklearn.externals import joblib
import random

import importlib.util
spec = importlib.util.spec_from_file_location("simple_heroes", "machine learning/simple_heroes.py")
simple_heroes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple_heroes)

# list of names of all available machine learning models
all_models = []

def load_model(name):
	model = joblib.load("data/{}/{}.model".format(name, name))
	model.n_jobs = 1 #for some reason setting n_jobs to 1 makes single predictions much faster.
	return model
	
orig_all_heroes = set([simple_heroes.real_to_ordered(i) for i in simple_heroes.dota_hero_ids])
all_heroes = set([simple_heroes.real_to_ordered(i) for i in simple_heroes.dota_hero_ids])
team_size = 5
# enum values for pick and ban
pick = 0
ban = 1
# captains mode
cm_order = (
	(ban,1),(ban,1),(ban,1),(ban,1),
	(pick,1),(pick,2),(pick,1),
	(ban,1),(ban,1),(ban,1),(ban,1),
	(pick,1),(pick,1),(pick,1),(pick,1),
	(ban,1),(ban,1),
	(pick,1),(pick,1))
allpick_order = ((pick,1),(pick,1),(pick,1),(pick,1),(pick,1),(pick,1),(pick,1),(pick,1),(pick,1),(pick,1),)
randomdraft_order = allpick_order

allpick_cp = 2**-3
cm_cp = 2**-5
transpo_cp = 2**-5

# this is used by everything as the current game mode
#pick_ban_order = allpick_order
#pick_ban_order = randomdraft_order
pick_ban_order = cm_order

def make_random_pool(pool_size=50):
	all_heroes = [simple_heroes.real_to_ordered(i) for i in simple_heroes.dota_hero_ids]
	random.shuffle(all_heroes)
	random_pool = set(all_heroes[:pool_size])
	return random_pool
	
# all_heroes = make_random_pool()

# convert mcts state to feature vector
def state_to_feature(state):
	radiant_heroes = [0.0] * len(simple_heroes.dota_hero_ids)
	dire_heroes = [0.0] * len(simple_heroes.dota_hero_ids)
	for i in state.radiant_heroes: radiant_heroes[i] = 1.0
	for i in state.dire_heroes: dire_heroes[i] = 1.0
	feature = radiant_heroes + dire_heroes
	return feature

def predict_radiant_win_probability(feature, model):
	radiant_win, dire_win = model.predict_proba([feature])[0]
	#return (radiant_win + (1 - dire_win)) / 2
	return radiant_win

def print_tree(node, indent=''):
	print(indent + "Q:", node.total_simulated_reward, "N:", node.visit_count)
	print(indent + "State:", node.state.str())
	print(indent + "Children:")
	node.children.sort(key=lambda n: n.incoming_action)
	for n in node.children:
		print(indent + str(n.incoming_action) + ':')
		print_tree(n, indent + ' ')