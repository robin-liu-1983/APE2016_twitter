#!/usr/bin/env python
# -*- coding: utf-8 -*-

# To run this code, first edit config.py with your configuration, then:
#
# mkdir data
# python twitter_stream_download.py -q apple -d data
#
# It will produce the list of tweets for the query "apple"
# in the file data/stream_apple.json

import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
# import argparse
import string
import json


class MyListener(StreamListener):
    """Custom StreamListener for streaming data."""

    def __init__(self, data_dir, query):
        query_fname = format_filename(query)
        self.outfile = "%s/stream_%s.json" % (data_dir, query_fname)

    def on_data(self, data):
        try:
            with open(self.outfile, 'a') as f:
                f.write(data)
                print(data)
                return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
            time.sleep(5)
        return True

    def on_error(self, status):
        print(status)
        return True


def format_filename(fname):
    """Convert file name into a safe string.
    Arguments:
        fname -- the file name to convert
    Return:
        String -- converted file name
    """
    return ''.join(convert_valid(one_char) for one_char in fname)


def convert_valid(one_char):
    """Convert a character into '_' if invalid.
    Arguments:
        one_char -- the char to convert
    Return:
        Character -- converted char
    """
    valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
    if one_char in valid_chars:
        return one_char
    else:
        return '_'


@classmethod
def parse(cls, api, raw):
    status = cls.first_parse(api, raw)
    setattr(status, 'json', json.dumps(raw))
    return status

# auth conifguration
consumer_key = 'jsn5YA04k5aq80oQBEqNs3eTO'
consumer_secret = 'yzIa1FJY7vJz9kCqJYqaQaThQc8o4bS5BGxh8rNcR2uAfRh7wp'
access_token = '23399092-hPluWow97IVPNenB3ycbAbklvv8i9CyRfVvtnBjxz'
access_secret = 'EJ7GOsacvmZsDikgPzAaoSbw7SWYV1I4dzv2y5EcVzjil'

# auth conifguration
consumer_key = 'jsn5YA04k5aq80oQBEqNs3eTO'
consumer_secret = 'yzIa1FJY7vJz9kCqJYqaQaThQc8o4bS5BGxh8rNcR2uAfRh7wp'
access_token = '23399092-hPluWow97IVPNenB3ycbAbklvv8i9CyRfVvtnBjxz'
access_secret = 'EJ7GOsacvmZsDikgPzAaoSbw7SWYV1I4dzv2y5EcVzjil'

# twitter stream filter
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

# 'American presidential election 2016'

twitter_data = "APE2016"

# Democratic Party
# name               twitter_name       twitters current   follow        likes
# Hillary Clinton    @HillaryClinton    4,452       634    5,520,000     1,002
name1 = 'HillaryClinton,Hillary'

# Berbie Sanders    @BernieSanders     13,800     1,920     1,530,000     14
name2 = 'BerbieSanders,Sanders'

# Republican Party

# Donald J. Trump   @realDonaldTrump    3,1100      42      6,500,000     66
name3 = 'DonaldTump,Trump'

# Macro Rubio       @MarcoRubio         5,127       2457     1,260,000    1,755
name4 = 'MarcoRubio,Rubio'

# Ted Cruz          @TedCruz            14500       13800     866,000     605
name5 = 'TedCruz,Cruz'


twitter_stream10 = Stream(auth, MyListener("output", twitter_data))

twitter_stream10.filter(
    track=[name1,
           name2,
           name3,
           name4,
           name5], async=True)
