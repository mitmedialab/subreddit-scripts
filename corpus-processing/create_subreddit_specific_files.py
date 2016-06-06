import simplejson as json
from collections import defaultdict
import math
import heapq
import sys
import csv

from pybloom import BloomFilter

#TOP SUBS BY COMMENTS
top_subs_by_comments = []
with open('/mas/u/jnmatias/projects/reddit/reddit-scraper/data/top_75k_subreddits_by_comments.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        top_subs_by_comments.append(row)

# CREATE BLOOMFILTER OF SUBS WITH MORE THAN 30 COMMENTS IN JUNE 2015
tsbc = [x for x in top_subs_by_comments if int(x['comments'])>=30]
sub_sample = BloomFilter(capacity=len(tsbc), error_rate=0.0001)
[sub_sample.add(x['subname']) for x in tsbc]
print "subreddits >30 comments a month: " + str(len(sub_sample))

# CREATE BLOOMFILTER OF BOTS
bot_names = ['[deleted]', 'AutoModerator', 'autowikibot', 'TweetsInCommentsBot',
             'TweetPoster', 'TotesMessanger', 'PriceZombie',
            '500pxBot', 'TrollaBot', 'RemindMeBot', 'Mentioned_Videos']

bots = BloomFilter(capacity=len(bot_names), error_rate = 0.0001)
[bots.add(x) for x in bot_names]
print "bots: " + str(len(bots))

### CREATE A JSON FILE FOR EACH SUBREDDIT
subreddit_comments = defaultdict(list)
counter = 0 
for filename in ['/mas/u/jnmatias/smbshare/reddit-archive/comments/RC_2015-07',
                 '/mas/u/jnmatias/smbshare/reddit-archive/comments/RC_2015-08',
                 '/mas/u/jnmatias/smbshare/reddit-archive/comments/RC_2015-09']:
    for line in open(filename, 'r'):
        counter +=1
        if counter % 100000 == 0:
            sys.stdout.write(".")#str(counter) + ", ")
            sys.stdout.flush()
        comment = json.loads(line)
        author = comment['author']
        subreddit = comment['subreddit']
        subreddit_id = comment['subreddit_id']
        if author in bots:
            continue
        if subreddit in sub_sample:
            subreddit_comments[subreddit_id].append(line)
            if len(subreddit_comments[subreddit_id])>=100000:
                fd = open("./subreddits/" + subreddit_id +".json", "a")
                fd.write("".join(subreddit_comments[subreddit_id]))
                fd.close()
                sys.stdout.write("x")
                subreddit_comments[subreddit_id] = []

for subreddit_id, sub in subreddit_comments.iteritems():
    fd = open("/mas/u/jnmatias/projects/arrow_reddit_survival/subreddits/" + subreddit_id +".json", "a") 
    fd.write("".join(sub))
    fd.close()
    print "writing " + subreddit_id
