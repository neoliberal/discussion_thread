import praw
import datetime
import time
import sys
import os

def getLatestDThread(NE):
    """
    Returns latest discussion thread object
    """

    d_threads = [x for x in NE.search('Discussion Thread', time_filter='week') if 'Discussion' in x.title]

    dateref = datetime.datetime.now() - datetime.timedelta(weeks = 1)

    for x in d_threads:

        if datetime.datetime.utcfromtimestamp(x.created_utc) > dateref:
            latest = x
            dateref = datetime.datetime.utcfromtimestamp(x.created_utc)

    return latest


def checkDThread(dthread, comment_limit, age_limit):
    """
    Returns true if latest discussion thread is completed and a
    new one is required
    """

    # hours that the discussion thread has been up
    delta = (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(dthread.created_utc))
    delta_hours = delta.total_seconds()/3600

    # number of comments in the discussion thread
    num_comments = dthread.num_comments

    return (num_comments > comment_limit or delta_hours > age_limit)


def postNewDThread(old_dthread, NE):
    old_dthread_moderation = praw.models.reddit.submission.SubmissionModeration(old_dthread)
    old_dthread_moderation.sticky(state=False)
    time.sleep(5)
    post_text = old_dthread.selftext

    new_dthread = NE.submit("Discussion Thread", selftext= post_text, url=None, resubmit=True, send_replies=False)
    new_dthread_moderation = praw.models.reddit.submission.SubmissionModeration(new_dthread)
    time.sleep(5)
    new_dthread_moderation.sticky(state=True, bottom=False)
    new_dthread_moderation.distinguish()
    new_dthread_moderation.suggested_sort(sort='new')


def updateSticky(comment_limit, hours_limit, NE):
    '''
    Updates sticky if necessary
    '''
    print("getting latest thread")
    x = getLatestDThread(NE)
    time.sleep(10)
    print("checking thread")
    if checkDThread(x, comment_limit, hours_limit):
        print("posting thread...")
        postNewDThread(x, NE)
        print("Posted new thread")
    else:
        print("Current thread is sufficient")


## Main

r = praw.Reddit()
NE = r.subreddit("neoliberal")

updateSticky(300, 5, NE)

