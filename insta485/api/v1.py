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
    post_fetch_newest = connection.execute(
        """
        SELECT postid
        FROM posts
        WHERE owner IN (
            SELECT username2
            FROM following
            WHERE username1 = ?)
        OR owner = ?
        ORDER BY postid ASC
        LIMIT 10;
        """,
        (logname, logname,)
    )
    posts = post_fetch_newest.fetchall()
    context = {
        "next": "",
        "results": [{
            "postid": post['postid'],
            "url": f"/api/v1/posts/{post['postid']}/"
        } for post in posts],
        "url": "apli/v1/posts"
    }
    return jsonify(**context)


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
def get_post(postid_url_slug):
    """Return post on postid.

    Example:
    {
      "created": "2017-09-28 04:33:28",
      "imgUrl": "/uploads/122a7d27ca1d7420a1072f695d9290fad4501a41.jpg",
      "owner": "awdeorio",
      "ownerImgUrl": "/uploads/e1a7c5c32973862ee15173b0259e3efdb6a391af.jpg",
      "ownerShowUrl": "/users/awdeorio/",
      "postShowUrl": "/posts/1/",
      "url": "/api/v1/posts/1/"
    }
    """
    context = {
        "created": "2017-09-28 04:33:28",
        "imgUrl": "/uploads/122a7d27ca1d7420a1072f695d9290fad4501a41.jpg",
        "owner": "awdeorio",
        "ownerImgUrl": "/uploads/e1a7c5c32973862ee15173b0259e3efdb6a391af.jpg",
        "ownerShowUrl": "/users/awdeorio/",
        "postid": "/posts/{}/".format(postid_url_slug),
        "url": flask.request.path,
    }
    return flask.jsonify(**context)
