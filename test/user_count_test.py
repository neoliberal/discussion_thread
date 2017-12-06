from typing import Dict, Tuple, List

import praw
from prettytable import PrettyTable


def user_count(submission: praw.models.Submission) -> PrettyTable:
    """
    returns formatted table of Name, Postcount, Karma, and Karma/Post

    credit to /u/zqvt
    """
    print("Constructing table of user count table")
    submission.comments.replace_more(limit=None)
    comment_count: Dict[str, Tuple[int, int]] = dict()

    print("Making dictionary")
    for comment in submission.comments.list():
        print(comment)
        author = comment.author
        score = comment.score
        if author not in comment_count:
            comment_count[author] = (1, score)
        else:
            old_count, old_score = comment_count[author]
            comment_count[author] = (old_count + 1, old_score + score)
    print("Made dictionary")

    print("Sorting users")
    sorted_users: List[Tuple[str, Tuple[int, int]]] = sorted(
        comment_count.items(),
        key=(lambda item: item[1][0]),
        reverse=True
    )
    sorted_users = sorted_users[:100]
    print("Sorted users")

    print("Constructing table")
    table: PrettyTable = PrettyTable(['Name', 'Count', 'Karma', 'Karma / Post'])
    table.junction_char = '|'
    for user in sorted_users:
        karma_post: float = float(user[1][1] / user[1][0])
        table.add_row([
            "/u/{}".format(user[0]),
            user[1][0],
            user[1][1],
            '{0:2.2f}'.format(karma_post)
        ])
    print("Constructed table")

    print("Constructed table of user count table")
    return table
