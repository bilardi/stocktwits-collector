Getting started
===============

Stocktwits collector package is implemented for collecting the twits of Stocktwits on your local.

The goal is to implement this package for each Stocktwits API and to manage how to download many data on more files to avoid networking issues and to require again all data but only the missing part.

It is part of the `educational repositories <https://github.com/pandle/materials>`_ to learn how to write stardard code and common uses of the TDD.

Installation
############

If you want to use this package into your code, you can install by python3-pip:

.. code-block:: bash

    pip3 install stocktwits_collector
    python3
    >>> import stocktwits_collector.collector as Collector
    >>> help(Collector)

Development
###########

The package is not self-consistent. So after to have downloaded the package by github and you have to install the requirements:

.. code-block:: bash

    git clone https://github.com/bilardi/stocktwits-collector
    cd stocktwits-collector/
    pip3 install --upgrade -r requirements.txt

See the documentation to contribute.

Documentation
#############

Read the documentation on `readthedocs <https://stocktwits-collector.readthedocs.io/en/latest/>`_ for

* Usage
* Development

Change Log
##########

See `CHANGELOG.md <https://github.com/bilardi/stocktwits-collector/blob/master/CHANGELOG.md>`_ for details.

License
#######

This package is released under the MIT license.  See `LICENSE <https://github.com/bilardi/stocktwits-collector/blob/master/LICENSE>`_ for details.
