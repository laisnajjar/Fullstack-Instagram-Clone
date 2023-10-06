"""REST API."""

import flask
from flask import request, jsonify
import insta485


def check_password(logname, password):
    """Check password."""
    # fetch user from database
    connection = insta485.model.get_db()
    user_fetch = connection.execute(
        """
        SELECT u.username, u.password
        FROM users u
        WHERE u.username = ?
        """,
        (logname,)
    )
    users = user_fetch.fetchone()
    # check user exists
    if users is None:
        return False
    # hash given password with same salt as password in database
    # then check if passwords match
    salt = users['password'].split('$')[1]
    password_db_string = insta485.views.pass_help.hash_password(salt, password)
    if users['password'] == password_db_string:
        return True
    return False


def check_login():
    """Test login."""
    # user not in session, must check authorization
    if 'username' not in flask.session:
        # authorization not provided
        if request.authorization is None:
            return None
        # authorization provided, check password
        logname = request.authorization['username']
        password = request.authorization['password']
        if not check_password(logname, password):
            return None
        return logname
    # return logname from flask session
    logname = flask.session['username']
    return logname


def check_postid_range(postid):
    """Check if postid is in range."""
    # fecth Max(*) from databse
    connection = insta485.model.get_db()
    check_fetch = connection.execute(
        "SELECT MAX(postid) as max FROM posts"
    ).fetchone()
    # check if postid is in range of max
    check = check_fetch['max']
    if postid <= check:
        return False
    return True


def get_newest_post_id(logname):
    """Get newest post id."""
    connection = insta485.model.get_db()
    postid_fetch = connection.execute(
        """
        SELECT postid as def
            FROM posts
            WHERE (owner IN (
                SELECT username2
                FROM following
                WHERE username1 = ?)
            OR owner = ?)
            ORDER BY postid DESC
        """,
        (logname, logname,)
    ).fetchone()
    return postid_fetch['def']


def get_num_posts(logname):
    """Get number of posts."""
    connection = insta485.model.get_db()
    postid_fetch = connection.execute(
        """
        SELECT COUNT(*) as num_posts
            FROM posts
            WHERE (owner IN (
                SELECT username2
                FROM following
                WHERE username1 = ?)
            OR owner = ?)
        """,
        (logname, logname,)
    ).fetchone()
    return postid_fetch['num_posts']


@insta485.app.route('/api/v1/')
def api_get_resource_urls():
    """Return API resource URLs."""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return jsonify(**context)


@insta485.app.route('/api/v1/posts/')
def api_get_newest_posts():
    """Return 10 newest posts."""
    connection = insta485.model.get_db()
    # authentication
    logname = check_login()
    if logname is None:
        return jsonify({"message": "Forbidden", "status_code": 403}), 403
    # get query parameters
    postid_lte = request.args.get("postid_lte", default=None, type=int)
    size = request.args.get("size", default=10, type=int)
    page = request.args.get("page", default=0, type=int)
    offset = page * size
    # check if size and page are positive
    if size < 0 or page < 0:
        return jsonify({"message": "Bad Request", "status_code": 400}), 400
    # if postid_lte is None, we need the newest postid
    if postid_lte is None:
        postid_lte = get_newest_post_id(logname)
    # fetch (size) amount of posts
    # where postid <= postid_lte
    # and owner is followed by logname
    # starting from ids > page * size
    post_fetch_newest = connection.execute(
        """
        SELECT postid
        FROM posts
        WHERE (owner IN (
            SELECT username2
            FROM following
            WHERE username1 = ?)
        OR owner = ?)
        AND postid <= ?
        ORDER BY postid DESC
        LIMIT ?
        OFFSET ?;
        """,
        (logname, logname, postid_lte, size, offset)
    )
    posts = post_fetch_newest.fetchall()
    # if there are more posts than requested, next url is valid
    next_url = ""
    if get_num_posts(logname) - (offset) >= size:
        next_url = f"/api/v1/posts/?size={size}&page={page+1}" \
                f"&postid_lte={postid_lte}"
    # get url from flask, but strip extra (e.g. "localhost:5000")
    url = request.url
    url = url[url.find('/api/'):]
    # context
    context = {
        "next": next_url,
        "results": [{
            "postid": post['postid'],
            "url": f"/api/v1/posts/{post['postid']}/"
        } for post in posts],
        "url": url
    }
    return jsonify(**context)


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/', methods=["GET"])
def api_get_post(postid_url_slug):
    """Return post on postid."""
    connection = insta485.model.get_db()
    # authentication
    logname = check_login()
    if logname is None:
        return jsonify({"message": "Forbidden", "status_code": 403}), 403
    # check if postid is in range
    if check_postid_range(postid_url_slug):
        return jsonify({"message": "Not Found", "status_code": 404}), 404
    # fetch comments, post, and likes
    comment_fetch = connection.execute(
        """SELECT commentid, text, owner, postid, created
        FROM comments WHERE postid = ?""",
        (postid_url_slug,)
    )
    comments = comment_fetch.fetchall()
    post_fetch = connection.execute(
        """
        SELECT p.postid, p.filename, p.owner, p.created, u.filename as headshot
        FROM posts p
        INNER JOIN users u ON u.username = p.owner
        WHERE postid = ?
        """,
        (postid_url_slug,)
    )
    post = post_fetch.fetchone()
    like_fetch = connection.execute(
        """
        SELECT Count(*) as num_likes, likeid,
        CASE WHEN owner = ? THEN 1 ELSE 0 END AS lognameLikesThis
        FROM likes
        WHERE postid = ?
        """,
        (logname, postid_url_slug,)
    )
    likes = like_fetch.fetchone()
    # context
    context = {
        "comments": [
            {
                "commentid": comment['commentid'],
                "lognameOwnsThis": comment['owner'] == logname,
                "owner": comment['owner'],
                "ownerShowUrl": f"/users/{comment['owner']}/",
                "text": comment['text'],
                "url": f"/api/v1/comments/{comment['commentid']}/"
            } for comment in comments
        ],
        "comments_url": f"/api/v1/comments/?postid={postid_url_slug}",
        "created": post['created'],
        "imgUrl": f"/uploads/{post['filename']}",
        "likes": {
            "lognameLikesThis": likes['lognameLikesThis'] == 1,
            "numLikes": likes['num_likes'],
            "url": None if likes['num_likes'] == 0
            else f"/api/v1/likes/{likes['likeid']}/"
            },
        "owner": post['owner'],
        "ownerImgUrl": f"/uploads/{post['headshot']}",
        "ownerShowUrl": f"/users/{post['owner']}/",
        "postShowUrl": f"/posts/{post['postid']}/",
        "postid": post['postid'],
        "url": f"/api/v1/posts/{post['postid']}/",

    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/likes/', methods=["POST"])
def api_update_likes():
    """Update likes."""
    connection = insta485.model.get_db()
    logname = check_login()
    if logname is None:
        return jsonify({"message": "Forbidden", "status_code": 403}), 403
    postid = int(request.args.get('postid'))
    if check_postid_range(postid):
        return jsonify({"message": "Not Found", "status_code": 404}), 404
    like_fetch = connection.execute(
        """
        SELECT likeid as id,
        CASE WHEN owner = ? THEN 1 ELSE 0 END AS lognameLikesThis
        FROM likes
        WHERE postid = ?
        """,
        (logname, postid,)
    )
    likes = like_fetch.fetchone()
    # user already liked post
    if likes is not None and likes['lognameLikesThis'] == 1:
        return jsonify({"likeid": likes['id'],
                        "url": f"/api/v1/likes/{likes['id']}/"}), 200
    # update user to like post
    connection.execute(
        """
        INSERT INTO likes (owner, postid)
        VALUES (?, ?)
        """,
        (logname, postid,)
    )
    # get likeids from inserted
    get_likeid = connection.execute(
        "SELECT likeid FROM likes WHERE postid = ? and owner = ?",
        (postid, logname,)
    )
    got_likes = get_likeid.fetchone()
    return jsonify({"likeid": got_likes['likeid'],
                    "url": f"/api/v1/likes/{got_likes['likeid']}/"}), 201


@insta485.app.route('/api/v1/likes/<int:likeid>/', methods=["DELETE"])
def api_delete_likes(likeid):
    """Delete like."""
    connection = insta485.model.get_db()
    logname = check_login()
    if logname is None:
        return jsonify({"message": "Forbidden", "status_code": 403}), 403
    like_fetch = connection.execute(
        """
        SELECT likeid,
        CASE WHEN owner = ? THEN 1 ELSE 0 END AS lognameOwnsThis
        FROM likes WHERE likeid = ?
        """,
        (logname, likeid)
    )
    like_check = like_fetch.fetchone()
    if like_check is None:
        return "", 404
    if like_check['lognameOwnsThis'] == 0:
        return "", 403
    connection.execute(
        """
        DELETE FROM likes
        WHERE likeid = ? and owner = ?
        """,
        (likeid, logname,)
    )
    return "", 204


@insta485.app.route('/api/v1/comments/', methods=["POST"])
def api_add_comment():
    """Add comment to post."""
    connection = insta485.model.get_db()
    logname = check_login()
    if logname is None:
        return jsonify({"message": "Forbidden", "status_code": 403}), 403
    postid = int(request.args.get('postid'))
    text = request.get_json().get('text')
    if check_postid_range(postid) or text is None:
        return jsonify({"message": "Not Found", "status_code": 404}), 404
    connection.execute(
        """
        INSERT INTO comments (text, owner, postid)
        VALUES (?, ?, ?)
        """,
        (text, logname, postid,)
    )
    id_fetch = connection.execute(
        "SELECT last_insert_rowid() as commentid"
    )
    get_id = id_fetch.fetchone()
    context = {
        "commentid": get_id['commentid'],
        "lognameOwnsThis": True,
        "owner": logname,
        "ownerShowUrl": f"/users/{logname}/",
        "text": text,
        "url": f"/api/v1/comments/{get_id['commentid']}/"
    }
    return jsonify(**context), 201


@insta485.app.route('/api/v1/comments/<int:commentid>/', methods=["DELETE"])
def api_del_comment(commentid):
    """Delete comment."""
    connection = insta485.model.get_db()
    logname = check_login()
    if logname is None:
        return jsonify({"message": "Forbidden", "status_code": 403}), 403
    comment_fetch = connection.execute(
        """
        SELECT commentid,
        CASE WHEN owner = ? THEN 1 ELSE 0 END AS lognameOwnsThis
        FROM comments WHERE commentid = ?
        """,
        (logname, commentid)
    )
    comment_check = comment_fetch.fetchone()
    if comment_check is None:
        return "", 404
    if comment_check['lognameOwnsThis'] == 0:
        return "", 403
    connection.execute(
        """
        DELETE FROM comments
        WHERE commentid = ?
        """,
        (commentid,)
    )
    return "", 204
