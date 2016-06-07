import simplejson as json
from collections import defaultdict
import math
import heapq
import sys
import csv
import glob

from pybloom import BloomFilter


reddit_archive_dir = sys.argv[1]
sub_archive_dir = sys.argv[2]
print 
print "outputting to " + sub_archive_dir

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
for filename in sorted(glob.glob(reddit_archive_dir + "*")):
    print filename
    for line in open(filename, 'r'):
        counter +=1
        if counter % 100000 == 0:
            sys.stdout.write(".")#str(counter) + ", ")
            sys.stdout.flush()
        comment = json.loads(line)
        #author = comment['author']
        subreddit = comment['subreddit']
        subreddit_id = comment['subreddit_id']
        #if author in bots:
        #    continue
        subreddit_comments[subreddit_id].append(line)
        # if there are more than 50000 comments for a subreddit
        # in the dict, then write them out to file
        if(len(subreddit_comments[subreddit_id])>25000):
          fd = open(sub_archive_dir + subreddit_id +".json", "a") 
          fd.write("".join(subreddit_comments[subreddit_id]))
          fd.close()
          sys.stdout.write("W")
          subreddit_comments[subreddit_id] = []
 

print "Found a total of %(count)s subreddits" % len(subreddit_comments.keys())

for subreddit_id, sub in subreddit_comments.iteritems():
    fd = open(sub_archive_dir + subreddit_id +".json", "a") 
    fd.write("".join(sub))
    fd.close()
    print "writing " + subreddit_id
