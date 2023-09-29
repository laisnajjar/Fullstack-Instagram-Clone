"""REST API."""

import flask
from flask import request, jsonify
import insta485


def check_postid_range(postid):
    """Check if postid is in range."""
    connection = insta485.model.get_db()
    check_fetch = connection.execute(
        "SELECT MAX(postid) as max FROM posts"
    ).fetchone()
    check = check_fetch['max']
    if postid <= check:
        return False
    return True


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
    logname = request.authorization['username']
    postid_lte = request.args.get("postid_lte", default=None, type=int)
    size = request.args.get("size", default=10, type=int)
    page = request.args.get("page", default=0, type=int)
    offset = page * size
    if size < 0 or page < 0:
        return jsonify({"message": "Bad Request", "status_code": 400}), 400
    if postid_lte is None:
        postid_lte_fetch = connection.execute(
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
            (logname, logname)
        ).fetchone()
        postid_lte = postid_lte_fetch['def']
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
    num_posts = connection.execute(
        """
        SELECT postid
        FROM posts
        WHERE (owner IN (
            SELECT username2
            FROM following
            WHERE username1 = ?)
        OR owner = ?)
        """,
        (logname, logname,)
    ).fetchall()
    next_url = ""
    if len(num_posts) > size:
        next_url = f"/api/v1/posts/?size={size}&page={page+1}" \
                f"&postid_lte={postid_lte}"

    url = request.url
    url = url[url.find('/api/'):]

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
    logname = request.authorization['username']
    if check_postid_range(postid_url_slug):
        return jsonify({"message": "Not Found", "status_code": 404}), 404
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
            "url": None if likes['num_likes'] == 0 else f"/api/v1/likes/{likes['likeid']}/"
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
    logname = request.authorization['username']
    postid = int(request.args.get('postid'))
    if check_postid_range(postid):
        return jsonify({"message": "Not Found", "status_code": 404}), 404
    like_fetch = connection.execute(
        """
        SELECT likeid,
        CASE WHEN owner = ? THEN 1 ELSE 0 END AS lognameLikesThis
        FROM likes
        WHERE postid = ?
        """,
        (logname, postid,)
    )
    likes = like_fetch.fetchone()
    # user already liked post
    if likes is not None and likes['lognameLikesThis'] == 1:
        return jsonify({"likeid": likes['likeid'],
                        "url": f"/api/v1/likes/{likes['likeid']}/"}), 200
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
        "SELECT likeid FROM likes WHERE postid = ?",
        (postid,)
    )
    got_likes = get_likeid.fetchone()
    return jsonify({"likeid": got_likes['likeid'],
                    "url": f"/api/v1/likes/{got_likes['likeid']}/"}), 201


@insta485.app.route('/api/v1/likes/<int:likeid>/', methods=["DELETE"])
def api_delete_likes(likeid):
    """Delete like."""
    connection = insta485.model.get_db()
    logname = request.authorization['username']
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
        WHERE likeid = ?
        """,
        (likeid,)
    )
    return "", 204


@insta485.app.route('/api/v1/comments/', methods=["POST"])
def api_add_comment():
    """Add comment to post."""
    connection = insta485.model.get_db()
    logname = request.authorization['username']
    postid = int(request.args.get('postid'))
    text = request.get_json().get('text')
    if check_postid_range(postid):
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
    logname = request.authorization['username']
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
