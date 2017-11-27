"""dicussion thread"""
import logging

import praw

from slackbot.python_logging.slack_logger import make_slack_logger

class DiscussionThread(object):
    """handles discussion thread"""
    def __init__(self, reddit: praw.Reddit, subreddit: str, webhook_url: str,
                 new_duration: int = 24) -> None:
        self.reddit: praw.Reddit = reddit
        self.subreddit: praw.models.Subreddit = self.reddit.subreddit(subreddit)
        self.submission: praw.reddit.models.Submission = self.latest()
        self.duration: int = new_duration
        self.logger: logging.Logger = make_slack_logger(webhook_url, "discussion-thread")

    def latest(self) -> praw.models.Submission:
        """return latest discussion thread"""
        for submission in self.subreddit.search("Discussion Thread", sort="new"):
            if submission.author == self.reddit.user.me():
                return submission

    def check(self) -> bool:
        """posts or updates discussion thread if necessary"""
        if self.needs_new():
            self.post()
            return True

        if self.updated_text() or self.updated_sticky():
            self.update()
            return True

        return False

    def get_body(self) -> str:
        """gets body from wiki page"""
        return self.subreddit.wiki["dt/config"].content_md

    def post(self) -> bool:
        """posts the discussion thread"""
        old_moderation: praw.models.reddit.submission.SubmissionModeration = self.submission.mod
        old_moderation.sticky(state=False)

        body: str = self.get_body()
        self.submission: praw.models.Submission = self.subreddit.submit(
            "Discussion Thread", selftext=body, url=None, resubmit=True, send_replies=False)
        self.logger.info("New discussion thread posted at %s", self.submission.shortlink)

        new_moderation: praw.models.reddit.submission.SubmissionModeration = self.submission.mod
        new_moderation.sticky(state=True, bottom=False)
        new_moderation.distinguish()
        new_moderation.suggested_sort(sort='new')

        return True

    def needs_new(self) -> bool:
        """checks if new discussion thread is needed"""
        import datetime
        time: datetime.timedelta = (datetime.datetime.utcnow() -
                                    datetime.datetime.utcfromtimestamp(self.submission.created_utc))
        hours: int = int(time.total_seconds() / (60 * 60))

        return hours > self.duration

    def updated_text(self) -> bool:
        """"checks if DT text has been updated"""
        current_body: str = self.submission.selftext
        wiki_body: str = self.get_body()
        return not(current_body == wiki_body)

    def updated_sticky(self) -> bool:
        """checks if sticky has been updated"""
        #todo
        pass

    def update(self) -> bool:
        """updates text of dt"""
        self.logger.info("Updating body of Discussion Thread")
        self.submission.edit(self.get_body())
        return True
