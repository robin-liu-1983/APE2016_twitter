
>Twitter is a popular social network where users can share short of tweets per day, there’s a lot of data to analyse and to play with.

>This is the first in a series of articles dedicated to mining data on Twitter using Python. In this first part, we’ll see different options to collect data from Twitter. Once we have built a data set, in the next episodes we’ll discuss some interesting data applications.

[toc]

## 1.Collecting data

### 1.1 Register Your App

In order to have access to Twitter data programmatically, we need to create an app that interacts with the Twitter API.

The first step is the registration of your app. In particular, you need to point your browser to *http://apps.twitter.com*, log-in to Twitter (if you’re not already logged in) and register a new application. You can now choose a name and a description for your app (for example “Mining Demo” or similar). You will receive a consumer key and a consumer secret: these are application settings that should always be kept private. From the configuration page of your app, you can also require an access token and an access token secret. Similarly to the consumer keys, these strings must also be kept private: they provide the application access to Twitter on behalf of your account. The default permissions are read-only, which is all we need in our case, but if you decide to change your permission to provide writing features in your app, you must negotiate a new access token.

**Important Note**: there are rate limits in the use of the Twitter API, as well as limitations in case you want to provide a downloadable data-set, see:

*https://dev.twitter.com/overview/terms/agreement-and-policy*
*https://dev.twitter.com/rest/public/rate-limiting*

### 1.2 Accessing the Data

Twitter provides **REST APIs** you can use to interact with their service. There is also a bunch of Python-based clients out there that we can use without re-inventing the wheel. In particular, **Tweepy** in one of the most interesting and straightforward to use, so let’s install it:

```bash
pip install tweepy==3.5.0
```

In order to authorise our app to access Twitter on our behalf, we need to use the OAuth interface:

```python
import tweepy
from tweepy import OAuthHandler
 
consumer_key = 'YOUR-CONSUMER-KEY'
consumer_secret = 'YOUR-CONSUMER-SECRET'
access_token = 'YOUR-ACCESS-TOKEN'
access_secret = 'YOUR-ACCESS-SECRET'
 
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
 
api = tweepy.API(auth)
```

The api variable is now our entry point for most of the operations we can perform with Twitter.

For example, we can read our own timeline (i.e. our Twitter homepage) with:

```python
for status in tweepy.Cursor(api.home_timeline).items(10):
    # Process a single status
    print(status.text) 
```

Tweepy provides the convenient Cursor interface to iterate through different types of objects. In the example above we’re using 10 to limit the number of tweets we’re reading, but we can of course access more. The status variable is an instance of the Status() class, a nice wrapper to access the data. The JSON response from the Twitter API is available in the attribute _json (with a leading underscore), which is not the raw JSON string, but a dictionary.

* So the code above can be re-written to process/store the JSON:

```python
for status in tweepy.Cursor(api.home_timeline).items(10):
    # Process a single status
    process_or_store(status._json) 
```

* What if we want to have a list of all our followers? There you go:

```python
for friend in tweepy.Cursor(api.friends).items():
    process_or_store(friend._json)
```

* And how about a list of all our tweets? Simple:

```python
for tweet in tweepy.Cursor(api.user_timeline).items():
    process_or_store(tweet._json)

```

In this way we can easily collect tweets (and more) and store them in the original JSON format, fairly easy to convert into different data models depending on our storage (many NoSQL technologies provide some bulk import feature).

The function `process_or_store()` is a place-holder for your custom implementation. In the simplest form, you could just print out the JSON, one tweet per line:

```python
def process_or_store(tweet):
    print(json.dumps(tweet))
```

### 1.3 Streaming

In case we want to “keep the connection open”, and gather all the upcoming tweets about a particular event, the streaming API is what we need. We need to extend the StreamListener() to customise the way we process the incoming data. A working example that gathers all the new tweets with the **#python** hashtag:

```python
from tweepy import Stream
from tweepy.streaming import StreamListener
 
class MyListener(StreamListener):
 
    def on_data(self, data):
        try:
            with open('python.json', 'a') as f:
                f.write(data)
                return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True
 
    def on_error(self, status):
        print(status)
        return True
 
twitter_stream = Stream(auth, MyListener())
twitter_stream.filter(track=['#python'])

```

Depending on the search term, we can gather tons of tweets within a few minutes. This is especially true for live events with a world-wide coverage (World Cups, Super Bowls, Academy Awards, you name it), so keep an eye on the JSON file to understand how fast it grows and consider how many tweets you might need for your tests. The above script will save each tweet on a new line, so you can use the command wc -l python.json from a Unix shell to know how many tweets you’ve gathered.

You can see a minimal working example of the Twitter Stream API in the following Gist:

```python
##config.py
consumer_key = 'your-consumer-key'
consumer_secret = 'your-consumer-secret'
access_token = 'your-access-token'
access_secret = 'your-access-secret'

```


```python
##twitter_stream_download.py 
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
import argparse
import string
import config
import json

def get_parser():
    """Get parser for command line arguments."""
    parser = argparse.ArgumentParser(description="Twitter Downloader")
    parser.add_argument("-q",
                        "--query",
                        dest="query",
                        help="Query/Filter",
                        default='-')
    parser.add_argument("-d",
                        "--data-dir",
                        dest="data_dir",
                        help="Output/Data Directory")
    return parser


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

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    auth = OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_secret)
    api = tweepy.API(auth)

    twitter_stream = Stream(auth, MyListener(args.data_dir, args.query))
    twitter_stream.filter(track=[args.query])

```
## 2.Text Pre-processing

### 2.1 The Anatomy of a Tweet

Assuming that you have collected a number of tweets and stored them in JSON as suggested above, let’s have a look at the structure of a tweet:

```python
import json
 
with open('mytweets.json', 'r') as f:
    line = f.readline() # read only the first tweet/line
    tweet = json.loads(line) # load it as Python dict
    print(json.dumps(tweet, indent=4)) # pretty-print

```

The key attributes are the following:

* `text`: the text of the tweet itself
* `created_at`: the date of creation
* `favorite_count`, `retweet_count`: the number of favourites and retweets
* `favorited, retweeted`: boolean stating whether the authenticated user (you) have favourited or retweeted this tweet
* `lang`: acronym for the language (e.g. “en” for english)
* `id`: the tweet identifier
* `place`, coordinates, geo: geo-location information if available
* `user`: the author’s full profile
* `entities`: list of entities like URLs, @-mentions, hashtags and symbols
* `in_reply_to_user_id`: user identifier if the tweet is a reply to a specific user
* `in_reply_to_status_id`: status identifier id the tweet is a reply to a specific status

As you can see there’s a lot of information we can play with. All the `*_id` fields also have a `*_id_str` counterpart, where the same information is stored as a string rather than a big int (to avoid overflow problems). We can imagine how these data already allow for some interesting analysis: we can check who is most favourited/retweeted, who’s discussing with who, what are the most popular hashtags and so on. Most of the goodness we’re looking for, i.e. the content of a tweet, is anyway embedded in the text, and that’s where we’re starting our analysis.

We start our analysis by breaking the text down into words. Tokenisation is one of the most basic, yet most important, steps in text analysis. The purpose of tokenisation is to split a stream of text into smaller units called tokens, usually words or phrases. While this is a well understood problem with several out-of-the-box solutions from popular libraries, Twitter data pose some challenges because of the nature of the language.

### 2.2 How to Tokenise a Tweet Text

Let’s see an example, using the popular **NLTK** library to tokenise a fictitious tweet:

```python
from nltk.tokenize import word_tokenize
 
tweet = 'RT @marcobonzanini: just an example! :D http://example.com #NLP'
print(word_tokenize(tweet))
# ['RT', '@', 'marcobonzanini', ':', 'just', 'an', 'example', '!', ':', 'D', 'http', ':', '//example.com', '#', 'NLP']

```
You will notice some peculiarities that are not captured by a general-purpose English tokeniser like the one from NLTK: **@-mentions**, **emoticons**, **URLs** and **#hash-tags** are not recognised as single tokens. The following code will propose a pre-processing chain that will consider these aspects of the language. 

```python
import re
 
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""
 
regex_str = [
    emoticons_str,
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
 
    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]
    
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)
 
def tokenize(s):
    return tokens_re.findall(s)
 
def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    return tokens
 
tweet = "RT @marcobonzanini: just an example! :D http://example.com #NLP"
print(preprocess(tweet))
# ['RT', '@marcobonzanini', ':', 'just', 'an', 'example', '!', ':D', 'http://example.com', '#NLP']

```

As you can see, **@-mentions**, **emoticons**, **URLs** and **#hash-tags** are now preserved as individual tokens.

If we want to process all our tweets, previously saved on file:

```python
with open('mytweets.json, 'r') as f:
    for line in f:
        tweet = json.loads(line)
        tokens = preprocess(tweet['text'])
        do_something_else(tokens)

```

The tokeniser is probably far from perfect, but it gives you the general idea. The tokenisation is based on regular expressions (regexp), which is a common choice for this type of problem. Some particular types of tokens (e.g. phone numbers or chemical names) will not be captured, and will be probably broken into several tokens. To overcome this problem, as well as to improve the richness of your pre-processing pipeline, you can improve the regular expressions, or even employ more sophisticated techniques like Named Entity Recognition.

The core component of the tokeniser is the regex_str variable, which is a list of possible patterns. In particular, we try to capture some emoticons, HTML tags, Twitter @usernames (@-mentions), Twitter #hashtags, URLs, numbers, words with and without dashes and apostrophes, and finally “anything else”. Please take a moment to observe the regexp for capturing numbers: why don’t we just use \d+? The problem here is that numbers can appear in several different ways, e.g. 1000 can also be written as 1,000 or 1,000.00 — and we can get into more complications in a multi-lingual environment where commas and dots are inverted: “one thousand” can be written as 1.000 or 1.000,00 in many non-anglophone countries. The task of identifying numeric tokens correctly just gives you a glimpse of how difficult tokenisation can be.

The regular expressions are compiled with the flags re.VERBOSE, to allow spaces in the regexp to be ignored (see the multi-line emoticons regexp), and re.IGNORECASE to catch both upper and lowercases. The tokenize() function simply catches all the tokens in a string and returns them as a list. This function is used within preprocess(), which is used as a pre-processing chain: in this case we simply add a lowercasing feature for all the tokens that are not emoticons (e.g. :D doesn’t become :d).

## 3.Term Frequencies

### 3.1 Counting Terms

Assuming we have collected a list of tweets (see Part 1 of the tutorial), the first exploratory analysis that we can perform is a simple word count. In this way, we can observe what are the terms most commonly used in the data set. In this example, I’ll use the set of my tweets, so the most frequent words should correspond to the topics I discuss (not necessarily, but bear with be for a couple of paragraphs).

We can use a custom tokeniser to split the tweets into a list of terms. The following code uses the preprocess() function described in Part 2 of the tutorial, in order to capture Twitter-specific aspects of the text, such as #hashtags, @-mentions, emoticons and URLs. In order to keep track of the frequencies while we are processing the tweets, we can use collections.Counter() which internally is a dictionary (term: count) with some useful methods like most_common():

```python
import operator 
import json
from collections import Counter
 
fname = 'mytweets.json'
with open(fname, 'r') as f:
    count_all = Counter()
    for line in f:
        tweet = json.loads(line)
        # Create a list with all the terms
        terms_all = [term for term in preprocess(tweet['text'])]
        # Update the counter
        count_all.update(terms_all)
    # Print the first 5 most frequent words
    print(count_all.most_common(5))

```

The above code will produce some unimpressive results:

```python
[(':', 44), ('rt', 26), ('to', 26), ('and', 25), ('on', 22)]

```

As you can see, the most frequent words (or should I say, tokens), are not exactly meaningful.

### 3.2 Removing stop-words

In every language, some words are particularly common. While their use in the language is crucial, they don’t usually convey a particular meaning, especially if taken out of context. This is the case of articles, conjunctions, some adverbs, etc. which are commonly called stop-words. In the example above, we can see three common stop-words – to, and and on. Stop-word removal is one important step that should be considered during the pre-processing stages. One can build a custom list of stop-words, or use available lists (e.g. NLTK provides a simple list for English stop-words).

Given the nature of our data and our tokenisation, we should also be careful with all the punctuation marks and with terms like RT (used for re-tweets) and via (used to mention the original author of an article or a re-tweet), which are not in the default stop-word list. 

```python
from nltk.corpus import stopwords
import string
 
punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via']

```

We can now substitute the variable terms_all in the first example with something like:

```python
terms_stop = [term for term in preprocess(tweet['text']) if term not in stop]

```

After counting, sorting the terms and printing the top 5, this is the result:

```python
[('python', 11), ('@miguelmalvarez', 9), ('#python', 9), ('data', 8), ('@danielasfregola', 7)]

```

So apparently I mostly tweet about Python and data, and the users I re-tweet more often are **@miguelmalvarez** and **@danielasfregola**, it sounds about right.

### 3.3 More term filters

Besides stop-word removal, we can further customise the list of terms/tokens we are interested in. Here you have some examples that you can embed in the first fragment of code:

```python
# Count terms only once, equivalent to Document Frequency
terms_single = set(terms_all)
# Count hashtags only
terms_hash = [term for term in preprocess(tweet['text']) 
              if term.startswith('#')]
# Count terms only (no hashtags, no mentions)
terms_only = [term for term in preprocess(tweet['text']) 
              if term not in stop and
              not term.startswith(('#', '@'))] 
              # mind the ((double brackets))
              # startswith() takes a tuple (not a list) if 
              # we pass a list of inputs

```

After counting and sorting, these are my most commonly used hashtags:

```pyton
[('#python', 9), ('#scala', 6), ('#nosql', 4), ('#bigdata', 3), ('#nlp', 3)]

```

and these are my most commonly used terms:

```python
[('python', 11), ('data', 8), ('summarisation', 6), ('twitter', 5), ('nice', 5)]

```

“nice”?

While the other frequent terms represent a clear topic, more often than not simple term frequencies don’t give us a deep explanation of what the text is about. To put things in context, let’s consider sequences of two terms (a.k.a. bigrams). 

```python
from nltk import bigrams 
 
terms_bigram = bigrams(terms_stop)

```

The bigrams() function from NLTK will take a list of tokens and produce a list of tuples using adjacent tokens. Notice that we could use terms_all to compute the bigrams, but we would probably end up with a lot of garbage. In case we decide to analyse longer n-grams (sequences of n tokens), it could make sense to keep the stop-words, just in case we want to capture phrases like “to be or not to be”.

So after counting and sorting the bigrams, this is the result:

```python
[(('nice', 'article'), 4), (('extractive', 'summarisation'), 4), (('summarisation', 'sentence'), 3), (('short', 'paper'), 3), (('paper', 'extractive'), 2)]

```

So apparently I tweet about nice articles (I wouldn’t bother sharing the boring ones) and extractive summarisation (the topic of my PhD dissertation). This also sounds about right.


## 4.Rugby and Term Co-Occurrences

### 4.1 The Application Domain

As the name suggests, six teams are involved in the competition: England, Ireland, Wales, Scotland, France and Italy. This means that we can expect the event to be tweeted in multiple languages (English, French, Italian, Welsh, Gaelic, possibly other languages as well), with English being the major language. Assuming the team names will be mentioned frequently, we could decide to look also for their nicknames, e.g. Les Bleus for France or Azzurri for Italy. During the last day of the competition, three matches are played sequentially. Three teams in particular had a shot for the title: England, Ireland and Wales. At the end, Ireland won the competition but everything was open until the very last minute.

### 4.2 Setting Up

I used the streaming API to download all the tweets containing the string #rbs6nations during the day. Obviously not all the tweets about the event contained the hashtag, but this is a good baseline. The time frame for the download was from around 12:15PM to 7:15PM GMT, that is from about 15 minutes before the first match, to about 15 minutes after the last match was over. At the end, more than 18,000 tweets have been downloaded in JSON format, making for about 75Mb of data. This should be small enough to quickly do some processing in memory, and at the same time big enough to observe something possibly interesting.

The textual content of the tweets has been pre-processed with tokenisation and lowercasing using the preprocess() function introduced in Part 2 of the tutorial.

### 4.3 Interesting terms and hashtags

Following what we discussed in Part 3 (Term Frequencies), we want to observe the most common terms and hashtags used during day. If you have followed the discussion about creating different lists of tokens in order to capture terms without hashtags, hashtags only, removing stop-words, etc. you can play around with the different lists.

This is the unsurprising list of top 10 most frequent terms (terms_only in Part 3) in the data set.

```python
[('ireland', 3163), ('england', 2584), ('wales', 2271), ('…', 2068), ('day', 1479), ('france', 1380), ('win', 1338), ('rugby', 1253), ('points', 1221), ('title', 1180)]

```

The first three terms correspond to the teams who had a go for the title. The frequencies also respect the order in the final table. The fourth term is instead a punctuation mark that we missed and didn’t include in the list of stop-words. This is because string.punctuation only contains ASCII symbols, while here we’re dealing with a unicode character. If we dig into the data, there will be more examples like this, but for the moment we don’t worry about it.

After adding the suspension-points symbol to the list of stop-words, we have a new entry at the end of the list:

```python
[('ireland', 3163), ('england', 2584), ('wales', 2271), ('day', 1479), ('france', 1380), ('win', 1338), ('rugby', 1253), ('points', 1221), ('title', 1180), ('🍀', 1154)]

```

Interestingly, a new token we didn’t account for, **an Emoji symbol** (in this case, the Irish Shamrock).

If we have a look at the most common hashtags, we need to consider that #rbs6nations will be by far the most common token (that’s our search term for downloading the tweets), so we can exclude it from the list. This leave us with:

```python
[('#engvfra', 1701), ('#itavwal', 927), ('#rugby', 880), ('#scovire', 692), ('#ireland', 686), ('#angfra', 554), ('#xvdefrance', 508), ('#crunch', 500), ('#wales', 446), ('#england', 406)]

```

We can observe that the most common hashtags, a part from #rugby, are related to the individual matches. In particular England v France has received the highest number of mentions, probably being the last match of the day with a dramatic finale. Something interesting to notice is that a fair amount of tweets also contained terms in French: the count for #angfra should in fact be added to #engvfra. Those unfamiliar with rugby probably wouldn’t recognise that also #crunch should be included with #EngvFra match, as Le Crunch is the traditional name for this event. So by far, the last match has received a lot of attention.

### 4.4 Term co-occurrences

Sometimes we are interested in the terms that occur together. This is mainly because the context gives us a better insight about the meaning of a term, supporting applications such as word disambiguation or semantic similarity. We discussed the option of using bigrams in the previous article, but we want to extend the context of a term to the whole tweet.

We can refactor the code from the previous article in order to capture the co-occurrences. We build a co-occurrence matrix com such that **com[x][y]** contains the number of times the term x has been seen in the same tweet as the term y:

```python
from collections import defaultdict
# remember to include the other import from the previous post
 
com = defaultdict(lambda : defaultdict(int))
 
# f is the file pointer to the JSON data set
for line in f: 
    tweet = json.loads(line)
    terms_only = [term for term in preprocess(tweet['text']) 
                  if term not in stop 
                  and not term.startswith(('#', '@'))]
 
    # Build co-occurrence matrix
    for i in range(len(terms_only)-1):            
        for j in range(i+1, len(terms_only)):
            w1, w2 = sorted([terms_only[i], terms_only[j]])                
            if w1 != w2:
                com[w1][w2] += 1

```

While building the co-occurrence matrix, we don’t want to count the same term pair twice, e.g. com[A][B] == com[B][A], so the inner for loop starts from i+1 in order to build a triangular matrix, while sorted will preserve the alphabetical order of the terms.

For each term, we then extract the 5 most frequent co-occurrent terms, creating a list of tuples in the form ((term1, term2), count):

```python
com_max = []
# For each term, look for the most common co-occurrent terms
for t1 in com:
    t1_max_terms = max(com[t1].items(), key=operator.itemgetter(1))[:5]
    for t2 in t1_max_terms:
        com_max.append(((t1, t2), com[t1][t2]))
# Get the most frequent co-occurrences
terms_max = sorted(com_max, key=operator.itemgetter(1), reverse=True)
print(terms_max[:5])

```

The results:

```python
[(('6', 'nations'), 845), (('champions', 'ireland'), 760), (('nations', 'rbs'), 742), (('day', 'ireland'), 731), (('ireland', 'wales'), 674)]

```

This implementation is pretty straightforward, but depending on the data set and on the use of the matrix, one might want to look into tools like scipy.sparse for building a sparse matrix.

We could also look for a specific term and extract its most frequent co-occurrences. We simply need to modify the main loop including an extra counter, for example:

```python
search_word = sys.argv[1] # pass a term as a command-line argument
count_search = Counter()
for line in f:
    tweet = json.loads(line)
    terms_only = [term for term in preprocess(tweet['text']) 
                  if term not in stop 
                  and not term.startswith(('#', '@'))]
    if search_word in terms_only:
        count_search.update(terms_only)
print(&quot;Co-occurrence for %s:&quot; % search_word)
print(count_search.most_common(20))

```

The outcome for “ireland”:

```python
[('champions', 756), ('day', 727), ('nations', 659), ('wales', 654), ('2015', 638), ('6', 613), ('rbs', 585), ('http://t.co/y0nvsvayln', 559), ('🍀', 526), ('10', 522), ('win', 377), ('england', 377), ('twickenham', 361), ('40', 360), ('points', 356), ('sco', 355), ('ire', 355), ('title', 346), ('scotland', 301), ('turn', 295)]

```

The outcome for “rugby”:

```python
[('day', 476), ('game', 160), ('ireland', 143), ('england', 132), ('great', 105), ('today', 104), ('best', 97), ('well', 90), ('ever', 89), ('incredible', 87), ('amazing', 84), ('done', 82), ('amp', 71), ('games', 66), ('points', 64), ('monumental', 58), ('strap', 56), ('world', 55), ('team', 55), ('http://t.co/bhmeorr19i', 53)]

```

Overall, quite interesting.

## 5.Data Visualisation Basics

A picture is worth a thousand tweets: more often than not, designing a good visual representation of our data, can help us make sense of them and highlight interesting insights. After collecting and analysing Twitter data, the tutorial continues with some notions on data visualisation with Python.

### 5.1 From Python to Javascript with Vincent

While there are some options to create plots in Python using libraries like matplotlib or ggplot, one of the coolest libraries for data visualisation is probably D3.js which is, as the name suggests, based on Javascript. D3 plays well with web standards like CSS and SVG, and allows to create some wonderful interactive visualisations.

Vincent bridges the gap between a Python back-end and a front-end that supports D3.js visualisation, allowing us to benefit from both sides. The tagline of Vincent is in fact “The data capabilities of Python. The visualization capabilities of JavaScript”. Vincent, a Python library, takes our data in Python format and translates them into Vega, a JSON-based visualisation grammar that will be used on top of D3. It sounds quite complicated, but it’s fairly simple and pythonic. You don’t have to write a line in Javascript/D3 if you don’t want to.

Firstly, let’s install **Vincent**:

```bash
sudo pip install vincent

```

Secondly, let’s create our first plot. Using the _list of most frequent terms_ (without hashtags) from our _rugby data set_, we want to plot their frequencies:

```python
import vincent
 
word_freq = count_terms_only.most_common(20)
labels, freq = zip(*word_freq)
data = {'data': freq, 'x': labels}
bar = vincent.Bar(data, iter_idx='x')
bar.to_json('term_freq.json')

```

At this point, the file term_freq.json will contain a description of the plot that can be handed over to D3.js and Vega. A simple template (taken from Vincent resources) to visualise the plot:

```html
<html>  
<head>    
    <title>Vega Scaffold</title>
    <script src="http://d3js.org/d3.v3.min.js" charset="utf-8"></script>
    <script src="http://d3js.org/topojson.v1.min.js"></script>
    <script src="http://d3js.org/d3.geo.projection.v0.min.js" charset="utf-8"></script>
    <script src="http://trifacta.github.com/vega/vega.js"></script>
</head>
<body>
    <div id="vis"></div>
</body>
<script type="text/javascript">
// parse a spec and create a visualization view
function parse(spec) {
  vg.parse.spec(spec, function(chart) { chart({el:"#vis"}).update(); });
}
parse("term_freq.json");
</script>
</html>

```

Save the above HTML page as chart.html and run the simple Python web server:

```bash
python -m http.server 8888 # Python 3
python -m SimpleHTTPServer 8888 # Python 2

```

Now you can open your browser at _http://localhost:8888/chart.html_and observe the result:

![](http://robin.info-lab.top/wp-content/uploads/2016/02/term_freq.png)

Notice: you could save the HTML template directly from Python with:

```python
bar.to_json('term_freq.json', html_out=True, html_path='chart.html')

```

but, at least in Python 3, the output is not a well formed HTML and you’d need to manually strip some characters.

With this procedure, we can plot many different types of charts with Vincent. Let’s take a moment to browse the docs and see its capabilities.

### 5.2 Time Series Visualisation

Another interesting aspect of analysing data from Twitter is the possibility to observe the distribution of tweets over time. In other words, if we organise the frequencies into temporal buckets, we could observe how Twitter users react to real-time events.

One of my favourite tools for data analysis with Python is Pandas, which also has a fairly decent support for time series. As an example, let’s track the hashtag #ITAvWAL to observe what happened during the first match.

Firstly, if we haven’t done it yet, we need to install Pandas:

```bash
sudo pip install pandas

```

In the main loop which reads all the tweets, we simply track the occurrences of the hashtag, i.e. we can refactor the code from the previous episodes into something similar to:

```python
import pandas
import json
 
dates_ITAvWAL = []
# f is the file pointer to the JSON data set
for line in f:
    tweet = json.loads(line)
    # let's focus on hashtags only at the moment
    terms_hash = [term for term in preprocess(tweet['text']) if term.startswith('#')]
    # track when the hashtag is mentioned
    if '#itavwal' in terms_hash:
        dates_ITAvWAL.append(tweet['created_at'])
 
# a list of "1" to count the hashtags
ones = [1]*len(dates_ITAvWAL)
# the index of the series
idx = pandas.DatetimeIndex(dates_ITAvWAL)
# the actual series (at series of 1s for the moment)
ITAvWAL = pandas.Series(ones, index=idx)
 
# Resampling / bucketing
per_minute = ITAvWAL.resample('1Min', how='sum').fillna(0)

```

The last line is what allows us to track the frequencies over time. The series is re-sampled with intervals of 1 minute. This means all the tweets falling within a particular minute will be aggregated, more precisely they will be summed up, given how='sum'. The time index will not keep track of the seconds anymore. If there is no tweet in a particular minute, the *fillna()* function will fill the blanks with zeros.

To put the time series in a plot with Vincent:

```python
time_chart = vincent.Line(ITAvWAL)
time_chart.axis_titles(x='Time', y='Freq')
time_chart.to_json('time_chart.json')

```

Once you embed the time_chart.json file into the HTML template discussed above, you’ll see this output:

![](http://robin.info-lab.top/wp-content/uploads/2016/02/time1.png)

The interesting moments of the match are observable from the spikes in the series. The first spike just before 1pm corresponds to the first Italian try. All the other spikes between 1:30 and 2:30pm correspond to Welsh tries and show the Welsh dominance during the second half. The match was over by 2:30, so after that Twitter went quiet.

Rather than just observing one sequence at a time, we could compare different series to observe how the matches has evolved. So let’s refactor the code for the time series, keeping track of the three different hashtags #ITAvWAL, #SCOvIRE and #ENGvFRA into the corresponding pandas.Series. 

```python
# all the data together
match_data = dict(ITAvWAL=per_minute_i, SCOvIRE=per_minute_s, ENGvFRA=per_minute_e)
# we need a DataFrame, to accommodate multiple series
all_matches = pandas.DataFrame(data=match_data,
                               index=per_minute_i.index)
# Resampling as above
all_matches = all_matches.resample('1Min', how='sum').fillna(0)
 
# and now the plotting
time_chart = vincent.Line(all_matches[['ITAvWAL', 'SCOvIRE', 'ENGvFRA']])
time_chart.axis_titles(x='Time', y='Freq')
time_chart.legend(title='Matches')
time_chart.to_json('time_chart.json')

```

And the output:

![](http://robin.info-lab.top/wp-content/uploads/2016/02/time2.png)

We can immediately observe when the different matches took place (approx 12:30-2:30, 2:30-4:30 and 5-7) and we can see how the last match had the all the attentions, especially in the end when the winner was revealed.


## 6.Sentiment Analysis Basics

Sentiment Analysis is one of the interesting applications of text analytics. Although the term is often associated with sentiment classification of documents, broadly speaking it refers to the use of text analytics approaches applied to the set of problems related to identifying and extracting subjective material in text sources.

### 6.1 A Simple Approach for Sentiment Analysis

The technique we’re discussing in this post has been elaborated from the traditional approach proposed by Peter Turney in his paper Thumbs Up or Thumbs Down? Semantic Orientation Applied to Unsupervised Classification of Reviews. A lot of work has been done in Sentiment Analysis since then, but the approach has still an interesting educational value. In particular, it is intuitive, simple to understand and to test, and most of all unsupervised, so it doesn’t require any labelled data for training.

Firstly, we define the Semantic Orientation (SO) of a word as the difference between its associations with positive and negative words. In practice, we want to calculate “how close” a word is with terms like good and bad. The chosen measure of “closeness” is Pointwise Mutual Information (PMI), calculated as follows (t1 and t2 are terms):

$PMI ( t_{1}, t_{2} ) = log( \dfrac{P(t_{1} \wedge t_{2})}{P(t_{1}) \cdot P(t_{2})}) $

In Turney’s paper, the SO of a word was calculated against excellent and poor, but of course we can extend the vocabulary of positive and negative terms. Using V^{+} and a vocabulary of positive terms and V^{-} for the negative ones, the Semantic Orientation of a term t is hence defined as:

$SO(t) = \Sigma_{t^{'}\in{V^{+}}}PMI(t^{}, t^{ ' }) - \Sigma_{t^{'}\in{V^{-}}} PMI(t^{}, t^{ ' })$

We can build our own list of positive and negative terms, or we can use one of the many resources available on-line, for example the opinion lexicon by Bing Liu.

### 6.2 Computing Term Probabilities

In order to compute$P(t)$(the probability of observing the term t) and $P(t_1 \wedge t_2)$ (the probability of observing the terms t1 and t2 occurring together) we can re-use some previous code to calculate term frequencies and term co-occurrences. Given the set of documents (tweets) D, we define the Document Frequency (DF) of a term as the number of documents where the term occurs. The same definition can be applied to co-occurrent terms. Hence, we can define our probabilities as:


$P(t) = \frac{\mbox{DF}(t)}{|D|}$
$P(t_1 \wedge t_2) = \frac{\mbox{DF}(t_1 \wedge t_2)}{|D|}$

In the previous articles, the document frequency for single terms was stored in the dictionaries count_single and count_stop_single (the latter doesn’t store stop-words), while the document frequency for the co-occurrencies was stored in the co-occurrence matrix com

This is how we can compute the probabilities:

```python
# n_docs is the total n. of tweets
p_t = {}
p_t_com = defaultdict(lambda : defaultdict(int))
 
for term, n in count_stop_single.items():
    p_t[term] = n / n_docs
    for t2 in com[term]:
        p_t_com[term][t2] = com[term][t2] / n_docs

```

### 6.3 Computing the Semantic Orientation

Given two vocabularies for positive and negative terms:

```python
positive_vocab = [
    'good', 'nice', 'great', 'awesome', 'outstanding',
    'fantastic', 'terrific', ':)', ':-)', 'like', 'love',
    # shall we also include game-specific terms?
    # 'triumph', 'triumphal', 'triumphant', 'victory', etc.
]
negative_vocab = [
    'bad', 'terrible', 'crap', 'useless', 'hate', ':(', ':-(',
    # 'defeat', etc.
]

```

We can compute the PMI of each pair of terms, and then compute the
Semantic Orientation as described above:

```python
pmi = defaultdict(lambda : defaultdict(int))
for t1 in p_t:
    for t2 in com[t1]:
        denom = p_t[t1] * p_t[t2]
        pmi[t1][t2] = math.log2(p_t_com[t1][t2] / denom)
 
semantic_orientation = {}
for term, n in p_t.items():
    positive_assoc = sum(pmi[term][tx] for tx in positive_vocab)
    negative_assoc = sum(pmi[term][tx] for tx in negative_vocab)
    semantic_orientation[term] = positive_assoc - negative_assoc

```

The Semantic Orientation of a term will have a positive (negative) value if the term is often associated with terms in the positive (negative) vocabulary. The value will be zero for neutral terms, e.g. the PMI’s for positive and negative balance out, or more likely a term is never observed together with other terms in the positive/negative vocabularies.

We can print out the semantic orientation for some terms:

```python
semantic_sorted = sorted(semantic_orientation.items(), 
                         key=operator.itemgetter(1), 
                         reverse=True)
top_pos = semantic_sorted[:10]
top_neg = semantic_sorted[-10:]
 
print(top_pos)
print(top_neg)
print("ITA v WAL: %f" % semantic_orientation['#itavwal'])
print("SCO v IRE: %f" % semantic_orientation['#scovire'])
print("ENG v FRA: %f" % semantic_orientation['#engvfra'])
print("#ITA: %f" % semantic_orientation['#ita'])
print("#FRA: %f" % semantic_orientation['#fra'])
print("#SCO: %f" % semantic_orientation['#sco'])
print("#ENG: %f" % semantic_orientation['#eng'])
print("#WAL: %f" % semantic_orientation['#wal'])
print("#IRE: %f" % semantic_orientation['#ire'])

```

Different vocabularies will produce different scores. Using the opinion lexicon from Bing Liu, this is what we can observed on the Rugby data-set:

```
# the top positive terms
[('fantastic', 91.39950482011552), ('@dai_bach', 90.48767241244532), ('hoping', 80.50247748725415), ('#it', 71.28333427277785), ('days', 67.4394844955977), ('@nigelrefowens', 64.86112716005566), ('afternoon', 64.05064208341855), ('breathtaking', 62.86591435212975), ('#wal', 60.07283361352875), ('annual', 58.95378954406133)]
# the top negative terms
[('#england', -74.83306534609066), ('6', -76.0687215594536), ('#itavwal', -78.4558633116863), ('@rbs_6_nations', -80.89363516601993), ("can't", -81.75379628180468), ('like', -83.9319149443813), ('10', -85.93073078165587), ('italy', -86.94465165178258), ('#engvfra', -113.26188957010228), ('ball', -161.82146824640125)]
# Matches
ITA v WAL: -78.455863
SCO v IRE: -73.487661
ENG v FRA: -113.261890
# Individual team
#ITA: 53.033824
#FRA: 14.099372
#SCO: 4.426723
#ENG: -0.462845
#WAL: 60.072834
#IRE: 19.231722

```

### 6.4 Some Limitations

The PMI-based approach has been introduced as simple and intuitive, but of course it has some limitations. The semantic scores are calculated on terms, meaning that there is no notion of “entity” or “concept” or “event”. For example, it would be nice to aggregate and normalise all the references to the team names, e.g. #ita, Italy and Italia should all contribute to the semantic orientation of the same entity. Moreover, do the opinions on the individual teams also contribute to the overall opinion on a match?

Some aspects of natural language are also not captured by this approach, more notably modifiers and negation: how do we deal with phrases like not bad (this is the opposite of just bad) or very good (this is stronger than just good)? 

## 7.Geolocation and Interactive Maps

Geolocation is the process of identifying the geographic location of an object such as a mobile phone or a computer. Twitter allows its users to provide their location when they publish a tweet, in the form of latitude and longitude coordinates. With this information, we are ready to create some nice visualisation for our data, in the form of interactive maps.

This article briefly introduces the GeoJSON format and Leaflet.js, a nice Javascript library for interactive maps, and discusses its integration with the Twitter data we have collected in the previous parts of this tutorial (see Part 4 for details on the rugby data set).

### 7.1 GeoJSON

GeoJSON is a format for encoding geographic data structures. The format supports a variety of geometric types that can be used to visualise the desired shapes onto a map. For our examples, we just need the simplest structure, a Point. A point is identified by its coordinates (latitude and longitude).

In GeoJSON, we can also represent objects such as a Feature or a FeatureCollection. The first one is basically a geometry with additional properties, while the second one is a list of features.

Our Twitter data set can be represented in GeoJSON as a FeatureCollection, where each tweet would be an individual Feature with its one geometry (the aforementioned Point).

This is how the JSON structure looks like:

```python
{
    "type": "FeatureCollection",
    "features": [
        { 
            "type": "Feature",
            "geometry": {
                "type": "Point", 
                "coordinates": [some_latitude, some_longitude]
            },
            "properties": {
                "text": "This is sample a tweet",
                "created_at": "Sat Mar 21 12:30:00 +0000 2015"
            }
        },
        /* more tweets ... */
    ]
}

```

### 7.2 From Tweets to GeoJSON

Assuming the data are stored in a single file as described in the first chapter of this tutorial, we simply need to iterate all the tweets looking for the coordinates field, which may or may not be present. Keep in mind that you need to use coordinates, because the geo field is deprecated (see the API).

This code will read the data set, looking for tweets where the coordinates are explicitely given. Once the GeoJSON data structure is created (in the form of a Python dictionary), then the data are dumped into a file called geo_data.json:

```python
# Tweets are stored in "fname"
with open(fname, 'r') as f:
    geo_data = {
        "type": "FeatureCollection",
        "features": []
    }
    for line in f:
        tweet = json.loads(line)
        if tweet['coordinates']:
            geo_json_feature = {
                "type": "Feature",
                "geometry": tweet['coordinates'],
                "properties": {
                    "text": tweet['text'],
                    "created_at": tweet['created_at']
                }
            }
            geo_data['features'].append(geo_json_feature)
 
# Save geo data
with open('geo_data.json', 'w') as fout:
    fout.write(json.dumps(geo_data, indent=4))

```

### 7.3 Interactive Maps with Leaflet.js

Leaflet.js is an open-source Javascript library for interactive maps. You can create maps with tiles of your choice (e.g. from OpenStreetMap or MapBox), and overlap interactive components.

In order to prepare a web page that will host a map, you simply need to include the library and its CSS, by putting in the head section of your document the following lines:

```html
<link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.css" />
<script src="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.js"></script>

```

Moreover, we have all our GeoJSON data in a separate file, so we want to load the data dynamically rather than manually put all the points in the map. For this purpose, we can easily play with jQuery, which we also need to include:

```html
<script src="http://code.jquery.com/jquery-2.1.0.min.js"></script>

```

The map itself will be placed into a div element:

```html
<!-- this goes in the <head> -->
<style>
#map {
    height: 600px;
}
</style>
<!-- this goes in the <body> -->
<div id="map"></div>

```

We’re now ready to create the map with Leaflet: 

```js
// Load the tile images from OpenStreetMap
var mytiles = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
});
// Initialise an empty map
var map = L.map('map');
// Read the GeoJSON data with jQuery, and create a circleMarker element for each tweet
// Each tweet will be represented by a nice red dot
$.getJSON("./geo_data.json", function(data) {
    var myStyle = {
        radius: 2,
        fillColor: "red",
        color: "red",
        weight: 1,
        opacity: 1,
        fillOpacity: 1
    };
 
    var geojson = L.geoJson(data, {
        pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng, myStyle);
        }
    });
    geojson.addTo(map)
});
// Add the tiles to the map, and initialise the view in the middle of Europe
map.addLayer(mytiles).setView([50.5, 5.0], 5);

```

A screenshot of the results:

![](http://robin.info-lab.top/wp-content/uploads/2016/02/rugby-map-osm.png)

The above example uses OpenStreetMap for the tile images, but Leaflet lets you choose other services. For example, in the following screenshot the tiles are coming from MapBox. 

![](http://robin.info-lab.top/wp-content/uploads/2016/02/rugby-map-mapbox.png)

You can see the interactive maps in action here:

 [ Tiles from OpenStreetMap](http://bonzanini.github.io/mining-twitter/rugby-osm.html)  
 [Tiles from MapBox](http://bonzanini.github.io/mining-twitter/rugby-mapbox.html)  
 
 **参考 http://marcobonzanini.com 博客中的相关文章，转发请注明**
