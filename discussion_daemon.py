"""turns discussion thread into daemon"""
import logging
import sys

import daemon
from daemon import pidfile

from discussion_thread import DiscussionThread

def main() -> None:
    """main function"""
    import os
    import praw
    reddit: praw.Reddit = praw.Reddit(
        client_id=os.environ["client_id"],
        client_secret=os.environ["client_secret"],
        refresh_token=os.environ["refresh_token"],
        user_agent="linux:neoliberal_discussion_thread:v2.0 (by /u/CactusChocolate)"
    )

    thread: DiscussionThread = DiscussionThread(
        reddit,
        "neoliberal",
        os.environ["slack_webhook_url"]
    )
    file_handler: logging.Handler = logging.FileHandler("/var/log/flairbot.log")
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_handler.setFormatter(logging.Formatter(format_string))
    file_handler.setLevel(logging.DEBUG)
    thread.logger.addHandler(file_handler)

    def log_unhandled(*exc_info):
        """sys.excepthook override"""
        import traceback
        # pylint: disable=E1120
        text: str = "".join(traceback.format_exception(*exc_info))
        thread.logger.critical(text)

    sys.excepthook = log_unhandled

    with daemon.DaemonContext(
        working_directory="/var/lib/discussion_thread",
        umask=0o002,
        pidfile=pidfile.TimeoutPIDLockFile(
            "/var/run/discussion_thread.pid")
    ) as context:
        while context.is_open:
            thread.check()
            from time import sleep
            sleep(30)


if __name__ == "__main__":
    main()
