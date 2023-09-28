"""REST API."""

import flask
from flask import request, jsonify
import insta485


@insta485.app.route('/api/v1/')
def get_resource_urls():
    """Return API resource URLs."""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return jsonify(**context)


@insta485.app.route('/api/v1/posts/')
def get_newest_posts():
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


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
def get_post(postid_url_slug):
    """Return post on postid."""
    connection = insta485.model.get_db()
    logname = request.authorization['username']
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
    owner = post['owner']
    like_fetch = connection.execute(
        """
        SELECT Count(*) as num_likes, likeid,
        CASE WHEN owner = ? THEN 1 ELSE 0 END AS lognameLikesThis
        FROM likes
        WHERE postid = ?
        """,
        (owner, postid_url_slug,)
    )
    likes = like_fetch.fetchone()
    context = {
       "comments": [{
           "commentid":  comment['commentid'],
           "lognameOwnsThis": True if comment['owner'] == logname else False,
           "owner": comment['owner'],
           "ownerShowUrl":  f"/users/{comment['owner']}/",
           "text": comment['text'],
           "url": f"/api/v1/comments/{comment['commentid']}/"
                } for comment in comments],
        "comments_url": f"/api/v1/comments/?postid={postid_url_slug}",
        "created": post['created'],
        "imgUrl": f"/uploads/{post['filename']}",
        "likes": [{
            "lognameLikesThis":
            True if likes['lognameLikesThis'] == 1 else False,
            "numLikes": likes['num_likes'],
            "url": f"/api/v1/likes/{likes['likeid']}/"
            }],
        "owner": post['owner'],
        "ownerImgUrl": f"/uploads/{post['headshot']}",
        "ownerShowUrl": f"/users/{post['owner']}/",
        "postShowUrl": f"/posts/{post['postid']}/",
        "postid": post['postid'],
        "url": f"/api/v1/posts/{post['postid']}/",

    }
    return flask.jsonify(**context)
