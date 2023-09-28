"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from insta485.views.pass_help import abort_unauthenicated_user
import insta485


@insta485.app.route("/explore/", methods=["GET"])
def show_explore():
    """Explore page."""
    logname, connection = abort_unauthenicated_user()
    connection = insta485.model.get_db()
    user_fetch = connection.execute(
        """
        SELECT DISTINCT u.username, u.filename as user_profile_pic
        FROM users u
        WHERE (SELECT COUNT(*) from following f
            WHERE f.username1 = ? AND f.username2 = u.username) = 0
        """,
        (logname,)
    )
    users = user_fetch.fetchall()

    # Add database info to context
    context = {"users": users, "logname": logname}
    return flask.render_template("explore.html", **context)
