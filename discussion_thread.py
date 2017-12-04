"""dicussion thread"""
from configparser import ConfigParser
import logging
from typing import List

import praw
from schedule import Scheduler

from slackbot.python_logging.slack_logger import make_slack_logger

class DiscussionThread(object):
    """handles discussion thread"""
    def __init__(self, reddit: praw.Reddit, subreddit: str) -> None:
        self.logger: logging.Logger = make_slack_logger("discussion-thread")
        self.reddit: praw.Reddit = reddit
        self.subreddit: praw.models.Subreddit = self.reddit.subreddit(subreddit)

        self.submission: praw.reddit.models.Submission = self.latest()
        self.config: ConfigParser = self.get_config()
        self.schedule: Scheduler = self.make_scheduler()
        self.logger.info("discussion-thread intialized successfully")
        return

    def latest(self) -> praw.models.Submission:
        """return latest discussion thread"""
        self.logger.debug("Fetching latest discussion thread")
        for submission in self.subreddit.search("Discussion Thread", sort="new"):
            if submission.author == self.reddit.user.me():
                self.logger.debug("Latest discussion thread returned")
                return submission

    def get_config(self) -> ConfigParser:
        """grabs config"""
        self.logger.debug("Grabbing config")
        parser: ConfigParser = ConfigParser(allow_no_value=True)
        parser.read_string(self.subreddit.wiki["dt/config"].content_md)
        self.logger.debug("Config grabbed")
        return parser

    def make_scheduler(self) -> Scheduler:
        """makes scheduler object"""
        self.logger.debug("Making scheduler")
        scheduler: Scheduler = Scheduler()
        days: List[str] = self.config.options("days")
        time: str = self.config["config"]["time"]
        self.logger.debug("Setting discussion thread time to \"%s\"", time)

        for day in days:
            self.logger.debug("Adding day \"%s\" to scheduler", day)
            getattr(scheduler.every(), day).at(time).do(self.post)

        self.logger.debug("Scheduler made")
        return scheduler

    def check(self) -> bool:
        """posts or updates discussion thread if necessary"""
        self.schedule.run_pending()

        if self.updated_text():
            self.update_body()
            return True

        if self.updated_sticky():
            self.update_sticky()
            return True

        return False

    def get_body(self) -> str:
        """gets body from wiki page"""
        return self.subreddit.wiki["dt/config/body"].content_md

    def post(self) -> bool:
        """posts the discussion thread"""
        old_moderation: praw.models.reddit.submission.SubmissionModeration = self.submission.mod
        old_moderation.sticky(state=False)

        self.submission: praw.models.Submission = self.subreddit.submit(
            self.config.get("config", "title", fallback="Discussion Thread"),
            selftext=self.get_body(),
            url=None,
            flair_id=self.config.get("flair", "id", fallback=None),
            flair_text=self.config.get("flair", "text", fallback=None),
            resubmit=True,
            send_replies=False
        )
        self.logger.info("New discussion thread posted at %s", self.submission.shortlink)

        new_moderation: praw.models.reddit.submission.SubmissionModeration = self.submission.mod
        new_moderation.sticky(state=True, bottom=False)
        new_moderation.distinguish()
        new_moderation.suggested_sort(sort="new")

        return True

    def updated_text(self) -> bool:
        """"checks if DT text has been updated"""
        current_body: str = self.submission.selftext
        wiki_body: str = self.get_body()
        return not current_body == wiki_body

    def update_body(self) -> bool:
        """updates text of dt"""
        self.logger.info("Updating body of Discussion Thread")
        self.submission.edit(self.get_body())
        return True

    def updated_sticky(self) -> bool:
        """checks if sticky has been updated"""
        # todo
        pass

    def update_sticky(self) -> bool:
        """updates sticky comment"""
        # todo
        pass
