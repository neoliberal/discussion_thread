"""dicussion thread"""
from configparser import ConfigParser, NoSectionError
from datetime import datetime
import json
import logging
import pytz
import requests
import time
from typing import List, Optional, Dict, Tuple

import praw
from schedule import Scheduler
from tabulate import tabulate
from slack_python_logging import slack_logger

class DiscussionThread(object):
    """handles discussion thread"""
    def __init__(self, reddit: praw.Reddit, subreddit: str) -> None:
        def get_config() -> ConfigParser:
            """grabs config"""
            parser: ConfigParser = ConfigParser(allow_no_value=True, delimiters=('='))
            self.logger.debug("Grabbing config")
            while True:
                try:
                    config_string = self.subreddit.wiki["dt/config"].content_md
                    break
                except:
                    self.logger.error("Unable to retrieve config, wait 1 minute & retry")
                    from time import sleep
                    sleep(60)
            if config_string:
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
            times: List[str] = []

            try:
                times = self.config.options("times")
            except NoSectionError:
                self.logger.warning("No times specified in the config, setting to 1:00")
                times = ["1:00"]

            try:
                days: List[str] = self.config.options("days")
            except NoSectionError:
                self.logger.warning("No days are specified in the config, setting to all days")
                for time in times:
                    try:
                        scheduler.every().day.at(time).do(self.post)
                    except ValueError:
                        self.logger.debug("\"%s\" is not a valid time, skipping")
            else:
                for day in days:
                    self.logger.debug("Adding day \"%s\" to scheduler", day)
                    for time in times:
                        try:
                            getattr(scheduler.every(), day).at(time).do(self.post)
                        except AttributeError:
                            self.logger.error("\"%s\" is not an valid day, skipping", day)
                        except ValueError:
                            self.logger.warning("\"%s\" is not a valid time, skipping", time)

            self.logger.debug("Scheduler made")
            return scheduler

        self.logger: logging.Logger = slack_logger.initialize("discussion_thread")
        self.reddit: praw.Reddit = reddit
        self.subreddit: praw.models.Subreddit = self.reddit.subreddit(subreddit)

        self.config: ConfigParser = get_config()
        self.submission: Optional[praw.reddit.models.Submission] = latest()
        self.schedule: Scheduler = make_scheduler()
        self.logger.info("discussion-thread intialized successfully")
        return

    def check(self) -> bool:
        """posts or updates discussion thread if necessary"""
        import prawcore
        from time import sleep

        try:
            self.schedule.run_pending()

            if self.updated_text():
                self.update_body()
                return True

            if self.updated_sticky():
                self.update_sticky()
                return True
        except prawcore.exceptions.ServerError:
            self.logger.error("Reddit server error: Sleeping for 1 minute.")
            sleep(60)
        except prawcore.exceptions.ResponseException:
            self.logger.error("Reddit response error: Sleeping for 1 minute.")
            sleep(60)
        except prawcore.exceptions.RequestException:
            self.logger.error("Reddit request error: Sleeping for 1 minute.")
            sleep(60)
        except requests.exceptions.HTTPError:
            self.logger.error("Bad HTTP status fetching events: Sleeping for 1 minute.")
            sleep(60)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            self.logger.error("Error connecting to events page: Sleeping for 1 minute.")
            sleep(60)

        # self.submission.comments.replace_more(limit=0)

        return False

    def get_body(self) -> str:
        """gets body from wiki page"""
        dt_body = self.subreddit.wiki["dt/config/body"].content_md
        try:
            events = self.get_events()
        except Exception:
            # Too many ways things can go wrong here, so let's just fail gracefully
            logging.warning("unable to fetch events!")
            events = ""
        return(dt_body + events)

    def get_events(self) -> str:
        """Get the upcoming events from the Neoliberal Project website"""
        nl_project_events_url = "https://neoliberalproject.org/upcoming-events?format=json"
        events_page = requests.get(nl_project_events_url, timeout=10)
        events_page.raise_for_status() # Raise an error if we're rate limited
        upcoming_events = events_page.json()['upcoming']
        upcoming_events.sort(key = lambda event: event['startDate'])

        # Build a markdown list of events
        output = ["", "", "## Upcoming Events", ""]
        for event in upcoming_events:
            current_epoch = time.time()
            event_epoch = event['startDate'] / 1000 # convert ms to s
            if event_epoch > current_epoch + (14*24*60*60):
                # Skip any events further than 14 days out
                continue
            # Dates will be given in New York time. If we ever have events in
            # Australia, this will be a problem.
            eastern_time = pytz.timezone('America/New_York')
            event_date = datetime.fromtimestamp(event_epoch, eastern_time)
            date_string = event_date.strftime('%b %d')
            event_url = f'https://neoliberalproject.org{event["fullUrl"]}'
            output.append(f'* {date_string}: [{event["title"]}]({event_url})')

        if len(output) == 4:
            # Don't bother posting the Upcoming events header if there aren't any
            return("")

        return("\n".join(output))

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
        self.logger.info(
            "<https://reddit.com%s|New discussion thread posted>",
            new_thread.permalink
        )

        old_thread: Optional[praw.Models.Submission] = self.submission
        if old_thread is not None:
            self.logger.debug("Unsticking old thread")
            old_moderation: praw.models.reddit.submission.SubmissionModeration = old_thread.mod
            old_moderation.sticky(state=False)
            self.logger.debug("Unstickied old thread")

            self.logger.debug("Posting new discussion thread comment in old thread")
            visit_comment: praw.models.Comment = old_thread.reply(
                f"Please visit the [next discussion thread]({new_thread.permalink})."
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

        # self.logger.debug("Posting user count table in new thread")
        # new_thread.reply(
        #     f"""
        #     Top 100 Users on the [Last Discussion Thread]({old_thread.permalink}):

        #     {self.user_count(old_thread)}
        #     """
        # )
        # self.logger.debug("Posted user count table in new thread")

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

    def user_count(self, submission: praw.models.Submission) -> str:
        """
        returns formatted table of Name, Postcount, Karma, and Karma/Post

        credit to /u/zqvt
        """
        self.logger.debug("Constructing table of user count table")

        self.logger.debug("Replacing remaining MoreComments")
        submission.comments.replace_more(limit=None)
        self.logger.debug("Replaced remaining MoreComments")

        self.logger.debug("Making dictionary")
        comment_count: Dict[str, Tuple[int, int]] = dict()
        for comment in submission.comments.list():
            author = comment.author
            score = comment.score
            if author not in comment_count:
                comment_count[author] = (1, score)
            else:
                old_count, old_score = comment_count[author]
                comment_count[author] = (old_count + 1, old_score + score)
        self.logger.debug("Made dictionary")

        self.logger.debug("Sorting users")
        sorted_users: List[Tuple[str, Tuple[int, int]]] = sorted(
            comment_count.items(),
            key=(lambda item: item[1][0]),
            reverse=True
        )[:100]
        self.logger.debug("Sorted users")

        self.logger.debug("Constructing table")
        table: List[Tuple[str, int, int, float]] = []
        for user in sorted_users:
            table.append((
                f"/u/{user[0]}",
                user[1][0],
                user[1][1],
                float(user[1][1] / user[1][0])
            ))
        self.logger.debug("Constructed table")

        self.logger.debug("Constructed table of user count table")
        return tabulate(
            table,
            headers=["User", "Count", "Karma", "Karma / Post"],
            tablefmt="pipe",
            floatfmt="2.2f",
        )
