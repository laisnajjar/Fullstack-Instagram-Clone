"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import redirect, url_for
from flask import abort
from insta485.views.pass_help import abort_unauthenicated_user
import insta485


@insta485.app.route("/users/<username>/", methods=["GET"])
def show_user(username):
    """User profile page."""
    logname, connection = abort_unauthenicated_user()
    if logname is None:
        return redirect(url_for('show_login'))
    user_exists_fetch = connection.execute(
        "SELECT COUNT(*) FROM users WHERE username = ?",
        (username,)
    )
    user_exists = user_exists_fetch.fetchone()
    if not user_exists:
        abort(404)
    # fetch user info, if logname follows user, post count
    user_fetch = connection.execute(
        """
        SELECT DISTINCT
            u.username, u.fullname, u.filename as user_profile_pic_url,
            COALESCE((SELECT COUNT(*) FROM posts
            WHERE posts.owner = u.username),0)
            AS post_count,
            CASE WHEN EXISTS
            (SELECT 1 FROM following WHERE following.username2 = u.username
            AND following.username1 = ?)
            THEN 1 ELSE 0 END
            AS logname_follows_username
        FROM users u
        WHERE u.username = ?
        """,
        (logname, username)
    )
    user = user_fetch.fetchone()
    # fetch post info
    posts_fetch = connection.execute(
        """
        SELECT DISTINCT
            p.postid, p.filename AS post_url, p.owner
        FROM posts p
        WHERE p.owner = ?
        """,
        (username,)
    )
    posts = posts_fetch.fetchall()
    # fetch follower and following count for the user
    follow_fetch = connection.execute(
        """
        SELECT DISTINCT u.username,
        COALESCE((SELECT COUNT(*) FROM following
            WHERE following.username1 = u.username),0)
            AS following_count,
        COALESCE((SELECT COUNT(*) FROM following
            WHERE following.username2 = u.username),0)
            AS follower_count
        FROM users u
        WHERE u.username = ?
        """,
        (username,)
    )
    follow = follow_fetch.fetchone()

    # Add database info to context
    context = {"user": user, "posts": posts,
               "follow": follow, "logname": logname, "username": username}
    return flask.render_template("user.html", **context)
