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
        get data from Stocktwits, default last 100 messages

            Arguments:
                :event (dict): dictionary fully described in save_history()
                    symbols (list of str): names of symbols to fetch
                    users (list of str): names of users to fetch
                    since (int): optional, min ID
                    max (int): optional, max ID
                    limit (int): optional, defalt 100 messages
            Returns:
                list of messages
        """
        messages = []

        if "since" not in event:
            event["since"] = 0

        if "max" not in event:
            event["max"] = 0

        if "limit" not in event:
            event["limit"] = 100

        if "users" in event:
            for user in event["users"]:
                response = self.ts.get_user_msgs(user_id=user, since=event["since"], max=event["max"], limit=event["limit"], callback=None, filter=None)
                messages.extend(response["messages"])

        if "symbols" in event:
            for symbol in event["symbols"]:
                with self.hold_output() as (out, err):
                    try:
                        response = self.ts.get_symbol_msgs(symbol_id=symbol, since=event["since"], max=event["max"], limit=event["limit"], callback=None, filter=None)
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

    def get_cursor(self, messages):
        """
        get cursor with oldest date, min ID and max ID

            Arguments:
                :messages (list[dict]): list of messages
            Returns:
                a dictionary with oldest_date, since (min ID) and max (ID)
        """
        return {
            "oldest_date": messages[-1]["created_at"],
            "since": messages[-1]["id"],
            "max": messages[0]["id"]
        }

    def walk(self, event, cursor, history):
        """
        walk along the messages like a shrimp 

            Arguments:
                :event (dict): dictionary fully described in save_history()
                :cursor (dict): dictionary with the keys oldest_date, since (min ID) and max (ID)
                :history (list[dict]): list of messages
            Returns:
                cursor, messages
        """
        event["max"] = cursor["since"]
        messages = self.get_data(event)
        cursor = self.get_cursor(messages)
        messages.extend(history)
        return cursor, messages

    def get_history(self, event):
        """
        get history from Stocktwist, default last 100 messages

            Arguments:
                :event (dict): dictionary fully described in save_history()
                    created_at (datetime): optional, min datetime
            Returns:
                list of messages
        """
        history = []
        messages = self.get_data(event)
        history.extend(messages)

        if "created_at" in event:
            cursor = self.get_cursor(messages)
            while self.is_younger(event["created_at"], cursor["oldest_date"]) and not event["created_at"] == cursor["oldest_date"]:
                if "is_verbose" in event and event["is_verbose"] is True:
                    print("get_history", event["created_at"], cursor["oldest_date"])
                cursor, history = self.walk(event, cursor, history)
        # elif "since" in event and event["since"] > 0:
        #     cursor = self.get_cursor(messages)
        #     while event["since"] < cursor["since"]:
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
                the temporary chunk event updated with the partial created_at and new since
        """
        cursor = self.get_cursor(messages)
        oldest_date = self.get_date(event["chunk"], cursor["oldest_date"])
        if oldest_date == event["created_at"]:
            oldest_date = self.get_date(event["chunk"], oldest_date, True)
        next_chunk = self.update_event("created_at", oldest_date, current_chunk)
        if self.is_younger(next_chunk["created_at"], event["created_at"]):
            if event["created_at"] == current_chunk["created_at"]:
                return next_chunk
            else:
                next_chunk["created_at"] = event["created_at"]
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
                the temporary chunk event updated with the partial created_at and new max
        """
        chunk = datetime.strptime(current_chunk["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        next_chunk = self.get_temporary_event(history, current_chunk, event)
        cursor = self.get_cursor(history)
        if self.get_date(next_chunk["created_at"]) == self.get_date(cursor["oldest_date"]):
            chunk = datetime.strptime(next_chunk["created_at"], "%Y-%m-%dT%H:%M:%SZ")

        filename = f'{event["filename_prefix"]}{chunk.strftime("%Y%m%d")}{event["filename_suffix"]}'
        with open(filename, "a") as fh:
            json.dump(history, fh)
        return next_chunk

    def save_history(self, event):
        """
        save history recovered by Collector class from Stocktwist, default last 100 messages on files splitted by chunk per day, week or month

            Arguments:
                :event (dict):
                    symbols (list[str]): names of symbols to fetch
                    users (list[str]): names of users to fetch
                    only_combo (bool): optional, if True, fetches only messages of those symbols posted from those users
                    since (int): optional, min ID
                    max (int): optional, max ID
                    limit (int): optional, default 100 messages
                    created_at (str): optional, min datetime
                    chunk (str): optional (day, week or month), default day
                    filename_prefix (str): optional, default "history."
                    filename_suffix (str): optional, default ".json"
            Returns:
                last temporary chunk event discarded
        """
        history = []
        if "chunk" not in event:
            event["chunk"] = "day"

        if "created_at" not in event:
            event["created_at"] = self.get_date(event["chunk"])

        if "filename_prefix" not in event:
            event["filename_prefix"] = "history."

        if "filename_suffix" not in event:
            event["filename_suffix"] = ".json"

        messages = self.get_data(event)
        history.extend(messages)
        cursor = self.get_cursor(messages)
        oldest_date = self.get_date(event["chunk"], cursor["oldest_date"])
        chunk = self.update_event("created_at", oldest_date, event)

        if "created_at" in event:
            if "is_verbose" in event and event["is_verbose"] is True:
                print("save_history", event["created_at"], cursor["oldest_date"])
            while self.is_younger(event["created_at"], chunk["created_at"]):
                history = self.get_history(chunk)
                chunk = self.save_data(history, chunk, event)
                if "is_verbose" in event and event["is_verbose"] is True:
                    print("save_history", event["created_at"], chunk["created_at"])
                history = []
        # elif "since" in event and event["since"] > 0:
        #     while event["since"] < cursor["since"]:
        #         history = self.get_history(chunk)
        #         chunk = self.save_data(history, chunk, event)
        #         history = []

        return chunk
