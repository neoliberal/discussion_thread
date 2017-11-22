"""turns discussion thread into daemon"""
import daemon
import praw

from discussion_thread import DiscussionThread

def main() -> None:
    """main function"""
    reddit: praw.Reddit = praw.Reddit()
    thread: DiscussionThread = DiscussionThread(reddit, "neoliberal")

    with daemon.DaemonContext(
        working_directory="/var/lib/discussion_thread",
        umask=0o002,
        pidfile=daemon.pidfile.TimeoutPIDLockFile("/var/run/discussion_thread.pid")
        ):
        thread.check_post()
        from time import sleep
        sleep(30)


if __name__ == "main":
    main()
