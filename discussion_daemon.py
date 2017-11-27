"""turns discussion thread into daemon"""
import daemon

from discussion_thread import DiscussionThread

def main() -> None:
    """main function"""
    import os
    import praw
    reddit: praw.Reddit = praw.Reddit(
        client_id=os.environ["client_id"],
        client_secret=os.environ["client_secret"],
        refresh_token=os.environ["refresh_token"],
        user_agent="linux:discussion_thread:v2.0 (by /u/CactusChocolate)"
    )
    thread: DiscussionThread = DiscussionThread(
        reddit,
        "neoliberal",
        os.environ["slack_webhook_url"]
    )

    with daemon.DaemonContext(
        working_directory="/var/lib/discussion_thread",
        umask=0o002,
        pidfile=daemon.pidfile.TimeoutPIDLockFile("/var/run/discussion_thread.pid")
        ):
        thread.check()
        from time import sleep
        sleep(30)


if __name__ == "main":
    main()
