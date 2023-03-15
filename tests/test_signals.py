import unittest
import pandas as pd
from datetime import datetime
from stocktwits_collector.signals import Signals

class TestService(unittest.TestCase, Signals):
    s = None
    def __init__(self, *args, **kwargs):
        self.s = Signals()
        unittest.TestCase.__init__(self, *args, **kwargs)

    def test_convert_datetime(self):
        created_at = '2020-01-01T00:00:00Z'
        self.assertTrue(isinstance(self.s.convert_datetime(created_at), datetime))

    def test_convert_sentiment(self):
        self.assertEqual(self.s.convert_sentiment('Bullish'), 1)
        self.assertEqual(self.s.convert_sentiment('Bearish'), -1)
        self.assertEqual(self.s.convert_sentiment('anything else'), 0)

    def add_signals(self, twits):
        prefix = 'my_prefix'
        ema_list = [5, 10]
        features = ['id', 'body', 'created_at', 'sentiment', 'likes', 'user_id']
        self.assertCountEqual(twits.keys(), features)
        self.assertListEqual(twits.keys().to_list(), features)
        twits_enriched = self.s.add_signals(prefix, 'sentiment', twits, ema_list)
        for feature in ['datetime', 'date', 'time', 'hour']:
            features.append(feature)
        for ly in ['day', 'hour']:
            pf = f'{prefix}_{ly}'
            for feature in [f'{pf}_number', f'{pf}_total_cum', f'{pf}_day_cum', f'{pf}_hour_cum', f'{pf}_bull', f'{pf}_bear', f'{pf}_bb_ratio']:
                features.append(feature)
            for ema in ema_list:
                features.append(f'{pf}_bb_ratio_{ema}')
        self.assertCountEqual(twits_enriched.keys(), features)
        self.assertListEqual(twits_enriched.keys().to_list(), features)

    def test_csv_ok(self):
        twits = pd.read_csv('tests/collection-ok.csv')
        self.add_signals(twits)

    def test_csv_ko(self):
        twits = pd.read_csv('tests/collection-ko.csv')
        self.assertRaises(Exception, lambda: self.add_signals(twits))

if __name__ == '__main__':
    unittest.main()
