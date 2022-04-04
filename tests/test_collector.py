import unittest
import json
from datetime import datetime
from stocktwits_collector.collector import Collector

class Streamer():
    um = None
    umh = None
    umb = None
    uma = None
    umt = None
    cum = 0
    sm = None
    smh = None
    smb = None
    sma = None
    smt = None
    def __init__(self):
        self.um = None
        with open('tests/user-msgs-all.json') as json_file:
            self.um = json.load(json_file)
        with open('tests/user-msgs-head.json') as json_file:
            self.umh = json.load(json_file)
        with open('tests/user-msgs-before.json') as json_file:
            self.umb = json.load(json_file)
        with open('tests/user-msgs-after.json') as json_file:
            self.uma = json.load(json_file)
        with open('tests/user-msgs-tail.json') as json_file:
            self.umt = json.load(json_file)
        with open('tests/symbol-msgs-all.json') as json_file:
            self.sm = json.load(json_file)
        with open('tests/symbol-msgs-head.json') as json_file:
            self.smh = json.load(json_file)
        with open('tests/symbol-msgs-before.json') as json_file:
            self.smb = json.load(json_file)
        with open('tests/symbol-msgs-after.json') as json_file:
            self.sma = json.load(json_file)
        with open('tests/symbol-msgs-tail.json') as json_file:
            self.smt = json.load(json_file)
    def get_user_msgs(self, user_id, since, max, limit, callback=None, filter=None):
        if max == 0:
            return {"messages": self.umh}
        if max == 449480585 or max == 449480803:
            return {"messages": self.umb}
        if max == 449480293:
            return {"messages": self.uma}
        if max == 449479692:
            return {"messages": self.umt}
        #return {"messages": self.umt}
    def get_symbol_msgs(self, symbol_id, since, max, limit, callback=None, filter=None):
        if max == 0:
            return {"messages": self.smh}
        if max == 449484164:
            return {"messages": self.smb}
        if max == 449483787:
            return {"messages": self.sma}
        if max == 449483718:
            return {"messages": self.smt}
        #return {"messages": self.smt}

class TestService(unittest.TestCase, Collector):
    c = None
    def __init__(self, *args, **kwargs):
        self.c = Collector()
        self.c.ts = Streamer()
        unittest.TestCase.__init__(self, *args, **kwargs)

    def test_there_is_symbol(self):
        twits = [{"id": 1, "symbol": "APPL"}, {"symbol": "TSLA"}]
        self.assertFalse(self.c.there_is_symbol(twits, ["AMZN"]))
        self.assertTrue(self.c.there_is_symbol(twits, ["TSLA"]))

    def test_clean_data(self):
        twits = [{"id": 1}, {"id": 1}, {"id": 2}]
        self.assertEqual(len(twits), 3)
        self.assertEqual(len(self.c.clean_data(twits, {})), 2)
        # @todo: only_combo test

    def test_get_data(self):
        event = {"users": ["ChartMill"], "since": 449479095, "limit": 2}
        self.assertEqual(self.c.get_data(event), self.c.ts.umh)
        event = {"symbols": ["TSLA"], "since": 449483123, "limit": 2}
        self.assertEqual(self.c.get_data(event), self.c.ts.smh)

    def test_is_younger(self):
        self.assertFalse(self.c.is_younger("2022-02-25T06:54:00Z", "2022-02-16T20:10:00Z"))
        self.assertTrue(self.c.is_younger("2022-02-16T20:10:00Z", "2022-02-25T06:54:00Z"))

    def test_get_cursor(self):
        twits = [{"id": 2, "created_at": "2022-02-25T06:54:00Z"}, {"id": 1, "created_at": "2022-02-16T20:10:00Z"}]
        self.assertEqual(self.c.get_cursor(twits), {"oldest_date": "2022-02-16T20:10:00Z", "since": 1, "max": 2})

    def test_walk(self):
        cursor = {"since": 449480803}
        event = {"users": ["ChartMill"]}
        history = self.c.get_data(event)
        cursor, messages = self.c.walk(event, cursor, history)
        self.assertEqual(cursor, {"oldest_date": "2022-04-03T16:26:00Z", "since": 449480293, "max": 449480488})
        self.assertEqual(history[-1]["id"], messages[-1]["id"])
        self.assertEqual(messages[0]["id"], cursor["max"])

    def test_get_history(self):
        event = {"users": ["ChartMill"], "created_at": "2022-04-03T16:20:00Z"}
        self.assertEqual(self.c.get_history(event), self.c.ts.um)
        event = {"symbols": ["TSLA"], "created_at": "2022-04-03T17:01:11Z"}
        self.assertEqual(self.c.get_history(event), self.c.ts.sm)
        # @todo: since test

    def test_get_date(self):
        date = datetime.now()
        self.assertEqual(self.c.get_date("day"), date.strftime("%Y-%m-%dT00:00:00Z"))
        self.assertEqual(self.c.get_date("day", "2022-02-25T06:54:00Z"), "2022-02-25T00:00:00Z")
        self.assertEqual(self.c.get_date("day", "2022-02-25T06:54:00Z", True), "2022-02-24T00:00:00Z")
        self.assertEqual(self.c.get_date("week", "2022-02-25T06:54:00Z"), "2022-02-21T00:00:00Z")
        self.assertEqual(self.c.get_date("week", "2022-02-25T06:54:00Z", True), "2022-02-14T00:00:00Z")
        self.assertEqual(self.c.get_date("month", "2022-02-25T06:54:00Z"), "2022-02-01T00:00:00Z")
        self.assertEqual(self.c.get_date("month", "2022-02-25T06:54:00Z", True), "2022-01-01T00:00:00Z")
        self.assertEqual(self.c.get_date("month", "2022-01-25T06:54:00Z", True), "2021-12-01T00:00:00Z")

    def test_update_event(self):
        self.assertEqual(self.c.update_event("a", "1", {}), {"a": "1"})
        self.assertEqual(self.c.update_event("a", "1", {"a": "A"}), {"a": "1"})
        self.assertEqual(self.c.update_event("a", "1", {"a": "A", "b": "B"}), {"a": "1", "b": "B"})

    def test_get_temporary_event(self):
        event = {"users": ["ChartMill"], "created_at": "2022-04-01T16:20:00Z", "chunk": "day"}
        messages = self.c.get_data(event)
        self.assertEqual(self.c.get_temporary_event(messages, event, event), {"users": ["ChartMill"], "created_at": "2022-04-03T00:00:00Z", "chunk": "day", "since": 0, "max": 449480803, "limit": 100})

        event = {"users": ["ChartMill"], "created_at": "2022-04-03T00:00:00Z", "chunk": "day"}
        current_chunk = {"users": ["ChartMill"], "created_at": "2022-04-03T00:00:00Z", "chunk": "day", "since": 0, "max": 0, "limit": 100}
        self.assertEqual(self.c.get_temporary_event(messages, current_chunk, event), {"users": ["ChartMill"], "created_at": "2022-04-02T00:00:00Z", "chunk": "day", "since": 0, "max": 0, "limit": 100})

        event = {"users": ["ChartMill"], "created_at": "2022-04-03T00:00:00Z", "chunk": "day"}
        current_chunk = {"users": ["ChartMill"], "created_at": "2022-04-04T00:00:00Z", "chunk": "day", "since": 0, "max": 0, "limit": 100}
        self.assertEqual(self.c.get_temporary_event(messages, current_chunk, event), {"users": ["ChartMill"], "created_at": "2022-04-03T00:00:00Z", "chunk": "day", "since": 0, "max": 449480803, "limit": 100})

        event = {"users": ["ChartMill"], "created_at": "2022-04-04T16:30:00Z", "chunk": "day"}
        current_chunk = {"users": ["ChartMill"], "created_at": "2022-04-03T16:20:00Z", "chunk": "day", "since": 0, "max": 0, "limit": 100}
        self.assertEqual(self.c.get_temporary_event(messages, current_chunk, event), {"users": ["ChartMill"], "created_at": "2022-04-04T16:30:00Z", "chunk": "day", "since": 0, "max": 449480803, "limit": 100})

if __name__ == '__main__':
    unittest.main()
