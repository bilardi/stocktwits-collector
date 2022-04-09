import unittest
import os
import json
from datetime import datetime, timedelta
from stocktwits_collector.collector import Collector

class TestService(unittest.TestCase, Collector):
    c = None
    path = None
    is_verbose = None
    chunks = None
    def __init__(self, *args, **kwargs):
        self.c = Collector()
        self.path = "."
        self.is_verbose = True if "VERBOSE" in os.environ and os.environ["VERBOSE"] == 1 else False
        self.chunks = [os.environ["CHUNK"] if "CHUNK" in os.environ and os.environ["CHUNK"] else "day"]
        unittest.TestCase.__init__(self, *args, **kwargs)

    def run_save_history(self, chunk):
        start = datetime.now() - timedelta(days=2)
        if chunk == "week":
            start = datetime.now() - timedelta(days=8)
        elif chunk == "month":
            start = datetime.now() - timedelta(days=33)
        self.c.save_history({"is_verbose": self.is_verbose, "symbols":["TSLA"], "chunk": chunk, "start": start.strftime("%Y-%m-%dT06:54:00Z")})

    def check_files(self, chunk):
        issue = 0
        for file in os.listdir(self.path):
            if file.startswith("history"):
                filename = f"{self.path}/{file}"
                with open(filename, "r") as f:
                    data = json.loads(f.read())
                    cursor_data_salved = self.c.get_cursor(data)
                    if self.is_verbose:
                        print(file, 'salved', cursor_data_salved)
                    data_sorted = sorted(data, key = lambda i: (i['id']), reverse=True)
                    cursor_data_sorted = self.c.get_cursor(data_sorted)
                    if self.is_verbose:
                        print(file, 'sorted', cursor_data_sorted)
                    self.assertEqual(cursor_data_salved, cursor_data_sorted)
                    if not self.c.is_same_chunk(cursor_data_salved["oldest_date"], cursor_data_salved["earliest_date"], chunk):
                        data_cleaned = self.c.clean_history(chunk, cursor_data_salved, data)
                        if self.is_verbose:
                            print('data_cleaned salved', self.c.get_cursor(data_cleaned))
                        data_sorted = sorted(data_cleaned, key = lambda i: (i['id']), reverse=True)
                        if self.is_verbose:
                            print('data_cleaned sorted', self.c.get_cursor(data_sorted))
                        issue += 1
        self.assertEqual(issue, 0)

    def remove_files(self):
        for file in os.listdir(self.path):
            if file.startswith("history"):
                os.remove(file)

    def test_api(self):
        if self.chunks == ["all"]:
            chunks = ["day", "week", "month"]
        for chunk in self.chunks:
            self.run_save_history(chunk)
            self.check_files(chunk)
            self.remove_files()

if __name__ == '__main__':
    unittest.main()
