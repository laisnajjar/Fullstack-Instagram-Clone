"""Helper file."""
import uuid
import hashlib
import pathlib
import flask
import insta485


def hash_password(salt, attempted_password):
    """Hash password with given salt."""
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + attempted_password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def save_file(fileobj):
    """Save file."""
    filename = fileobj.filename
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    fileobj.save(path)
    return uuid_basename


def abort_unauthenicated_user():
    """Abort user not in session."""
    if 'username' not in flask.session:
        return None, None
    logname = flask.session['username']
    connection = insta485.model.get_db()
    return logname, connection


def fetch_user_data(connection, logname, username):
    """Functionlize  user fetch."""
    user_fetch = connection.execute(
        """
        SELECT
            f.username1 as username, u.filename as user_profile_pic_url,
            CASE WHEN EXISTS
            (SELECT 1 FROM following WHERE following.username2 = u.username
            AND following.username1 = ?)
            THEN 1 ELSE 0 END
            AS logname_follows_username
        FROM following f
        INNER JOIN users u
        WHERE f.username2 = ? AND f.username1 = u.username
        """,
        (logname, username)
    )
    return user_fetch.fetchall()


def user_exists_fetch(connection, username):
    """Functionalize user exists fetch."""
    user_fetch = connection.execute(
        "SELECT COUNT(*) FROM users WHERE username = ?",
        (username,)
    )
    return user_fetch.fetchone()
