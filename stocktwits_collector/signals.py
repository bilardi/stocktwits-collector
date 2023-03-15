"""The class for adding signals from Stocktwits Sentiment

    A collection of methods to make your signals
"""
import datetime
import pandas as pd

class Signals():

    def convert_datetime(self, date):
        """
        convert datetime from created_at to Datetime type

            Arguments:
                :date (str): date of created_at
            Returns:
                a datetime
        """
        new_date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        return new_date

    def convert_sentiment(self, sentiment):
        """
        convert Stocktwits Sentiment from string to number

            Arguments:
                :sentiment (str): Bullish or Bearish string
            Returns:
                a number: 1 for Bullish, -1 for Bearish, 0 for anything else
        """
        if sentiment == 'Bullish':
            return 1
        if sentiment == 'Bearish':
            return -1
        return 0

    def details(self, prefix, sentiment, twits):
        """
        add features in your DataFrame about datetime and simple Stocktwits Sentiment statistics

            Arguments:
                :prefix (str): prefix of the new features name
                :sentiment (str): feature name of Stocktwits Sentiment
                :twits (DataFrame): DataFrame of twits with at least Stocktwits created_at feature and Stocktwits Sentiment
            Returns:
                a DataFrame with the new features:
                datetime, date, time, hour, {prefix}_number, {prefix}_total_cum, {prefix}_day_cum, {prefix}_hour_cum
        """
        for feature in ['datetime', 'date', 'time', 'hour', f'{prefix}_number', f'{prefix}_total_cum', f'{prefix}_day_cum', f'{prefix}_hour_cum']:
            if feature in twits.keys():
                raise Warning('The feature named {} is already present: this method overwrites it!'.format(feature))
            
        twits['datetime'] = twits['created_at'].apply(self.convert_datetime)
        twits['date'] = twits['datetime'].dt.strftime('%Y-%m-%d')
        twits['time'] = twits['datetime'].dt.strftime('%H:%M:%SZ')
        twits['hour'] = twits['datetime'].dt.strftime('%Y-%m-%dT%H:59:59Z')

        twits[f'{prefix}_number'] = twits[sentiment].apply(self.convert_sentiment)
        twits[f'{prefix}_total_cum'] = twits[f'{prefix}_number'].cumsum()
        twits[f'{prefix}_day_cum'] = twits.groupby(['date'])[f'{prefix}_number'].cumsum()
        twits[f'{prefix}_hour_cum'] = twits.groupby(['hour'])[f'{prefix}_number'].cumsum()

        return twits

    def bull_bear_ratios(self, prefix, groupby, sentiment, twits, ema_list = []):
        """
        add features in your DataFrame about Bullish/Bearish Ratio and related EMAs

            Arguments:
                :prefix (str): prefix of the new features name
                :groupby (str): feature name used within groupby with sentiment
                :sentiment (str): feature name of Stocktwits Sentiment
                :twits (DataFrame): DataFrame of twits with at least Stocktwits body and created_at features and Stocktwits Sentiment
                :ema_list (list of int): default is empty
            Returns:
                a DataFrame with the new features:
                {prefix}_bull, {prefix}_bear, {prefix}_bb_ratio and {prefix}_bb_ratio_{ema} for ema in ema_list
        """
        features = [f'{prefix}_bull', f'{prefix}_bear', f'{prefix}_bb_ratio']
        for ema in ema_list:
            features.append(f'{prefix}_bb_ratio_{ema}')
        for feature in features:
            if feature in twits.keys():
                raise Warning('The feature named {} is already present: this method overwrites it!'.format(feature))

        sentiments = twits[sentiment].unique()
        for s in ['Bearish', 'Bullish']:
            if s not in sentiments:
                raise Exception('Stocktwits Sentiment named {} not found'.format(s))

        bull_bear_df = twits.groupby([groupby, sentiment]).agg({'body': 'count'}).unstack().reset_index()
        bull_bear_df.sort_values(groupby, inplace=True)
        bull_bear_df['Bull/Bear Ratio'] = (bull_bear_df[('body', 'Bullish')]) / (bull_bear_df[('body', 'Bearish')])
        
        bb = pd.DataFrame()
        bb[groupby] = bull_bear_df[groupby]
        bb[f'{prefix}_bull'] = bull_bear_df[('body','Bullish')]
        bb[f'{prefix}_bear'] = bull_bear_df[('body','Bearish')]
        bb[f'{prefix}_bb_ratio'] = bull_bear_df['Bull/Bear Ratio']

        for ema in ema_list:
            exp_ema = bb[f'{prefix}_bb_ratio'].ewm(com=0.5, adjust=False).mean()
            bb[f'{prefix}_bb_ratio_{ema}'] = exp_ema
        
        return twits.merge(bb)

    def add_signals(self, prefix, sentiment, twits, ema_list = [5, 6, 7, 8, 9, 10, 15, 20]):
        """
        add features in your DataFrame about datetime, statistics of Stocktwits Sentiment and related EMAs

            Arguments:
                :prefix (str): prefix of the new features name
                :sentiment (str): feature name of Stocktwits Sentiment
                :twits (DataFrame): DataFrame of twits with at least Stocktwits body and created_at features and Stocktwits Sentiment
                :ema_list (list of int): default is [5, 6, 7, 8, 9, 10, 15, 20]
            Returns:
                a DataFrame with the new features:
                datetime, date, time, hour, {prefix}_number, {prefix}_total_cum, {prefix}_day_cum, {prefix}_hour_cum,
                {prefix}_bull, {prefix}_bear, {prefix}_bb_ratio and {prefix}_bb_ratio_{ema} for ema in ema_list
        """
        twits = self.details(prefix, sentiment, twits)
        twits = self.bull_bear_ratios(f'{prefix}_day', 'date', sentiment, twits, ema_list)
        twits = self.bull_bear_ratios(f'{prefix}_hour', 'hour', sentiment, twits, ema_list)
        return twits
