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

Without optional parameters, the system downloads the last 30 messages and prints those in the output. If you want to save that on a file (or more files), you have to use at least the **chunk** parameter.

Examples
########

