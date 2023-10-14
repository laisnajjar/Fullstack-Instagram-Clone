"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import redirect, url_for, request, abort
from insta485.views.pass_help import save_file
from insta485.views.pass_help import abort_unauthenicated_user
import insta485


@insta485.app.route("/posts/<postid>/", methods=["GET"])
def show_posts(postid):
    """User post page."""
    logname, connection = abort_unauthenicated_user()
    if logname is None:
        return redirect(url_for('show_login'))
    connection = insta485.model.get_db()
    posts_fetch = connection.execute(
        """
        SELECT DISTINCT
            p.postid, p.filename AS post_url, p.owner, p.created,
            u.filename as user_profile_pic_url,
            (SELECT COUNT(*) from likes where likes.postid = p.postid)
            AS like_count,
            CASE WHEN EXISTS
            (SELECT 1 FROM likes WHERE likes.postid = p.postid
            AND likes.owner = ?) THEN 1 ELSE 0 END AS has_liked,
            (SELECT COUNT(*) from likes where likes.postid = p.postid)
            AS like_count
        FROM posts p
        INNER JOIN users u ON u.username = p.owner
        WHERE p.postid = ?
        """,
        (logname, postid,)
    )
    post = posts_fetch.fetchone()

    comment_fetch = connection.execute(
        """
        SELECT DISTINCT
            c.text, c.owner, c.postid, c.commentid
        FROM comments c
        WHERE c.postid = ?
        """,
        (postid,)
    )
    comments = comment_fetch.fetchall()
    # Add database info to context
    context = {"post": post, "comments": comments, "logname": logname}
    return flask.render_template("post.html", **context)


@insta485.app.route("/likes/", methods=["POST"])
def update_likes():
    """POST likes."""
    op_arg = request.form.get("operation")
    postid = request.form.get('postid')
    connection = insta485.model.get_db()
    logname = flask.session['username']
    alread_liked = connection.execute(
        """
        SELECT * FROM likes WHERE likes.owner = ? AND postid = ?
        """,
        (logname, postid)
    ).fetchone()
    if op_arg == 'like':
        if alread_liked:
            abort(409)
        connection.execute(
            """
            INSERT INTO likes(owner, postid)
            VALUES (?, ?)
            """,
            (logname, postid)
        )
    elif op_arg == 'unlike':
        if not alread_liked:
            abort(409)
        connection.execute(
            """
            DELETE FROM likes WHERE owner = ? AND  postid = ?
            """,
            (logname, postid)
        )
    target = request.args.get('target', '/')
    return redirect(target)


@insta485.app.route("/comments/", methods=["POST"])
def update_comments():
    """POST comments."""
    logname = flask.session['username']
    op_arg = request.form.get("operation")
    postid = request.form.get('postid')
    commentid = request.form.get('commentid')
    text = request.form.get('text')
    connection = insta485.model.get_db()
    if op_arg == 'create':
        if not text:
            abort(400)
        connection.execute(
            """
            INSERT INTO comments(commentid, text, owner, postid)
            VALUES (?, ?, ?, ?)
            """,
            (commentid, text, logname, postid)
        )
    elif op_arg == 'delete':
        valid_owner = connection.execute(
            """
            SELECT owner from comments
            WHERE commentid = ? AND postid = ?
            """,
            (commentid, postid)
        )
        if not valid_owner:
            abort(403)
        connection.execute(
            """
            DELETE FROM comments WHERE commentid = ?
            """,
            (commentid, )
        )
    target = request.args.get('target', '/')
    return redirect(target)


@insta485.app.route("/posts/", methods=["POST"])
def update_posts():
    """POST posts."""
    logname = flask.session['username']
    op_arg = request.form.get("operation")
    postid = request.form.get('postid')
    connection = insta485.model.get_db()
    if op_arg == 'create':
        fileobj = flask.request.files["file"]
        if not fileobj:
            abort(400)
        uuid_basename = save_file(fileobj)
        connection.execute(
            """
            INSERT into posts(postid, filename, owner)
            VALUES (?, ?, ?)
            """,
            (postid, uuid_basename, logname)
        )
    elif op_arg == 'delete':
        is_owner = connection.execute(
            """
            SELECT owner, filename from posts where postid = ?
            """,
            (postid,)
        ).fetchone()

        if not is_owner:
            abort(403)
        path = insta485.app.config["UPLOAD_FOLDER"]/is_owner['filename']
        if path.exists():
            path.unlink()

        connection.execute(
            """
            DELETE FROM posts WHERE owner = ? AND postid = ?
            """,
            (logname, postid)
        )
    target = request.args.get('target', f'/users/{logname}/')
    return redirect(target)
