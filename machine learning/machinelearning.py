import numpy as np
from sklearn import linear_model
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn import svm
from sklearn import neighbors
from sklearn.neural_network import MLPClassifier
from sklearn import preprocessing
import math
import time

from sklearn.externals import joblib

import simple_heroes

import sqlite3
import os
import os.path


def load_data(database, undersample=True):
	"""
	Load data from a sqlite3 database and convert the matches into feature vectors in form of numpy arrays.
	
	Optionally perform undersampling to get the same number of samples of both classes.
	
	This method can be used directly, or indirectly via make_training_validate_test.
	"""
	connection = sqlite3.connect(database)
	if undersample:
		number_of_radiant_wins = connection.execute('SELECT COUNT(radiant_win) FROM matches WHERE radiant_win IS NOT NULL AND radiant_win = 1 AND has_leaver = 0 AND radiant_hero_1 != 0 AND radiant_hero_2 != 0 AND radiant_hero_3 != 0 AND radiant_hero_4 != 0 AND radiant_hero_5 != 0 AND dire_hero_1 != 0 AND dire_hero_2 != 0 AND dire_hero_3 != 0 AND dire_hero_4 != 0 AND dire_hero_5 != 0').fetchone()[0]
		number_of_dire_wins = connection.execute('SELECT COUNT(radiant_win) FROM matches WHERE radiant_win IS NOT NULL AND radiant_win = 0 AND has_leaver = 0 AND radiant_hero_1 != 0 AND radiant_hero_2 != 0 AND radiant_hero_3 != 0 AND radiant_hero_4 != 0 AND radiant_hero_5 != 0 AND dire_hero_1 != 0 AND dire_hero_2 != 0 AND dire_hero_3 != 0 AND dire_hero_4 != 0 AND dire_hero_5 != 0').fetchone()[0]
		max_games_per_class = min(number_of_radiant_wins, number_of_dire_wins)
		radiant_wins = 0
		dire_wins = 0
	dataset = list()
	targetset = list()
	for lineno, line in enumerate(connection.execute('SELECT radiant_win, radiant_hero_1,radiant_hero_2,radiant_hero_3,radiant_hero_4,radiant_hero_5, dire_hero_1,dire_hero_2,dire_hero_3,dire_hero_4,dire_hero_5 FROM matches WHERE radiant_win IS NOT NULL AND has_leaver = 0 AND radiant_hero_1 != 0 AND radiant_hero_2 != 0 AND radiant_hero_3 != 0 AND radiant_hero_4 != 0 AND radiant_hero_5 != 0 AND dire_hero_1 != 0 AND dire_hero_2 != 0 AND dire_hero_3 != 0 AND dire_hero_4 != 0 AND dire_hero_5 != 0')):
		radiant_won = line[0]

		if undersample:
			if radiant_wins == max_games_per_class and dire_wins == max_games_per_class: #both classes already at max games
				break
			elif radiant_won == 0: #dire won
				if dire_wins == max_games_per_class: #dire already at max games
					continue
				else:
					dire_wins += 1
			else: #radiant won
				if radiant_wins == max_games_per_class: #radiant already at max games
					continue
				else:
					radiant_wins += 1

		radiant_hero_ids = line[1:6]
		dire_hero_ids  = line[6:]

		winner, features = extract_standard(radiant_won, radiant_hero_ids, dire_hero_ids)
		targetset.append(winner)
		dataset.append(features)
	connection.close()
	
	samples = np.array(dataset)
	target = np.array(targetset)
	# http://stackoverflow.com/questions/4601373/better-way-to-shuffle-two-numpy-arrays-in-unison
	rng_state = np.random.get_state()
	np.random.shuffle(samples)
	np.random.set_state(rng_state)
	np.random.shuffle(target)
	return (samples, target)

def extract_standard(radiant_won, radiant, dire):
	"""
	Turn a match constisting of its winner and the radiant and dire heroes into a feature vector.
	
	The default version uses a 224 dimensional feature vector and sets elements corresponding to the picked heroes to 1 while the rest are set to 0.
	The first 112 elements are the heroes on the radiant team and the other the heroes on the dire team.
	
	The target class 0 represents the radiant winning, and 1 the dire winning.
	"""
	def put_heroes_in_features(heroes, features):
		for i in heroes:
			features[simple_heroes.real_to_ordered(i)] = 1.0

	winner = int(not radiant_won)

	radiant_heroes = [0] * len(simple_heroes.dota_hero_ids)
	dire_heroes = [0] * len(simple_heroes.dota_hero_ids)

	put_heroes_in_features(radiant, radiant_heroes)
	put_heroes_in_features(dire, dire_heroes)

	features = radiant_heroes + dire_heroes

	return (winner, features)

	
def make_training_validate_test(database, training_ratio, undersample=True):
	"""
	Create a training, validate and test set to be used in model parameter tuning.
	
	Specified is the amount of samples in the training set in form of a ratio. The validate and test sets use remaining samples split evenly between them.
	
	The results are written to disk in the data directory.
	"""
	assert(training_ratio > 0 and training_ratio < 1)
	validate_ratio = test_ratio = (1-training_ratio) / 2
	(data, target) = load_data(database, undersample=undersample)
	
	number_of_samples = len(target)
	number_of_training_samples = math.floor(number_of_samples * training_ratio)
	number_of_validate_samples = math.floor(number_of_samples * validate_ratio)
	number_of_test_samples = math.floor(number_of_samples * test_ratio)
	
	training_data = data[0:number_of_training_samples]
	training_target = target[0:number_of_training_samples]
	validate_data = data[number_of_training_samples:number_of_training_samples+number_of_validate_samples]
	validate_target = target[number_of_training_samples:number_of_training_samples+number_of_validate_samples]
	test_data = data[number_of_training_samples+number_of_validate_samples:number_of_training_samples+number_of_validate_samples+number_of_test_samples]
	test_target = target[number_of_training_samples+number_of_validate_samples:number_of_training_samples+number_of_validate_samples+number_of_validate_samples]
	
	joblib.dump(training_data, "data/training_data");
	joblib.dump(training_target, "data/training_target");
	joblib.dump(validate_data, "data/validate_data");
	joblib.dump(validate_target, "data/validate_target");
	joblib.dump(test_data, "data/test_data");
	joblib.dump(test_target, "data/test_target");

def export_model(model, name):
	"""Export a model to disk. Models can consist of multiple files so a directory is created for each model."""
	path = "data/{}/".format(name)
	filename = "{}.model".format(name)
	if os.path.isdir(path):
		print("model already exists")
		return
	else:
		os.mkdir(path)
		joblib.dump(model, path + filename)
		
def load_model(name):
	"""Load a model from disk."""
	model = joblib.load("data/{}/{}.model".format(name, name))
	# Setting n_jobs to 1 in case it was set to a higher number while training the model seems to makes predictions of single samples much faster.
	model.n_jobs = 1
	return model

def print_speed_and_accuracy(models = ["decisiontree", "gradienttreeboosting", "knn", "logisticregression", "randomforest"]):
	"""
	Helper method to print speed and accuracy of already created models on the test data.
	
	Speed is measured in the time it takes to predict 1000 samples sequentially.
	"""
	test_data = joblib.load("data/test_data")
	test_target = joblib.load("data/test_target")

	for model in models:
		model = load_model(model)
		accuracy = model.score(test_data, test_target)
		start = time.time()
		for i in range(1000):
			model.predict_proba([test_data[i]])
		end = time.time()
		duration = end - start
		print(model, accuracy, duration)
	
if __name__ == '__main__':
	# Generate train, validate, test sets. Comment this out after having run it once so you dont regnerate the data every run.
	make_training_validate_test("data/matches.sqlite", 0.8)

	# Load training data if it has previously been generated	
	training_data = joblib.load("data/training_data")
	training_target = joblib.load("data/training_target")

	validate_data = joblib.load("data/validate_data")
	validate_target = joblib.load("data/validate_target")
	
	test_data = joblib.load("data/test_data")
	test_target = joblib.load("data/test_target")

	# Train a model
	# Examples for well working models and parameters. Uncomment to use one.
	# model = linear_model.LogisticRegression(solver='sag', dual=False, penalty='l2', n_jobs=4)
	# modelname = "logisticregression"
	# model = RandomForestClassifier(n_estimators=200, min_samples_split=0.001, max_depth=None, max_features="auto", n_jobs=2)
	# model = GradientBoostingClassifier(n_estimators=75, max_features=None, max_depth=15)
	# model = neighbors.KNeighborsClassifier(algorithm='ball_tree', n_neighbors=180, weights='distance', metric='manhattan', leaf_size=200, n_jobs=4)
	# model = MLPClassifier(hidden_layer_sizes=(100,))
	
	model.fit(training_data, training_target)
	model.score(validate_data, validate_target)

	# Export it to disk
	export_model(model, modelname)
	