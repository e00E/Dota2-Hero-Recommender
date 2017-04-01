Requirements:
[Python 3](https://www.python.org/downloads/), [Dota2api](https://dota2api.readthedocs.io/en/latest/installation.html), [scikit-learn](http://scikit-learn.org/stable/install.html).

If you are on Windows you might want to use [Anaconda](https://www.continuum.io/downloads) as your Python installation.

# Machine Learning
For machine learning we first query the Dota2 api to retrieve data of real matches. This can be done with:

```python "machine learning/get_data.py" --database "data/matches.sqlite" --api-key "your api key"```

You need a steam api key which you get [here](https://steamcommunity.com/dev/apikey).

If you are only interested in getting match data then you dont need to install scikit-learn and can use `get_data.py` alone.

The program will continually gather recent matches and store them in a sqlite3 database. You can exit it with ctrl-c.

When we have enough data we can train machine learning models with scikit-learn. This is done in `machine learning/machinelearning.py`. Scroll to the bottom of the file and edit the machine learning process how you see fit and run the file.

# Hero Recommending
Hero recommendations are done with Monte Carlo Tree Search. The main program is called with:
```python "monte carlo/main.py" "modelname"```
and it will interactively ask you to pick and enter the opponent's picks. Every step it displays the expected win probability and number of simulations run with the top X hero choices.

"modelname" is the name of a model that was previously trained.
It has some further command line options which you can see by running it with `--help`.
