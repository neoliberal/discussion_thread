"""turns discussion thread into daemon"""
import daemon
import praw

from discussion_thread import DiscussionThread

def main() -> None:
    """main function"""
    reddit: praw.Reddit = praw.Reddit()
    thread: DiscussionThread = DiscussionThread(reddit, "neoliberal")

    with daemon.DaemonContext(
        working_directory="/var/lib/discussion-thread",
        umask=0o002,
        pidfile=daemon.pidfile.TimeoutPIDLockFile("/var/run/discussion-thread.pid")
        ):
        thread.update()
        from time import sleep
        sleep(5)


if __name__ == "main":
    main()
