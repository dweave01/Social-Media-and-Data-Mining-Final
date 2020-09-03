# See also http://www.laurentluce.com/posts/twitter-sentiment-analysis-using-python-and-nltk/
# The purpose here is to automatically classify a tweet as positive or negative
# The classifier needs to be trained and to do that, we need a list of manually classified tweets.
# Let's start with 5 positive tweets and 5 negative tweets.

from nltk import *

pos_tweets = [('I love this car', 'positive'),
              ('This view is amazing', 'positive'),
              ('I feel great this morning', 'positive'),
              ('I am so excited about the concert', 'positive'),
              ('He is my best friend', 'positive')] 

neg_tweets = [('I do not like this car', 'negative'),
              ('This view is horrible', 'negative'),
              ('I feel tired this morning', 'negative'),
              ('I am not looking forward to the concert', 'negative'),
              ('He is my enemy', 'negative')]

# We take both of those lists and create a single list of tuples each containing two elements.
# First element is an array containing the words and second element is the type of sentiment.
# We get rid of the words smaller than 2 characters and we use lowercase for everything.

tweets = []

for (words, sentiment) in pos_tweets + neg_tweets:
    words_filtered = [e.lower() for e in words.split() if len(e) >= 3]
    tweets.append((words_filtered, sentiment))

# print tweets

test_tweets = ['I feel happy this morning',
               'Larry is my friend',
               'I do not like that man',
               'My house is not great',
               'Your song is annoying']

# The list of word features need to be extracted from the tweets.
# It is a list with every distinct words ordered by frequency of appearance.
# We use the following function to get the list plus the two helper functions.

def get_words_in_tweets(tweets):
    all_words = []
    for (words, sentiment) in tweets:
        all_words += words
    return all_words

all_words = get_words_in_tweets(tweets)

def get_word_features(wordlist):
    wordlist = FreqDist(wordlist)
    # word_features = wordlist.keys() # careful here
    word_features = [w for (w, c) in wordlist.most_common(2000)] #use most_common() if you want to select the most frequent words
    return word_features

word_features = get_word_features(get_words_in_tweets(tweets))
print(word_features)

def extract_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features

training_set = [(extract_features(d), c) for (d,c) in tweets]
# print training_set

# Or, alternatively, training_set = classify.apply_features(extract_features, tweets) 

# Now that we have our training set, we can train our classifier.
classifier = NaiveBayesClassifier.train(training_set)

# We can display the most informative features for our classifier using the method show_most_informative_features.
classifier.show_most_informative_features(100) # default 10
print

# Now that we have our classifier trained, we can use it to classify a (new) tweet and see what the sentiment type output is.
for t in test_tweets:
    # print "{0} : {1}".format(t, classifier.classify(extract_features(t.split())))
    print ("{0} : {1}".format(t, classifier.classify(extract_features([e.lower() for e in t.split() if len(e) >= 3]))))



    
