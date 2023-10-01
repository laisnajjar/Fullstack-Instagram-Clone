import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { use } from "chai";

/* Render all posts, "The Father of all posts" */
export default function RenderAllPosts({ url }) {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    let ignoreStaleRequest = false;
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        if (!ignoreStaleRequest) {
          setPosts(data.results.map((post) => post.url));
        }
      })
      .catch((error) => console.log(error));

    return () => {
      ignoreStaleRequest = true;
    };
  }, [url]);

  return (
    <div>
      {posts.map((post) => (
        <Post url={post} key={post} />
      ))}
    </div>
  );
}

/* Display image and post owner of a single post */
function Post({ url }) {
  const [created, setCreated] = useState("");
  const [imgUrl, setImgUrl] = useState("");
  const [owner, setOwner] = useState("");
  const [ownerImgUrl, setOwnerImgUrl] = useState("");
  const [onwerShowUrl, setOwnerShowUrl] = useState("");
  const [postShowUrl, setPostShowUrl] = useState("");
  const [likes, setLikes] = useState("");
  const [lognameLikesThis, setLognameLikesThis] = useState(false);
  const [likesUrl, setLikesUrl] = useState("");
  const [postid, setPostid] = useState("");
  /* handleLikes, call respective api (update or delete likes) */
  const UpdateLikes = () => {
    // unlike if user already liked
    if (lognameLikesThis) {
      fetch(likesUrl, {
        method: "DELETE",
        credentials: "same-origin",
      })
        .then(() => {
          setLikes(likes - 1);
          setLognameLikesThis(false);
        })
        .catch((error) => console.log(error));
    } else {
      // like if user has not liked
      fetch(`/api/v1/likes/?postid=${postid}`, {
        method: "POST",
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then(() => {
          setLikes(likes + 1);
          setLognameLikesThis(true);
        })
        .catch((error) => console.log(error));
    }
  };
  /* Set states */
  useEffect(() => {
    let ignoreStaleRequest = false;
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        if (!ignoreStaleRequest) {
          setCreated(data.created);
          setImgUrl(data.imgUrl);
          setOwner(data.owner);
          setOwnerImgUrl(data.ownerImgUrl);
          setOwnerShowUrl(data.ownerShowUrl);
          setPostShowUrl(data.postShowUrl);
          setLikes(data.likes.numLikes);
          setLognameLikesThis(data.likes.lognameLikesThis);
          setLikesUrl(data.likes.url);
          setPostid(data.postid);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      ignoreStaleRequest = true;
    };
  }, [url]);
  /* Return Page */
  return (
    <div className="container">
      <PostHeader
        owner={owner}
        ownerImgUrl={ownerImgUrl}
        onwerShowUrl={onwerShowUrl}
        created={created}
        postShowUrl={postShowUrl}
      />
      <PostImage imgUrl={imgUrl} />
      <LikesButton
        likes={likes}
        lognameLikesThis={lognameLikesThis}
        UpdateLikes={UpdateLikes}
      />
    </div>
  );
}
/* Header of post includes profile pic, name, and time */
function PostHeader({
  owner,
  ownerImgUrl,
  onwerShowUrl,
  created,
  postShowUrl,
}) {
  return (
    <>
      <link
        rel="stylesheet"
        type="text/css"
        href="{{ url_for('static', filename='css/style.css') }}"
      />
      <div className="post-header">
        <img src={ownerImgUrl} className="profile-pic" alt="owner_image" />
        <a className="post-username" href={onwerShowUrl}>
          {owner}
        </a>
        <a className="post-time" href={postShowUrl}>
          {created}
        </a>
      </div>
    </>
  );
}
/* Post Image return post image */
function PostImage({ imgUrl }) {
  return (
    <div>
      <link
        rel="stylesheet"
        type="text/css"
        href="{{ url_for('static', filename='css/style.css') }}"
      />
      <img className="post-pic" src={imgUrl} alt="post_image" />
    </div>
  );
}
function LikesButton({ likes, lognameLikesThis, UpdateLikes }) {
  return (
    <div>
      <link
        rel="stylesheet"
        type="text/css"
        href="{{ url_for('static', filename='css/style.css') }}"
      />
      <div>
        <div>
          {likes}
          {likes === 1 ? " like" : " likes"}
        </div>
        <button
          data-testid="like-unlike-button"
          onClick={UpdateLikes}
          type="submit"
        >
          {lognameLikesThis ? "Unlike" : "Like"}
        </button>
      </div>
    </div>
  );
}

RenderAllPosts.propTypes = {
  url: PropTypes.string.isRequired,
};
Post.propTypes = {
  url: PropTypes.string.isRequired,
};
PostHeader.propTypes = {
  owner: PropTypes.string.isRequired,
  ownerImgUrl: PropTypes.string.isRequired,
  onwerShowUrl: PropTypes.string.isRequired,
  created: PropTypes.string.isRequired,
  postShowUrl: PropTypes.string.isRequired,
};
PostImage.propTypes = {
  imgUrl: PropTypes.string.isRequired,
};
LikesButton.propTypes = {
  likes: PropTypes.number.isRequired,
  lognameLikesThis: PropTypes.bool.isRequired,
  UpdateLikes: PropTypes.func.isRequired,
};
