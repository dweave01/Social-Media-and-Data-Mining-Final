

import twitter
import json
import flask #imported this because a cookbook function used it
import time
import sys
import itertools
import networkx as nx
import matplotlib.pyplot as plt
def oauth_login():
    
    CONSUMER_KEY = 'TmeoHNR9yqbX0cxOMimFa3xts'
    CONSUMER_SECRET = 'b2T9f3lcrVQPwJLP9fMeCo5dCNX3JOPtP8j2cnJMHSLjC9mwrR'
    OAUTH_TOKEN = '1039911526931607552-8TsAaSBYUL5OEoW8nnk4nBLAw3o7ve'
    OAUTH_TOKEN_SECRET = 'dqXmzGZQxdJdQObhTnfZ4JhCKCX2QiuoDihiHheGCIZwL'
    
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
    final=fiveBest[:3] #keep only the top 5
    print("The three most popular friends are: "+ str(final)) #output ids of the top 5
    return final

###################################################### where I perform operations with the info
screen_name=input("Enter user you would like to research: ") #can do this to start with any user
nodeNum= input("How many people do you want in your network? ")
nodeNum=int(nodeNum)
#screen_name= 'aperna499' #Use myself as the starting point
start=make_twitter_request(twitter_api.users.lookup, 
                                screen_name=screen_name) #lookup starting user
for tweet in start:
    og=(tweet['id']) #storing current starters ID 
    
final=get_five_best(screen_name=screen_name) #run get five best on the starter

lastList=[] #create total list to store the 100 nodes
lastList.append(og) #store initial user into a completed person list

#for num in final:
   # lastList.append(num)

G=nx.Graph() #initialize graph
G.add_node(og) #add node for starting user

toDo=[] #list of items to research 
everyone=[]
everyone.append(og)
for x in final: #add nodes and edges for best 5 followers
    G.add_node(x) 
    G.add_edge(og,x) #connect to the starter (5 best) 
    toDo.append(x) #put those 5 into to do list
    
########################################################## 
#my crawler implementation    

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
nx.draw(G) #draw graph
print("Graph diameter: " + str(nx.diameter(G))) #graph diameter
print("Graph average distance: " + str(nx.average_shortest_path_length(G))) #avg distance
print('Number of nodes: ' + str(G.number_of_nodes())) #total number of nodes, (to show at leat 100 have been collected)
print('Number of edges: ' + str(G.number_of_edges()))
print(everyone)
plt.savefig("finalgraph.png") #save and then show graph
plt.show()       
            

