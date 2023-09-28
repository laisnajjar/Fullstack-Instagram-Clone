"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import redirect, url_for, request
from flask import abort
from insta485.views.pass_help import abort_unauthenicated_user
from insta485.views.pass_help import fetch_user_data, user_exists_fetch
import insta485


@insta485.app.route("/users/<username>/followers/", methods=["GET"])
def show_followers(username):
    """Show followers."""
    logname, connection = abort_unauthenicated_user()
    if logname is None:
        return redirect(url_for('show_login'))

    user_exists = user_exists_fetch(connection, username)
    if not user_exists:
        abort(404)

    user = fetch_user_data(connection, logname, username)

    # Add database info to context
    context = {"user": user, "logname": logname}
    return flask.render_template("followers.html", **context)


@insta485.app.route("/users/<username>/following/", methods=["GET"])
def show_following(username):
    """Following page."""
    logname, connection = abort_unauthenicated_user()
    if logname is None:
        return redirect(url_for('show_login'))

    user_exists = user_exists_fetch(connection, username)

    if not user_exists:
        abort(404)
    user_fetch = connection.execute(
        """
        SELECT DISTINCT
            u.username, u.filename as user_profile_pic_url,
            CASE WHEN EXISTS
            (SELECT 1 FROM following WHERE following.username2 = u.username
            AND following.username1 = ?)
            THEN 1 ELSE 0 END
            AS logname_follows_username
        FROM users u
        INNER JOIN following f
        WHERE f.username1 = ? AND f.username2 = u.username
        """,
        (logname, username)
    )
    user = user_fetch.fetchall()

    # Add database info to context
    context = {"user": user, "logname": logname, "username": username}
    return flask.render_template("following.html", **context)


@insta485.app.route("/following/", methods=["POST"])
def update_following():
    """POST following."""
    op_arg = request.form.get("operation")
    username = request.form.get('username')
    logname = flask.session['username']
    connection = insta485.model.get_db()
    follows = connection.execute(
        """
        SELECT username1 FROM following
        WHERE username1 = ? AND username2 = ?
        """,
        (logname, username)
    ).fetchone()
    if op_arg == 'follow':
        if follows:
            abort(409)
        connection.execute(
            """
            INSERT INTO following(username1, username2)
            VALUES (?, ?)
            """,
            (logname, username)
        )
    elif op_arg == 'unfollow':
        if not follows:
            abort(409)
        connection.execute(
            """
            DELETE FROM following WHERE username1 = ? AND username2 = ?
            """,
            (logname, username)
        )
    target = request.args.get('target', '/')
    return redirect(target)
