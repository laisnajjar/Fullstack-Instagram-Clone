"""Views, one for each Insta485 page."""
from insta485.views.index import show_index
from insta485.views.index import humanize_filter
from insta485.views.index import download_file
from insta485.views.explore import show_explore
from insta485.views.user import show_user

# from insta485.views.followers import show_followers
from insta485.views.following import show_following
from insta485.views.following import update_following

from insta485.views.posts import show_posts
from insta485.views.posts import update_likes
from insta485.views.posts import update_comments
from insta485.views.posts import update_posts
# from insta485.views.posts import uploads_persmission


from insta485.views.get_account import auth
from insta485.views.get_account import show_login
from insta485.views.get_account import show_account_create
from insta485.views.get_account import show_account_edit
from insta485.views.get_account import show_account_password
from insta485.views.get_account import show_account_delete

from insta485.views.post_account import login
from insta485.views.post_account import logout
from insta485.views.post_account import create
from insta485.views.post_account import delete
from insta485.views.post_account import edit
from insta485.views.post_account import password

from insta485.views.pass_help import hash_password
from insta485.views.pass_help import save_file
from insta485.views.pass_help import abort_unauthenicated_user
