"""dicussion thread"""
from configparser import ConfigParser
import logging
from typing import List, Optional

import praw
from schedule import Scheduler

from slackbot.python_logging.slack_logger import make_slack_logger

class DiscussionThread(object):
    """handles discussion thread"""
    def __init__(self, reddit: praw.Reddit, subreddit: str) -> None:
        def get_config() -> ConfigParser:
            """grabs config"""
            parser: ConfigParser = ConfigParser(allow_no_value=True)
            self.logger.debug("Grabbing config")
            config_string = self.subreddit.wiki["dt/config"].content_md
            if not config_string:
                self.logger.debug("Config grabbed")
                parser.read_string(config_string)
            else:
                self.logger.error("No config found")
            return parser

        def latest() -> Optional[praw.models.Submission]:
            """return latest discussion thread"""
            self.logger.debug("Fetching latest discussion thread")
            for submission in self.subreddit.search(
                    self.config.get("config", "title", fallback="Discussion Thread"),
                    sort="new"
                ):
                if submission.author == self.reddit.user.me():
                    self.logger.debug("Latest discussion thread returned")
                    return submission
            self.logger.warning("Could not find latest discussion thread. Returning None")
            return None

        def make_scheduler() -> Scheduler:
            """makes scheduler object"""
            self.logger.debug("Making scheduler")
            scheduler: Scheduler = Scheduler()
            days: List[str] = self.config.options("days")
            time: str = self.config.get("config", "time", fallback="1:00")
            self.logger.debug("Setting discussion thread time to \"%s\"", time)

            if days:
                for day in days:
                    self.logger.debug("Adding day \"%s\" to scheduler", day)
                    getattr(scheduler.every(), day).at(time).do(self.post)
            else:
                self.logger.warning("No days are specified in the config, setting to all days")
                scheduler.every().day.at(time).do(self.post)

            self.logger.debug("Scheduler made")
            return scheduler

        self.logger: logging.Logger = make_slack_logger("discussion-thread")
        self.reddit: praw.Reddit = reddit
        self.subreddit: praw.models.Subreddit = self.reddit.subreddit(subreddit)

        self.config: ConfigParser = get_config()
        self.submission: Optional[praw.reddit.models.Submission] = latest()
        self.schedule: Scheduler = make_scheduler()
        self.logger.info("discussion-thread intialized successfully")
        return

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
        self.logger.debug("Posting new discussion thread")
        new_thread: praw.Models.Submission = self.subreddit.submit(
            self.config.get("config", "title", fallback="Discussion Thread"),
            selftext=self.get_body(),
            url=None,
            resubmit=True,
            send_replies=False
        )
        self.logger.info("New discussion thread posted at %s", new_thread.shortlink)

        old_thread: Optional[praw.Models.Submission] = self.submission
        if old_thread is not None:
            self.logger.debug("Unstickying old thread")
            old_moderation: praw.models.reddit.submission.SubmissionModeration = self.submission.mod
            old_moderation.sticky(state=False)
            self.logger.debug("Unstickyied old thread")
            self.logger.debug("Posting new discussion thread comment in old thread")
            visit_comment: praw.models.Comment = old_thread.reply(
                "Please visit the [new discussion thread]({}).".format(new_thread.shortlink)
            )
            visit_comment.mod.distinguish(sticky=True)
            self.logger.debug("Posted new discussion thread comment in old thread")


        new_moderation: praw.models.reddit.submission.SubmissionModeration = new_thread.mod
        self.logger.debug("Stickying new thread")
        new_moderation.sticky(state=True, bottom=False)
        new_moderation.distinguish()
        self.logger.debug("Stickied new thread")
        self.logger.debug("Sorting new thread")
        new_moderation.suggested_sort(sort="new")
        self.logger.debug("Sorted new thread")
        self.logger.debug("Setting discussion thread flair")
        new_moderation.flair(
            css_class=self.config.get("flair", "id", fallback=''),
            text=self.config.get("flair", "text", fallback=''),
        )
        self.logger.debug("Set discussion thread flair")

        self.submission = new_thread

        return True

    def updated_text(self) -> bool:
        """"checks if DT text has been updated"""
        current_body: str = self.submission.selftext
        wiki_body: str = self.get_body()
        return not current_body == wiki_body

    def update_body(self) -> bool:
        """updates text of dt"""
        self.logger.debug("Updating body of Discussion Thread")
        self.submission.edit(self.get_body())
        self.logger.info("Updated body of discussion thread")
        return True

    def updated_sticky(self) -> bool:
        """checks if sticky has been updated"""
        # todo
        pass

    def update_sticky(self) -> bool:
        """updates sticky comment"""
        # todo
        pass
