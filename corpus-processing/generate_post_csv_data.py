import simplejson as json
from collections import defaultdict
from dateutil import parser
import datetime
import matplotlib.pyplot as plt   # Matplotlib for plotting
import math
import heapq
import sys
import csv
import numpy as np
import pandas as pd
import numpy as np

import string
import re

bots = ['[deleted]', 'AutoModerator', 'autowikibot', 'TweetsInCommentsBot',
            'TweetPoster', 'TotesMessanger', 'PriceZombie',
            '500pxBot', 'TrollaBot', 'RemindMeBot', 'Mentioned_Videos']

subgroup = re.search(".*?\/(.*)_", sys.argv[1])
sub = subgroup.group(1)
print sub

filename = "/mas/u/jnmatias/projects/arrow_reddit_survival/subreddits/"+sub+".json"
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


fd = open("/mas/u/jnmatias/projects/arrow_reddit_survival/subreddit_posts/"+sub+"_posts.json", "r")
all_posts = {}
for line in fd:
    post = json.loads(line)
    all_posts[post['id']]=post
fd.close()


    ### GENERATE DATAFRAME FROM POST JSON

post_rows = []

def defaultzero():
    return 0
prev_user_posts = defaultdict(defaultzero)

for post in all_posts.values():

    post_row = {"charlength":len(post['selftext'])}
    if "author_karma" in post.keys():
        post["author_comment_karma"]=post['author_karma']
    for key in ["score","num_comments","author_id","author_link_karma",
                "author_name","author_created",
                "author_comment_karma","downs","ups","author_flair_text",
               "domain","removal_reason", "approved_by", "subreddit_id", "id",
               "created_utc"]:
        post_row[key]=post[key]
    if string.find(post_row['domain'],"self.")>-1:
        post_row['post_type']="self"
    else:
        post_row['post_type']="link"

    ## LOOK AT THINGS ABOUT COMMENTS
    commenters = set()
    replies = set()
    controversiality = 0
    ups = 0
    for comment in posts["t3_"+post['id']]:
        commenters.add(comment['author'])
        replies.add(comment['parent_id'])
        controversiality += comment['controversiality']
        ups += comment['ups']
    post_row['unique_commenters']=len(commenters)
    post_row['reply_count']=len(replies)

    # CHECK FOR IMAGES
    #if(post['selftext_html']):
    #    post_row['image']=string.find(post['selftext_html'],"gif")>-1
    #else:
    #    post_row['image']=False

    try:
        post_row['mean_comment_controversiality']=float(controversiality)/float(post_row['num_comments'])
    except:
        post_row['mean_comment_controversiality']=0.
    try:
        post_row['mean_comment_ups']=float(ups)/float(post_row['num_comments'])
    except:
        post_row['mean_comment_ups']=0.
    post_row['prev_user_posts']=prev_user_posts[post['author_id']]
    prev_user_posts[post['author_id']]+=1

    ### NOW ADD PREVIOUS COMMENTS FOR THIS AUTHOR
    post_time = int(post_row['created_utc'])
    previous_comments = 0
    for comment in user_comments[post_row['author_name']]:
        if int(comment['created_utc'])>post_time:
            break
        previous_comments +=1
    post_row['previous_comments']=previous_comments

    post_rows.append(post_row)


## GENERATE DATAFRAME FROM POST_ROWS
pdf = pd.DataFrame(post_rows)

print pdf.columns

for key in ['num_comments', 'ups','score','charlength', "unique_commenters", 
            "reply_count", "prev_user_posts", "author_link_karma",
           "previous_comments"]:
    pdf["log_"+key]=pdf[key].map(math.log1p) 
    
pdf.to_csv("/mas/u/jnmatias/projects/arrow_reddit_survival/subreddit_post_csvs/"+sub+"_post_rows.csv", encoding='utf-8')
