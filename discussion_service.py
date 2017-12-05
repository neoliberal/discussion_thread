"""turns discussion thread into service"""
import os

import praw

from discussion_thread import DiscussionThread

def main() -> None:
    """main function"""
    reddit: praw.Reddit = praw.Reddit(
        client_id=os.environ["client_id"],
        client_secret=os.environ["client_secret"],
        refresh_token=os.environ["refresh_token"],
        user_agent="linux:neoliberal_discussion_thread:v2.0 (by /u/CactusChocolate)"
    )

    thread: DiscussionThread = DiscussionThread(
        reddit,
        "neoliberal"
    )

    while True:
        thread.check()
        from time import sleep
        sleep(5)

if __name__ == "__main__":
    main()
