Usage
=====

The package uses the Stocktwits API manages three type of streas: user, symbol and conversation. Now the package manages the user and symbol streams.

There are some parameters that you can use. These are the mandatory parameters:

* **symbols**, you can define a list of symbols that you want to download: this list has to have at least one element or it has to exist the parameter **users**
* **users**, you can define a list of users that you want to download: this list has to have at least one element or it has to exist the parameter **symbols**

And these are optionals:

* **only_combo**, when you want to download only the combo between a specific symbol and user, you have to use each previous parameter and this that it is a boolean
* **min**, it is the ID of a specific twit from which you want to start downloading
* **max**, it is the ID of a specific twit where you want to stop downloading
* **limit**, it is the number of messages that you want to download in one shot
* **start**, it is the datetime from which you want to start downloading
* **chunk**, it is the chunk (day, week or month) in which you want to split the data
* **filename_prefix**, it is the prefix name of files where you want to save the data
* **filename_suffix**, it is the suffix name of files where you want to save the data
* **is_verbose**, when you want to print some information to understand what the system is saving, it is a boolean

Without optional parameters, the system downloads the last 30 messages and prints those in the output. If you want to save that on a file (or more files), you have to use at least the **chunk** parameter.

Examples
########

Remeber to install the package by pip

.. code-block:: bash

    pip3 install stocktwits-collector

or by requirements.txt contains one line with **stocktwits-collector**

.. code-block:: bash

    pip3 install --upgrade -r requirements.txt


.. code-block:: python

    import os
    import json
    import pandas as pd

    from stocktwits_collector.collector import Collector
    sc = Collector()

    # download last messages up to 30
    messages = sc.get_history({'symbols': ['TSLA'], 'limit': 4})
    # download the messages from a date to today
    messages = sc.get_history({'symbols': ['TSLA'], 'start': '2022-04-04T00:00:00Z'})
    # save the messages on files splitted per chunk from a date to max ID
    chunk = sc.save_history({'symbols': ['TSLA'], 'start': '2022-04-04T00:00:00Z', 'chunk': 'day'})

    # load data from one file
    with open('history.20220404.json', 'r') as f:
        data = json.loads(f.read())
    df = pd.json_normalize(
        data,
        meta=[
            'id', 'body', 'created_at',
            ['user', 'id'],
            ['user', 'username'],
            ['entities', 'sentiment', 'basic']
        ]
    )
    twits = df[['id', 'body', 'created_at', 'user.username', 'entities.sentiment.basic']]

    # load data from multiple files
    frames = []
    path = '.'
    for file in os.listdir(path):
        filename = f"{path}/{file}"
        with open(filename, 'r') as f:
            data = json.loads(f.read())
            frames.append(pd.json_normalize(
                data,
                meta=[
                    'id', 'body', 'created_at',
                    ['user', 'id'],
                    ['user', 'username'],
                    ['entities', 'sentiment', 'basic']
                ]
              )
            )
    df = pd.concat(frames).sort_values(by=['id'])
    twits = df[['id', 'body', 'created_at', 'user.username', 'entities.sentiment.basic']]
