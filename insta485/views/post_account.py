"""For posts."""
import uuid
import os
import flask
from flask import url_for, redirect, request, abort
import insta485
from insta485.views.pass_help import hash_password, save_file


@insta485.app.route("/accounts/", methods=["POST"])
def account():
    """/accounts/."""
    op_args = request.form.get("operation")
    if op_args == 'login':
        return login()
    if op_args == 'create':
        return create()
    if op_args == 'delete':
        return delete()
    if op_args == 'edit_account':
        return edit()
    if op_args == 'update_password':
        return password()

    target = request.args.get('target', '/')
    return redirect(target)


@insta485.app.route("/accounts/logout/", methods=["POST"])
def logout():
    """Logout redirect to login."""
    flask.session.clear()
    return redirect(url_for('show_login'))


def login():
    """Login page."""
    # Connect to database
    connection = insta485.model.get_db()
    attempted_username = flask.request.form['username']
    attempted_password = flask.request.form['password']
    if not attempted_password or not attempted_password:
        abort(409)
    user_fetch = connection.execute(
        """
        SELECT u.username, u.password
        FROM users u
        WHERE u.username = ?
        """,
        (attempted_username,)
    )
    users = user_fetch.fetchone()
    if users is None:
        abort(403)
    salt = users['password'].split('$')[1]
    password_db_string = hash_password(salt, attempted_password)
    if users is None or users['password'] != password_db_string:
        abort(403)
    flask.session['username'] = attempted_username
    return redirect(url_for('show_index'))


def create():
    """Create an account."""
    connection = insta485.model.get_db()
    created_username = flask.request.form.get('username')
    created_fullname = flask.request.form.get('fullname')
    created_email = flask.request.form.get('email')
    created_file = flask.request.form.get('file')
    created_password = flask.request.form.get('password')
    # empty args
    if not (created_username or created_fullname
            or created_email or created_file):
        abort(400)
    # username taken
    user_exists = connection.execute(
        """
        SELECT username FROM users where username = ?
        """,
        (created_username,)
    ).fetchone()
    if user_exists:
        abort(409)
    # storing files
    fileobj = flask.request.files['file']
    uuid_basename = save_file(fileobj)
    # hashing password
    salt = uuid.uuid4().hex
    password_db_string = hash_password(salt, created_password)
    connection.execute(
        """
        INSERT INTO users (username, fullname, email, filename, password)
        VALUES (?, ?, ?, ?, ?)
        """,
        (created_username, created_fullname,
         created_email, uuid_basename, password_db_string,)
    )
    flask.session['username'] = created_username
    return redirect(url_for('show_index'))


def delete():
    """Accounts Delete."""
    if 'username' not in flask.session:
        abort(403)
    logname = flask.session['username']
    connection = insta485.model.get_db()
    post_files = connection.execute(
        "SELECT filename FROM posts WHERE owner = ?", (logname,)
    ).fetchall()
    user_icon = connection.execute(
        "SELECT filename FROM users WHERE username = ?", (logname,)
    ).fetchone()

    for file in post_files:
        path = insta485.app.config["UPLOAD_FOLDER"]/file['filename']
        print(f'THE PATH !!!!!!!!!!!!!!{path}')
        os.remove(path)
        print(f'{path.exists()}')
    path = insta485.app.config["UPLOAD_FOLDER"]/user_icon["filename"]
    os.remove(path)

    connection.execute(
        """
        DELETE FROM users WHERE username = ?
        """,
        (logname,)
    )
    flask.session.clear()
    target = request.args.get('target', '/')
    return redirect(target)


def edit():
    """Edit user account info."""
    if 'username' not in flask.session:
        abort(403)
    connection = insta485.model.get_db()
    logname = flask.session['username']
    updated_fullname = flask.request.form.get('fullname')
    updated_email = flask.request.form.get('email')
    fileobj = flask.request.files['file']
    if not (updated_fullname or updated_email):
        abort(400)
    if not fileobj:
        connection.execute(
            """
            UPDATE users
            SET fullname = ?, email = ?
            WHERE username = ?
            """,
            (updated_fullname, updated_email, logname,)
        )
    else:
        # fileobj = flask.request.files['file']
        fileobj = flask.request.files['file']
        uuid_basename = save_file(fileobj)
        old_file = connection.execute(
            """
            SELECT filename FROM users where username = ?
            """,
            (logname,)
        ).fetchone()
        path = insta485.app.config["UPLOAD_FOLDER"]/old_file['filename']
        if path.exists():
            path.unlink()
        connection.execute(
            """
            UPDATE users
            SET fullname = ?, email = ?, filename = ?
            WHERE username = ?
            """,
            (updated_fullname, updated_email, uuid_basename, logname,)
        )
    target = request.args.get('target', '/')
    return redirect(target)


def password():
    """Change password."""
    if 'username' not in flask.session:
        abort(403)
    connection = insta485.model.get_db()
    logname = flask.session['username']
    old_password = flask.request.form.get('password')
    new_password1 = flask.request.form.get('new_password1')
    new_password2 = flask.request.form.get('new_password2')
    if not (old_password or new_password1 or new_password2):
        abort(400)
    if new_password1 != new_password2:
        abort(401)
    password_fetch = connection.execute(
        """
        SELECT password FROM users where username = ?
        """,
        (logname,)
    ).fetchone()
    # hash old password
    salt = password_fetch['password'].split('$')[1]
    password_db_string = hash_password(salt, old_password)
    if password_fetch['password'] != password_db_string:
        abort(401)
    # hash new password
    salt = uuid.uuid4().hex
    password_db_string2 = hash_password(salt, new_password1)
    connection.execute(
        """
        UPDATE users
        SET password = ?
        WHERE username = ?
        """,
        (password_db_string2, logname,)
    ).fetchone()
    target = request.args.get('target', '/')
    return redirect(target)
