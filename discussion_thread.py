"""dicussion thread"""
import praw

class DiscussionThread(object):
    """handles discussion thread"""
    def __init__(self: DiscussionThread, reddit: praw.Reddit, subreddit: str,
                 new_duration: int = 24, comments_limit: int = 300) -> None:
        self.reddit: praw.Reddit = reddit
        self.subreddit: praw.models.Subreddit = self.reddit.subreddit(subreddit)
        self.duration = new_duration
        self.limit = comments_limit

    def update(self: DiscussionThread) -> bool:
        """updates discussion thread if necessary"""
        submission: praw.reddit.models.Submission = self.latest()
        if self.needs_new(submission):
            self.post(submission)
        return True

    def get_body(self: DiscussionThread) -> str:
        """gets body from wiki page"""
        return self.subreddit.wiki["dt/config"].content_md

    def post(self: DiscussionThread, old: praw.models.Submission) -> bool:
        """posts the discussion thread"""
        old_moderation: praw.models.reddit.submission.SubmissionModeration = old.mod
        old_moderation.sticky(state=False)

        body: str = self.get_body()
        new: praw.models.Submission = self.subreddit.submit(
            "Discussion Thread", selftext=body, url=None, resubmit=True, send_replies=False)
        new_moderation: praw.models.reddit.submission.SubmissionModeration = new.mod
        new_moderation.sticky(state=True, bottom=False)
        new_moderation.distinguish()
        new_moderation.suggested_sort(sort='new')
        return True

    def latest(self: DiscussionThread) -> praw.models.Submission:
        """returns the latest discussion thread"""
        for submission in self.subreddit.search("Discussion Thread", sort="new"):
            if submission.author == self.reddit.user.me():
                return submission

    def needs_new(self: DiscussionThread, submission: praw.models.Submission) -> bool:
        """checks if new discussion thread is needed"""
        import datetime
        time: datetime.timedelta = (datetime.datetime.utcnow() -
                                    datetime.datetime.utcfromtimestamp(submission.created_utc))
        hours: int = int(time.total_seconds() / 3600)

        return submission.num_comments > self.limit or hours > self.duration
