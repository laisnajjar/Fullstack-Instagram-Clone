"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import url_for, redirect
import insta485


@insta485.app.route("/accounts/auth/", methods=["GET"])
def auth():
    """AWS auth."""
    if 'username' not in flask.session:
        flask.abort(403)
    return "Success", 200


@insta485.app.route("/accounts/login/", methods=["GET", "POST"])
def show_login():
    """Login page."""
    if 'username' in flask.session:
        return redirect(url_for('show_index'))
    return flask.render_template("login.html")


@insta485.app.route("/accounts/create/", methods=["GET"])
def show_account_create():
    """Create an account."""
    if 'username' in flask.session:
        return redirect(url_for('show_account_edit'))
    return flask.render_template('account_create.html')


@insta485.app.route("/accounts/edit/", methods=["GET"])
def show_account_edit():
    """Edit user account info."""
    connection = insta485.model.get_db()
    logname = flask.session['username']
    user_fetch = connection.execute(
        """
        SELECT u.username, u.fullname, u.filename, u.email
        FROM users u WHERE username = ?
        """,
        (logname,)
    )
    user = user_fetch.fetchone()
    context = {"user": user, "logname": logname}
    return flask.render_template("account_edit.html", **context)


@insta485.app.route("/accounts/password/", methods=["GET", "POST"])
def show_account_password():
    """Reset account password."""
    logname = flask.session['username']
    context = {"logname": logname}
    return flask.render_template("account_password.html", **context)


@insta485.app.route("/accounts/delete/", methods=["GET"])
def show_account_delete():
    """Accounts Delete."""
    logname = flask.session['username']
    context = {"logname": logname}
    return flask.render_template('account_delete.html', **context)
