Development
===========

The package uses the Stocktwits API manages three type of streas: user, symbol and conversation. Now the package manages the user and symbol streams.

You can contribute to implement other functionalities by a Pull Request to master branch.

Run tests
#########

.. code-block:: bash

    cd stocktwits-collector/
    pip3 install --upgrade -r requirements.txt
    python3 -m unittest discover -v

Run make
########

Makefile is useful for many actions:

* run the unit test by ``make unittest``
* run the doc build by ``make doc``

Prepare a Pull Request (PR)
###########################

You can fork the repository in your space and then you can clone your copy in your local to change and run tests.

.. code-block:: bash

    cd stocktwits-collector/
    pip3 install --upgrade -r requirements.txt
    python3 -m unittest discover -v
    git checkout -b your-branch
    git add files-changed
    git commit -m "describe your changes here"
    git push origin push your-branch

You can create the `PR from your fork <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>`_.
