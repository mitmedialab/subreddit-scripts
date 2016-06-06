import simplejson as json
from collections import defaultdict
from dateutil import parser
import datetime
#import matplotlib.pyplot as plt   # Matplotlib for plotting
import math
import heapq
import sys
import csv
import numpy as np
import pandas as pd
import numpy as np

from collections import Counter
from collections import defaultdict

import statsmodels.api as sm
import statsmodels.formula.api as smf

from pybloom import BloomFilter

###### LOAD DATA

filename = sys.argv[1] #"/mas/u/jnmatias/projects/arrow_reddit_survival/subreddits/t5_2s3x4.json"

bots = ['[deleted]', 'AutoModerator', 'autowikibot', 'TweetsInCommentsBot',
        'TweetPoster', 'TotesMessanger', 'PriceZombie',
        '500pxBot', 'TrollaBot', 'RemindMeBot', 'Mentioned_Videos']

linecounter = 0
user_comments = defaultdict(list)

for line in open(filename, 'r'):
    linecounter +=1
    if linecounter % 100000 == 0:
        sys.stdout.write(".")#str(counter) + ", ")
        sys.stdout.flush()
    comment = json.loads(line)
    author = comment['author']
    if author in bots:
        continue
    user_comments[author].append(comment)
print "Total Users: " + str(len(user_comments.values()))
print "Total Comments: " + str(linecounter)

all_users = {}
all_weeks = []

def user_dict():
    return {"comments":0,"subcount":0,
            "weeks":[], "week_count":0,"censored":False}

user_weeks = defaultdict(user_dict)

counter = 0 
for comments in user_comments.values():
    counter +=1
    if counter % 1000 == 0:
        sys.stdout.write(".")#str(counter) + ", ")
        sys.stdout.flush()
    author = comments[0]['author']
    all_users[author] = comments
    
    earliest_week = int(datetime.datetime.fromtimestamp(int(comments[0]['created_utc'])).strftime("%Y%U"))
    last_week = int(datetime.datetime.fromtimestamp(int(comments[-1]['created_utc'])).strftime("%Y%U"))

    # CENSOR IF FIRST WEEK IS WITHIN THE FIRST TWO WEEKS OF THE PERIOD
    # OR IF THE LAST OBSERVATION IS WITHIN THE LAST WEEK
    censored = False
    if earliest_week <= 201526 +1:
        censored =True
    elif last_week >= 201539:
        censored=True
    
    user_weeks[author]['censored'] = censored
    
    week_comments = None
    week_comments = defaultdict(list)
    for comment in comments:
        week = int(datetime.datetime.fromtimestamp(int(comment['created_utc'])).strftime("%Y%U"))
        week_comments[week].append(comment)
    
    user_subs = set()
    # FOR NOW, WE'RE JUST GOING TO LOOK AT INCIDENTS IN THAT WEEK
    # IT MAY BE NECESSARY TO MAKE THESE CUMULATIVE MEASURES 
    week_from_zero = 0
    
    cum_comments = 0
    cum_deleted = 0
    cum_sum_ups = 0
    cum_sum_score = 0
    cum_sum_contro = 0
    cum_subreddits = 0
    cum_comment_length = 0
    
    for week in range(earliest_week,last_week+1):
        wt = {"comments":len(week_comments[week]), "subreddits":0, 
              "contro_sum":0, "ups_sum":0, "deleted":0,"score_sum":0,
             "week_from_zero":week_from_zero, "week":week, "author":author,
             "censored":censored, "DROPOUT":0, "comment_length":0}
        
        for comment in week_comments[week]:
            user_subs.add(comment['subreddit_id'])
            if(comment['body']=="[deleted]"):
                wt['deleted']+=1
                sys.stdout.write(str(wt['deleted']))
    
            wt['comment_length'] += len(comment['body'])
            wt['ups_sum']+= comment['ups']
            wt['score_sum']+= comment['score']
            wt['contro_sum']+= comment['controversiality']
 
        wt['mean_comment_length']=float(wt['comment_length'])/(float(wt['comments'])+1.)

        cum_sum_contro+= wt['contro_sum']
        wt['contro_cum'] = cum_sum_contro
        
        cum_comment_length += wt['comment_length']
        wt['comment_length_cum'] = cum_comment_length
        
        cum_deleted += wt['deleted']
        wt['deleted_cum'] = cum_deleted
        
        cum_sum_score += wt['score_sum']
        wt['score_cum'] = cum_sum_score
        
        cum_sum_ups += wt['ups_sum']
        wt['ups_cum'] = cum_sum_ups
        
        cum_comments += len(week_comments[week])
        wt['comments_cum'] = cum_comments
        
        week_from_zero +=1
        user_weeks[author]['weeks'].append(wt)
        all_weeks.append(wt)

    all_weeks[-1]['DROPOUT']=1
    user_weeks[author]['weeks'][-1]['DROPOUT']=1
    user_weeks[author]['comments']=len(comments)
    user_weeks[author]['week_count'] = len(user_weeks[author]['weeks'])
    user_weeks[author]['subcount'] = len(user_subs)

    
ppdf_nc = pd.DataFrame(all_weeks)
print "Week Count: " + str(len(all_weeks))
ppdf = ppdf_nc[ppdf_nc.censored!=True]
ppdf['log_comments_cum']=ppdf.comments_cum.map(math.log1p)
ppdf['log_deleted_cum'] = ppdf.deleted_cum.map(math.log1p)
ppdf['log_contro_sum'] = ppdf.contro_sum.map(math.log1p)
ppdf['log_contro_cum'] = ppdf.contro_cum.map(math.log1p)

ppdf['log_mean_comment_length'] = ppdf.mean_comment_length.map(math.log1p)
ppdf['log_comment_length_cum'] = ppdf.comment_length_cum.map(math.log1p)


result = smf.glm(formula = "DROPOUT ~ week_from_zero + I(week_from_zero)^2 + log_comments_cum + log_comment_length_cum + log_contro_sum", 
                 data=ppdf,
                 family=sm.families.Binomial()).fit()
#print result.summary()

comment = user_comments.values()[0][0]
model_result = {
    "subreddit":comment['subreddit'],
    "subreddit_id":comment['subreddit_id'],
    "total_users":len(user_comments.keys()),
    "total_weeks":len(all_weeks),
    "total_comments": linecounter
}

betas = {}
for k,v in result.params.to_dict().iteritems():
    betas["b_" + k] = v
model_result.update(betas)

pvalues = {}
for k,v in result.pvalues.to_dict().iteritems():
    pvalues['p_' + k] = v
model_result.update(pvalues)

tvalues = {}
for k,v in result.tvalues.to_dict().iteritems():
    tvalues['t_'+k] = v
model_result.update(tvalues)

#model_result['conf_int']=result.conf_int().to_dict()
model_result['aic']=result.aic
model_result['bic']=result.bic
model_result['pearson_chi2']= result.pearson_chi2


#### OUTPUT MODEL RESULT TO FILE
model_keys = ['subreddit_id',
 'p_log_comment_length_cum',
 'total_comments',
 'b_I(week_from_zero) ^ 2',
 'bic',
 'subreddit',
 't_log_comment_length_cum',
 'b_log_contro_sum',
 'b_Intercept',
 't_log_contro_sum',
 'total_users',
 'p_log_contro_sum',
 'pearson_chi2',
 'b_week_from_zero',
 'b_log_comments_cum',
 't_log_comments_cum',
 'p_I(week_from_zero) ^ 2',
 'p_log_comments_cum',
 't_week_from_zero',
 'b_log_comment_length_cum',
 't_Intercept',
 't_I(week_from_zero) ^ 2',
 'p_Intercept',
 'p_week_from_zero',
 'aic',
 'total_weeks']

fd = open(sys.argv[2], "a")
for k in model_keys:
  fd.write(str(model_result[k])+",")
fd.write("\n")
fd.close()
  
