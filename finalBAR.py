#Birds of a Feather Flock Together
#CIS 400 Term Project
#Code referenced from Anthony Perna HW2 (Only the crawler portion) 

import twitter
import json
import re
import time
from nltk import *
import sys
import itertools
import networkx as nx
import matplotlib.pyplot as plt
def oauth_login():
    
    CONSUMER_KEY = 'KzxmfUDz9Di17E3kbOMNgsvaW'
    CONSUMER_SECRET = 'AZcPsqFFgSSXXrZuHLkJMYf04UHOQRPQX4ugJyMLfvJNLVMxbh'
    OAUTH_TOKEN = '939585304708644864-PGOeiebcmRSmhMfw67HsKIjQ5BXLXzp'
    OAUTH_TOKEN_SECRET = 'LPBzsF9Zq117XZKrPX874wX3q56FFiGZZ7EcBcnI05dZA'
    
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                               CONSUMER_KEY, CONSUMER_SECRET)
    
    twitter_api = twitter.Twitter(auth=auth)
    return twitter_api


twitter_api = oauth_login()    

####################################################################### function from cookbook 
def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): 

    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
    
        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e
    
        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes
    
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429: 
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'\
                  .format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise

print(twitter_api)
###############################Above section signs in and handles errors (Borrowed from professor cookbook)
#This section gathers the users followers
from functools import partial
#from sys import maxsize as maxint
maxint=5000
def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None), \
    "Must have screen_name or user_id, but not both"
    
    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters
    
    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, 
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids, 
                                count=5000)

    friends_ids, followers_ids = [], []
    
    for twitter_api_func, limit, ids, label in [
                    [get_friends_ids, friends_limit, friends_ids, "friends"], 
                    [get_followers_ids, followers_limit, followers_ids, "followers"]
                ]:
        
        if limit == 0: continue
        
        cursor = -1
        while cursor != 0:
        
            # Use make_twitter_request via the partially bound callable...
            if screen_name: 
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else: # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']
        
            print('Fetched {0} total {1} ids for {2}'.format(len(ids),\
                  label, (user_id or screen_name)),file=sys.stderr)
        
            # XXX: You may want to store data during each iteration to provide an 
            # an additional layer of protection from exceptional circumstances
        
            if len(ids) >= limit or response is None:
                break
    
    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]
 
####################################################################Function From Cookbook
def get_user_profile(twitter_api, screen_names=None, user_ids=None):
    
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None), \
    "Must have screen_names or user_ids, but not both"
    
    items_to_info = {}

    items = screen_names or user_ids
    
    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See http://bit.ly/2Gcjfzr for details.
        
        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup, 
                                            screen_name=items_str)
        else: # user_ids
            response = make_twitter_request(twitter_api.users.lookup, 
                                            user_id=items_str)
    
      #  for user_info in response:
         #   if screen_names:
            #    items_to_info[user_info['screen_name']] = user_info
         #   else: # user_ids
            #    items_to_info[user_info['id']] = user_info Commented this because it was causing errors with my code

    return response
############################################################ My function, used to get 5 most popular users 
def get_five_best(screen_name=None, user_id=None):
    
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api, screen_name=screen_name, user_id=user_id) #find friends/followers
    
    friends_ids, followers_ids = set(friends_ids), set(followers_ids) #Changing data to a set

    mutual=(friends_ids.intersection(followers_ids)) #finds mutual friends (Intersection of the set) 

    print(str(len(mutual)) + ' Mutual Friends') #how many mutual friends the user has
    items=[]
    for word in mutual: #convert items to string
        items.append(word)

    people=(get_user_profile(twitter_api, user_ids=items)) #lookup each of the mutual friends (get all of their profiles) 
        
    new=[]
    for thing in people: #this loop obtains the id anf followers count of each user 
        a=(thing['id'])
        b=(thing['followers_count'])
        new.append((b,a)) #then stores the pair as a tuple
    
    new.sort(reverse=True) #Sort users by followers amount (Greatest to least)
    
    #with open('testFile.txt', 'w+') as filehandle: #write info to file
            #filehandle.write('%s\n' % new) #I wrote to file to test output

    fiveBest=[val[1] for val in new] #take ids only from the pairs
    final=fiveBest[:3] #keep only the top 3
    print("The three most popular friends are: "+ str(final)) #output ids of the top 3
    return final
###################################################### cookbook function
def harvest_user_timeline(twitter_api, screen_name=None, user_id=None, max_results=1000):

    assert (screen_name != None) != (user_id != None),     "Must have screen_name or user_id, but not both"

    kw = {  # Keyword args for the Twitter API call
        'count': 200,
        'trim_user': 'true',
        'include_rts' : 'true',
        'since_id' : 1
        }

    if screen_name:
        kw['screen_name'] = screen_name
    else:
        kw['user_id'] = user_id

    max_pages = 16
    results = []

    tweets = make_twitter_request(twitter_api.statuses.user_timeline, **kw)

    if tweets is None: # 401 (Not Authorized) - Need to bail out on loop entry
        tweets = []

    results += tweets

    print('Fetched {0} tweets'.format(len(tweets)), file=sys.stderr)

    page_num = 1

    # Many Twitter accounts have fewer than 200 tweets so you don't want to enter
    # the loop and waste a precious request if max_results = 200.

    # Note: Analogous optimizations could be applied inside the loop to try and
    # save requests. e.g. Don't make a third request if you have 287 tweets out of
    # a possible 400 tweets after your second request. Twitter does do some
    # post-filtering on censored and deleted tweets out of batches of 'count', though,
    # so you can't strictly check for the number of results being 200. You might get
    # back 198, for example, and still have many more tweets to go. If you have the
    # total number of tweets for an account (by GET /users/lookup/), then you could
    # simply use this value as a guide.

    if max_results == kw['count']:
        page_num = max_pages # Prevent loop entry

    while page_num < max_pages and len(tweets) > 0 and len(results) < max_results:

        # Necessary for traversing the timeline in Twitter's v1.1 API:
        # get the next query's max-id parameter to pass in.
        # See https://dev.twitter.com/docs/working-with-timelines.
        kw['max_id'] = min([ tweet['id'] for tweet in tweets]) - 1

        tweets = make_twitter_request(twitter_api.statuses.user_timeline, **kw)
        results += tweets

        print('Fetched {0} tweets'.format(len(tweets)),file=sys.stderr)

        page_num += 1

    print('Done fetching tweets', file=sys.stderr)

    return results[:max_results]

###################################################### where I perform operations with the info
screen_name=input("Enter user you would like to research: ") #can do this to start with any user
nodeNum= input("How many people do you want in your network? ")
nodeNum=int(nodeNum)
wordNum= input("How many common words do you want to find? ")
wordNum=int(wordNum)
#screen_name= 'aperna499' #Use myself as the starting point
start=make_twitter_request(twitter_api.users.lookup, 
                                screen_name=screen_name) #lookup starting user
for tweet in start:
    og=(tweet['id']) #storing current starters ID 
    
final=get_five_best(screen_name=screen_name) #run get five best on the starter
everyone= []
everyone.append(og)

lastList=[] #create total list to store the nodes
lastList.append(og) #store initial user into a completed person list

#for num in final:
   # lastList.append(num)

G=nx.Graph() #initialize graph
G.add_node(og) #add node for starting user

toDo=[] #list of items to research 
for x in final: #add nodes and edges for best 5 followers
    G.add_node(x) 
    G.add_edge(og,x) #connect to the starter (5 best) 
    toDo.append(x)#put those 5 into to do list
    everyone.append(x)
    
##########################################################
#crawler implementation    

for unit in toDo: #for all to do list items
    if len(toDo)<=nodeNum: #while 100 nodes have not been collected 
        lastList.append(unit)
        try:
            here=(get_five_best(user_id=unit)) #run 5 best on currently looked at user
            for y in here: #add nodes and edges for best 5 followers
                G.add_node(y) 
                G.add_edge(unit,y) #connect these 5 to the initial
                toDo.append(y) #add these 5 to the todo list
                everyone.append(y)
        except:
            print("Error Found! Bypassing.......") #if error is found, pass it and print this
            
    else:
          toDo=toDo #once complete do nothing

##########################################################
def clean_tweet(tweet): #referenced from https://www.geeksforgeeks.org/twitter-sentiment-analysis-using-python/
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) |(\w+://\S+)", " ", tweet).split())
def deEmojify(inputString):
        return inputString.encode('ascii', 'ignore').decode('ascii')
    
#sentiment alaysis segment (borrowed code from professor's SA tweets file)                            
tweetList=[]
for person in everyone:
        tweets=harvest_user_timeline(twitter_api, user_id=person, max_results=50)
        for tweet in tweets:
            data = str(tweet['text'])
            cleaned=clean_tweet(tweet=data)
            cleaner=deEmojify(inputString=cleaned)
            tweetList.append(cleaner)
            
tweets = []
for words in tweetList:
    words_filtered = [e.lower() for e in words.split() if len(e) >= 4]
    tweets.append(words_filtered)


def get_words_in_tweets(tweets):
    all_words = []
    for (words) in tweets:
        all_words += words
    return all_words

all_words = get_words_in_tweets(tweets)

def get_word_features(wordlist):
    wordlist = FreqDist(wordlist)
    sendIt=[]
    word_features = [(w,c) for (w, c) in wordlist.most_common(2000)] #use most_common() if you want to select the most frequent words
    for statement in word_features:
        sendIt.append(statement)
    return (sendIt)

word_features = get_word_features(get_words_in_tweets(tweets))
#print(word_features)

bad_words= ["this", "that", "have", "just", "with", "where", "your", "when", "ever", "dont't", "don’t","dont","like","what","will","they",
            "here","their","&amp","other","think","from","about","made","know"] #non helpful words are filtered out
ending=[]
with open('tweetOutput.txt', 'w+') as filehandle:            
    for (item, c) in word_features:
        if item in bad_words:
            continue
        else:
            filehandle.write('%s,%d\n' % (item,c))
            ending.append((item,c))

thing = ending[:wordNum]
for x in thing:
    print(x,end=" ")
    
#####################################################################
nx.draw(G) #draw graph of network
print(" ")
print('Number of nodes: ' + str(G.number_of_nodes())) #total number of nodes, (to show at leat 100 have been collected)
print('Number of edges: ' + str(G.number_of_edges()))
plt.savefig("finalgraph.png") #save and then show graph
plt.show()       
####################################################################
#separate words and their count
words=[]
count=[]
for (item,c) in thing:
    words.append(item)
    count.append(c)
####################################################################
#create graph of words
fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.bar(words,count)
ax.set_title("Word Frequency")
ax.set_xlabel("Words Used")
ax.set_ylabel("Amount Used")
plt.savefig("barGraph.png") #save and then show graph
plt.show()
