"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import send_from_directory, redirect, url_for, abort
import arrow
from insta485.views.pass_help import abort_unauthenicated_user
import insta485


@insta485.app.template_filter('humanize')
def humanize_filter(time):
    """Humanize time."""
    return arrow.get(time).humanize()


@insta485.app.route('/uploads/<path:filename>')
def download_file(filename):
    """Send Images correctly."""
    logname, connection = abort_unauthenicated_user()
    if logname is None:
        abort(403)
    file_fetch = connection.execute(
            """
            SELECT Count(*) from posts
            WHERE posts.filename = ?
            """,
            (filename,)
        ).fetchone()
    if not file_fetch:
        abort(404)
    return send_from_directory('../var/uploads', filename)


@insta485.app.route('/', methods=["GET"])
def show_index():
    """Index page."""
    if 'username' not in flask.session:
        return redirect(url_for('show_login'))
    logname = flask.session['username']
    # Query database
    connection = insta485.model.get_db()
    user_fetch = connection.execute(
        "SELECT DISTINCT u.username, u.fullname, "
        "u.filename AS user_profile_pic_url, "
        "p.postid, p.filename AS post_url, p.created, p.owner, "
        "(SELECT COUNT(*) from likes where likes.postid = p.postid) "
        "AS like_count, "
        "CASE WHEN EXISTS "
        "(SELECT 1 FROM likes WHERE likes.postid = p.postid "
        "AND likes.owner = ?) "
        "THEN 1 ELSE 0 END "
        "AS has_liked "
        "FROM users u "
        "INNER JOIN posts p "
        "ON u.username = p.owner "
        "LEFT JOIN following f ON u.username = f.username2 "
        "WHERE f.username1 = ? OR u.username = ? "
        "ORDER by p.postid DESC",
        (logname, logname, logname)
    )
    users = user_fetch.fetchall()
    print(users)
    comment_fetch = connection.execute(
        "SELECT commentid, text, owner, postid, created "
        "FROM comments"
    )
    comment_fetch = comment_fetch.fetchall()

    # Add database info to context
    context = {"users": users, "comments": comment_fetch, "logname": logname}
    return flask.render_template("index.html", **context)
