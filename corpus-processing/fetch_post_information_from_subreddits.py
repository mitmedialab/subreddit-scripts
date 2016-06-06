import simplejson as json
from collections import defaultdict
from dateutil import parser
import datetime
import math
import sys
import csv
import numpy as np
import numpy as np

import praw
import string
import random
import re
from os import listdir
from os.path import isfile, join

## CONNECT TO REDDIT
r = praw.Reddit(user_agent='')
r.set_oauth_app_info(client_id='',
                     client_secret='',
                     redirect_uri='')

## LOAD SUBREDDIT LIST
path = "/mas/u/jnmatias/projects/arrow_reddit_survival/subreddits/"
commentfiles = [f for f in listdir(path) if isfile(join(path, f))]

sub_files = {}
for f in commentfiles:
    subgroup = re.search("(.*)\.", f)
    sub = subgroup.group(1)
    sub_files[sub]=f

output_path = "/mas/u/jnmatias/projects/arrow_reddit_survival/subreddit_posts/"
removed = []
for f in [f for f in listdir(output_path) if isfile(join(output_path, f))]:
    subgroup = re.search("(.*)_", f)
    sub = subgroup.group(1)
    if sub in sub_files.keys():
        del sub_files[sub]
        sys.stdout.write(".")
    else:
        sys.stdout.write("x")
    removed.append(sub)
    sys.stdout.flush()
    
  
## TODO: EXCLUDE SUBREDDITS THAT ALREADY EXIST IN THE FOLDER OF SUBREDDIT POSTS
        
def generate_post_json_for_subreddit(filename):
#    filename = "/mas/u/jnmatias/projects/arrow_reddit_survival/subreddits/t5_31h78.json"
    filename = "/mas/u/jnmatias/projects/arrow_reddit_survival/subreddits/"+filename
    print "====LOADING===="
    print filename
    bots = ['[deleted]', 'AutoModerator', 'autowikibot', 'TweetsInCommentsBot',
            'TweetPoster', 'TotesMessanger', 'PriceZombie',
            '500pxBot', 'TrollaBot', 'RemindMeBot', 'Mentioned_Videos']

    linecounter = 0
    user_comments = defaultdict(list)
    posts = defaultdict(list)

    for line in open(filename, 'r'):
        linecounter +=1
        if linecounter % 100000 == 0:
            sys.stdout.write(".")#str(counter) + ", ")
            sys.stdout.flush()
        comment = json.loads(line)
        posts[comment['link_id']].append(comment)
        author = comment['author']
        if author in bots:
            continue
        user_comments[author].append(comment)
    print "Total Users: " + str(len(user_comments.values()))
    print "Total Comments: " + str(linecounter)
    print "Total Posts: " + str(len(posts.keys()))
    
    print "Querying Posts"
    counter = 0
    all_posts = {}
    keys = posts.keys()
    for i in range(0,len(posts.keys())/10):
        cur_keys = []
        for y in range(i*10,(i+1)*10):
            cur_keys.append(keys[y])
        for post in r.get_info(thing_id=cur_keys):
            counter +=1
            if counter % 100 == 0:
                sys.stdout.write(".")#str(counter) + ", ")
                sys.stdout.flush()
            pdict = post.__dict__
            del pdict['subreddit']
            del pdict['reddit_session']
            author  = pdict['author']
            del pdict['author']
            try:
                pdict['author_id']=author.id
                pdict['author_name']=author.name
                pdict['author_created']=author.created
                pdict['author_comment_karma']=author.comment_karma
                pdict['author_link_karma']=author.link_karma

            except:
                pdict['author_id']=pdict['author_name']=pdict['author_created']=pdict['author_karma']= pdict['author_link_karma'] = None
            all_posts[pdict['id']] = pdict

    ## OUTPUT TO POSTS JSON        
    s = user_comments.values()[0][0]['subreddit_id']
    fd = open("/mas/u/jnmatias/projects/arrow_reddit_survival/subreddit_posts/" + s + "_posts.json", "w")
    for post in all_posts.values():
        fd.write(json.dumps(post) + "\n")
    fd.close()  

onlyfiles = sub_files.values()

for i in range(0,len(onlyfiles)):
    f = random.choice(onlyfiles)
    onlyfiles.remove(f)
    generate_post_json_for_subreddit(f)
