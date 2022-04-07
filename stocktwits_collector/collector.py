"""The class for collecting twits of Stocktwits

    A collection of methods to simplify your downloading
"""
import sys
from contextlib import contextmanager
from io import StringIO
import json
from datetime import datetime, timedelta
import stockTwitFetchAPI.stocktwitapi as st

class Collector():
    ts = None
    def __init__(self):
        """
        the core of API is the package stockTwitFetchAPI with the class twitStreamer
        """
        self.ts = st.twitStreamer()

    @contextmanager
    def hold_output(self):
        """
        hold output

        This method is temporary until PR approval:
        https://github.com/p-hiroshige/stockTwitsAPI/pull/1

            Example:
                with hold_output() as (out, err):
                    method_with_a_print()
                captured_output = out.getvalue().strip()

        """
        new_out, new_err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def there_is_symbol(self, symbols_fetched, symbols_target):
        """
        check if in the message there are the symbols target

            Arguments:
                :symbols_fetched (list of dict): list of symbols
                :symbols_target (list of string): list of symbols names
            Returns:
                a boolean, True if there is at least one symbol of target in the symbols fetched
        """
        for symbol in symbols_fetched:
            if symbol["symbol"] in symbols_target:
                return True
        return False

    def clean_data(self, messages, event):
        """
        clean data

            Arguments:
                :messages (list of dict): list of messages
                :event (dict): dictionary fully described in save_history()
                    symbols (list of str): names of symbols to fetch
                    users (list of str): names of users to fetch
                    only_combo (bool): if True, fetches only messages of those symbols posted from those users
            Returns:
                list of unique dictionaries cleaned
        """
        # unique messages
        messages = list({ message["id"] : message for message in messages }.values())
        if "only_combo" in event and event["only_combo"] == True:
            if "symbols" in event and "users" in event:
                messages = list({ message["id"] : message for message in messages if self.there_is_symbol(message["symbols"], event["symbols"]) and message["user"]["username"] in event["users"] }.values())
        return messages

    def get_data(self, event):
        """
        get data from Stocktwits, default last 30 messages

            Arguments:
                :event (dict): dictionary fully described in save_history()
                    symbols (list of str): names of symbols to fetch
                    users (list of str): names of users to fetch
                    min (int): optional, min ID
                    max (int): optional, max ID
                    limit (int): optional, defalt 30 messages
            Returns:
                list of messages
        """
        messages = []

        if "min" not in event:
            event["min"] = 0

        if "max" not in event:
            event["max"] = 0

        if "limit" not in event:
            event["limit"] = 30

        if "users" in event:
            for user in event["users"]:
                response = self.ts.get_user_msgs(user_id=user, since=event["min"], max=event["max"], limit=event["limit"], callback=None, filter=None)
                messages.extend(response["messages"])

        if "symbols" in event:
            for symbol in event["symbols"]:
                with self.hold_output() as (out, err):
                    try:
                        response = self.ts.get_symbol_msgs(symbol_id=symbol, since=event["min"], max=event["max"], limit=event["limit"], callback=None, filter=None)
                    except Exception as error:
                        print(event)
                        raise Exception(error)
                    messages.extend(response["messages"])
                
        return self.clean_data(messages, event)

    def is_younger(self, first_date, second_date):
        """
        compare a date with a second date

            Argument:
                :first_date (str): datetime with format %Y-%m-%dT%H:%M:%SZ 
                :second_date (str): another date with format %Y-%m-%dT%H:%M:%SZ
            Returns:
                a boolean, True if first date is younger than second one
        """
        first = datetime.strptime(first_date, "%Y-%m-%dT%H:%M:%SZ")
        second = datetime.strptime(second_date, "%Y-%m-%dT%H:%M:%SZ")

        if first <= second:
            return True
        return False

    def is_same_chunk(self, first_date, second_date, chunk = "day"):
        """
        compare a date with a second date

            Argument:
                :first_date (str): datetime with format %Y-%m-%dT%H:%M:%SZ 
                :second_date (str): another date with format %Y-%m-%dT%H:%M:%SZ
                :chunk (str): day, week or month, default day
            Returns:
                a boolean, True if the dates are of the same chunk
        """
        first = datetime.strptime(first_date, "%Y-%m-%dT%H:%M:%SZ")
        second = datetime.strptime(second_date, "%Y-%m-%dT%H:%M:%SZ")
        is_same = False

        if chunk == "day":
            is_same = first.strftime("%Y-%m-%d") == second.strftime("%Y-%m-%d")
        if chunk == "week":
            is_same = first.strftime("%W") == second.strftime("%W")
        if chunk == "month":
            is_same = first.replace(day=1).strftime("%Y-%m-%d") == second.replace(day=1).strftime("%Y-%m-%d")

        return is_same

    def get_cursor(self, messages):
        """
        get cursor with oldest date, min ID and max ID

            Arguments:
                :messages (list[dict]): list of messages
            Returns:
                a dictionary with oldest_date, min ID, earliest_date and max (ID)
        """
        return {
            "oldest_date": messages[-1]["created_at"],
            "min": messages[-1]["id"],
            "earliest_date": messages[0]["created_at"],
            "max": messages[0]["id"]
        }

    def clean_history(self, chunk, cursor, history):
        """
        clean history from messages with different chunk

            Arguments:
                :chunk (str): day, week or month
                :cursor (dict): dictionary with the keys oldest_date, min ID, earliest_date and max (ID)
                :history (list[dict]): list of messages
            Returns:
                history cleaned
        """
        chunk = chunk if chunk in ["day", "week", "month"] else "day"
        same_oldest_date = 0
        same_earliest_date = 0

        for message in history:
            if self.is_same_chunk(message["created_at"], cursor["oldest_date"], chunk):
                same_oldest_date += 1
            if self.is_same_chunk(message["created_at"], cursor["earliest_date"], chunk):
                same_earliest_date += 1

        if len(history) == (same_oldest_date + same_earliest_date):
            current_chunk = cursor["oldest_date"]
            indexes_to_delete = []
            if same_oldest_date > same_earliest_date:
                current_chunk = cursor["earliest_date"]
            for index, message in enumerate(history):
                if self.is_same_chunk(message["created_at"], current_chunk):
                    indexes_to_delete.append(index)
            for index in indexes_to_delete:
                del history[index]

        return history

    def walk(self, event, cursor, history):
        """
        walk along the messages like a shrimp 

            Arguments:
                :event (dict): dictionary fully described in save_history()
                :cursor (dict): dictionary with the keys oldest_date, min ID, earliest_date and max (ID)
                :history (list[dict]): list of messages
            Returns:
                cursor, messages
        """
        event["max"] = cursor["min"]
        messages = self.get_data(event)
        cursor = self.get_cursor(messages)
        chunk = event["chunk"] if "chunk" in event else "day"

        if not self.is_same_chunk(cursor["oldest_date"], cursor["earliest_date"], chunk):
            history = self.clean_history(chunk, cursor, history)
        messages.extend(history)
            
        return cursor, messages

    def get_history(self, event):
        """
        get history from Stocktwist, default last 30 messages

            Arguments:
                :event (dict): dictionary fully described in save_history()
                    start (datetime): optional, min datetime
            Returns:
                list of messages
        """
        history = []
        messages = self.get_data(event)
        history.extend(messages)

        if "start" in event:
            cursor = self.get_cursor(messages)
            while self.is_younger(event["start"], cursor["oldest_date"]) and not event["start"] == cursor["oldest_date"]:
                if "is_verbose" in event and event["is_verbose"] is True:
                    print("get_history", event["start"], cursor["oldest_date"])
                cursor, history = self.walk(event, cursor, history)
        # elif "min" in event and event["min"] > 0:
        #     cursor = self.get_cursor(messages)
        #     while event["min"] < cursor["min"]:
        #         cursor, history = self.walk(event, cursor, history)

        return history

    def get_date(self, chunk, date = None, jump_chunk = False):
        """
        get date at midnight about chunk

            Arguments:
                :chunk (str): day, week or month
                :date (str): datetime with format %Y-%m-%dT%H:%M:%SZ
                :jump_chunk (bool): True if you want to jump one chunk
            Returns:
                string of date at midnight about that chunk or next one
        """
        if date is None:
            current = datetime.now()
        else:
            current = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        jump = 1
        start = current
        if chunk == "week":
            jump = 7
            start = current - timedelta(days=current.weekday())
        elif chunk == "month":
            jump = 0
            start = current.replace(day=1)
        if jump_chunk == True:
            start = start - timedelta(days=jump)
            if chunk == "month":
                month = start.month - 1
                year = start.year
                if month == 0:
                    month = 12
                    year = start.year - 1
                start = start.replace(month=month, year=year)
        return start.strftime("%Y-%m-%dT00:00:00Z")

    def update_event(self, key, value, event):
        """
        update a specific key of event

            Arguments:
                :key (str): attribute name of event
                :value (mix): value you want to replace on that key
                :event (dict): dictionary fully described in save_history()
            Returns:
                dictionary with the attribute named key changed with value
        """
        chunk = {}
        for k in event.keys():
            chunk[k] = event[k]
        chunk[key] = value
        return chunk

    def get_temporary_event(self, messages, current_chunk, event):
        """
        get temporary chunk event from messages

            Arguments:
                :messages (list[dict]): list of messages
                :current_chunk (dict): dictionary fully described in save_history()
                :event (dict): dictionary fully described in save_history()
            Returns:
                the temporary chunk event updated with the partial start and new min
        """
        cursor = self.get_cursor(messages)
        oldest_date = self.get_date(event["chunk"], cursor["oldest_date"])
        if event["start"] == oldest_date:
            oldest_date = self.get_date(event["chunk"], oldest_date, True)
        next_chunk = self.update_event("start", oldest_date, current_chunk)
        if self.is_younger(next_chunk["start"], event["start"]):
            if event["start"] == current_chunk["start"]:
                return next_chunk
            else:
                next_chunk["start"] = event["start"]
        next_chunk["max"] = cursor["max"]
        return next_chunk

    def save_data(self, history, current_chunk, event):
        """
        save data

            Arguments:
                :history (list[dict]): list of messages
                :current_chunk (dict): dictionary like event
                :event (dict): dictionary fully described in save_history()
            Returns:
                the temporary chunk event updated with the partial start and new max
        """
        chunk = datetime.strptime(current_chunk["start"], "%Y-%m-%dT%H:%M:%SZ")
        next_chunk = self.get_temporary_event(history, current_chunk, event)
        cursor = self.get_cursor(history)
        # if cursor["oldest_date"] != cursor["earliest_date"]:
        #   if oldest_date + 1 == earliest_date and 
        if self.get_date(next_chunk["start"]) == self.get_date(cursor["oldest_date"]):
            chunk = datetime.strptime(next_chunk["start"], "%Y-%m-%dT%H:%M:%SZ")

        filename = f'{event["filename_prefix"]}{chunk.strftime("%Y%m%d")}{event["filename_suffix"]}'
        with open(filename, "a") as fh:
            json.dump(history, fh)
        return next_chunk

    def save_history(self, event):
        """
        save history from Stocktwist on files splitted by chunk per day, week or month

            Arguments:
                :event (dict):
                    symbols (list[str]): names of symbols to fetch
                    users (list[str]): names of users to fetch
                    only_combo (bool): optional, if True, fetches only messages of those symbols posted from those users
                    min (int): optional, min ID
                    max (int): optional, max ID
                    limit (int): optional, default 30 messages
                    start (str): optional, min datetime
                    chunk (str): optional (day, week or month), default day
                    filename_prefix (str): optional, default "history."
                    filename_suffix (str): optional, default ".json"
            Returns:
                last temporary chunk event discarded
        """
        history = []
        if "chunk" not in event:
            event["chunk"] = "day"

        if "start" not in event:
            event["start"] = self.get_date(event["chunk"])

        if "filename_prefix" not in event:
            event["filename_prefix"] = "history."

        if "filename_suffix" not in event:
            event["filename_suffix"] = ".json"

        messages = self.get_data(event)
        history.extend(messages)
        cursor = self.get_cursor(messages)
        oldest_date = self.get_date(event["chunk"], cursor["oldest_date"])
        chunk = self.update_event("start", oldest_date, event)

        if "start" in event:
            if "is_verbose" in event and event["is_verbose"] is True:
                print("save_history", event["start"], cursor["oldest_date"])
            while self.is_younger(event["start"], chunk["start"]):
                history = self.get_history(chunk)
                chunk = self.save_data(history, chunk, event)
                if "is_verbose" in event and event["is_verbose"] is True:
                    print("save_history", event["start"], chunk["start"])
                history = []
        # elif "min" in event and event["min"] > 0:
        #     while event["min"] < cursor["min"]:
        #         history = self.get_history(chunk)
        #         chunk = self.save_data(history, chunk, event)
        #         history = []

        return chunk
