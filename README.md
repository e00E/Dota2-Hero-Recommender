Requirements:
[Python 3](https://www.python.org/downloads/), [Dota2api](https://dota2api.readthedocs.io/en/latest/installation.html), [scikit-learn](http://scikit-learn.org/stable/install.html).

If you are on Windows you might want to use [Anaconda](https://www.continuum.io/downloads) as your Python installation.

# Machine Learning
For machine learning we first query the Dota2 api to retrieve data of real matches. This can be done with:

```python "machine learning/get_data.py" --database "data/matches.sqlite" --api-key "your api key"```

You need a steam api key which you get [here](https://steamcommunity.com/dev/apikey).

If you are only interested in getting match data then you dont need to install scikit-learn and can use `get_data.py` alone.
