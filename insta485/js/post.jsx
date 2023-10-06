import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import InfiniteScroll from "react-infinite-scroll-component";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";

dayjs.extend(relativeTime);
dayjs.extend(utc);

/* Render all posts, "The Father of all posts" */
export default function RenderAllPosts({ url }) {
  const [posts, setPosts] = useState([]);
  const [nextUrl, setNextUrl] = useState("");
  const [hasMore, setHasMore] = useState(true);
  /* fecth more data */
  const fetchMoreData = () => {
    fetch(nextUrl, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        setPosts((prevPosts) => [
          ...prevPosts,
          ...data.results.map((post) => post.url),
        ]);
        setNextUrl(data.next);
      })
      .catch((error) => console.log(error));
  };
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
          setNextUrl(data.next);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      ignoreStaleRequest = true;
    };
  }, [url]);

  useEffect(() => {
    if (nextUrl === null) {
      setHasMore(false);
    }
  }, [nextUrl]);

  return (
    <InfiniteScroll
      style={{ overflow: "auto", height: "100vh" }}
      dataLength={posts.length}
      next={fetchMoreData}
      hasMore={hasMore}
      loader={<h4>Loading...</h4>}
    >
      <div>
        {posts.map((post) => (
          <Post postUrl={post} key={post} />
        ))}
      </div>
    </InfiniteScroll>
  );
}

/* Display image and post owner of a single post */
function Post({ postUrl }) {
  const [created, setCreated] = useState("");
  const [imgUrl, setImgUrl] = useState("");
  const [owner, setOwner] = useState("");
  const [ownerImgUrl, setOwnerImgUrl] = useState("");
  const [onwerShowUrl, setOwnerShowUrl] = useState("");
  const [postShowUrl, setPostShowUrl] = useState("");
  const [likes, setLikes] = useState(0);
  const [lognameLikesThis, setLognameLikesThis] = useState(false);
  const [likesUrl, setLikesUrl] = useState("");
  const [postid, setPostid] = useState("");
  const [comments, setComments] = useState([]);
  /* handleLikes, call respective api (update or delete likes) */
  const UpdateLikes = () => {
    /* unlike if user already liked */
    if (lognameLikesThis) {
      fetch(likesUrl, {
        method: "DELETE",
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          setLikes((likes) => likes - 1);
          setLognameLikesThis(false);
        })
        .catch((error) => console.log(error));
    } else {
      // like if user has not liked
      console.log("/api/v1/likes/?postid=${postid}");
      console.log(postid);
      fetch(`/api/v1/likes/?postid=${postid}`, {
        method: "POST",
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          setLikes((likes) => likes + 1);
          setLognameLikesThis(true);
          setLikesUrl(data.url);
        })
        .catch((error) => console.log(error));
    }
  };
  /* Double click to like */
  const DoubleClickLikes = () => {
    if (lognameLikesThis === false) {
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
  /* Post a comment */
  const PostComment = (newCommentText) => {
    fetch(`/api/v1/comments/?postid=${postid}`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: newCommentText }),
    })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((newComment) => {
        setComments([...comments, newComment]);
      })
      .catch((error) => console.log(error));
  };
  /* Delete a comment */
  const DeleteComment = (commentUrl) => {
    fetch(commentUrl, {
      method: "DELETE",
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
      })
      .then(() => {
        setComments(comments.filter((comment) => comment.url !== commentUrl));
      })
      .catch((error) => console.log(error));
  };

  /* Set states */
  useEffect(() => {
    let ignoreStaleRequest = false;
    fetch(postUrl, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        if (!ignoreStaleRequest) {
          setImgUrl(data.imgUrl);
          setOwner(data.owner);
          setOwnerImgUrl(data.ownerImgUrl);
          setOwnerShowUrl(data.ownerShowUrl);
          setPostShowUrl(data.postShowUrl);
          setLikes(Number(data.likes.numLikes));
          setLognameLikesThis(data.likes.lognameLikesThis);
          setLikesUrl(data.likes.url);
          setPostid(data.postid);
          setComments(data.comments);
          const humanReadableTime = dayjs.utc(data.created).local().fromNow();
          setCreated(humanReadableTime);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      ignoreStaleRequest = true;
    };
  }, [postUrl]);
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
      <PostImage imgUrl={imgUrl} DoubleClickLikes={DoubleClickLikes} />
      <LikesButton
        likes={likes}
        lognameLikesThis={lognameLikesThis}
        UpdateLikes={UpdateLikes}
      />
      <Comments
        comments={comments}
        PostComment={PostComment}
        DeleteComment={DeleteComment}
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
    <div className="post-header">
      <img src={ownerImgUrl} className="profile-pic" alt="owner_image" />
      <a className="post-username" href={onwerShowUrl}>
        {owner}
      </a>
      <a className="post-time" href={postShowUrl}>
        {created}
      </a>
    </div>
  );
}
/* Post Image return post image */
function PostImage({ imgUrl, DoubleClickLikes }) {
  return (
    <img
      className="post-pic"
      src={imgUrl}
      alt="post_image"
      onDoubleClick={() => DoubleClickLikes()}
    />
  );
}
function LikesButton({ likes, lognameLikesThis, UpdateLikes }) {
  return (
    <div>
      <div>
        <b>
          {likes}
          {likes === 1 ? " like" : " likes"}
        </b>
      </div>
      <button
        data-testid="like-unlike-button"
        onClick={UpdateLikes}
        type="submit"
      >
        {lognameLikesThis ? "Unlike" : "Like"}
      </button>
    </div>
  );
}

function Comments({ comments, PostComment, DeleteComment }) {
  // console.log(comments);
  const [newComment, setNewComment] = useState("");

  const handleInputChange = (event) => {
    setNewComment(event.target.value);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    PostComment(newComment);
    setNewComment("");
  };
  const commentSection = comments.map((comment) => (
    <div key={comment.commentid} className="comments">
      <a className="username" href={comment.ownerShowUrl}>
        {comment.owner}
      </a>
      <span data-testid="comment-text">{comment.text}</span>
      {comment.lognameOwnsThis && (
        <button
          data-testid="delete-comment-button"
          onClick={() => DeleteComment(comment.url)}
          type="submit"
        >
          Delete
        </button>
      )}
    </div>
  ));
  return (
    <div>
      <div>{commentSection}</div>
      <form data-testid="comment-form" onSubmit={handleSubmit}>
        <input
          type="text"
          name="comment"
          placeholder="Add a comment..."
          value={newComment}
          onChange={handleInputChange}
        />
      </form>
    </div>
  );
}

RenderAllPosts.propTypes = {
  url: PropTypes.string.isRequired,
};
Post.propTypes = {
  postUrl: PropTypes.string.isRequired,
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
  DoubleClickLikes: PropTypes.func.isRequired,
};
LikesButton.propTypes = {
  likes: PropTypes.number.isRequired,
  lognameLikesThis: PropTypes.bool.isRequired,
  UpdateLikes: PropTypes.func.isRequired,
};
Comments.propTypes = {
  comments: PropTypes.arrayOf(
    PropTypes.shape({
      commentid: PropTypes.number.isRequired,
      owner: PropTypes.string.isRequired,
      ownerShowUrl: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
    }),
  ).isRequired,
  PostComment: PropTypes.func.isRequired,
  DeleteComment: PropTypes.func.isRequired,
};
