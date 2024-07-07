from sqlmodel import select

from .models import Site
from .models import Board
from .models import Post
from .models import User


def uid_exists(db_session, model,
               unique_id_field, unique_id_value: int | str) -> bool:

        statement = \
            select(model).where(unique_id_field == unique_id_value).limit(limit=1)

        does_uid_exist: model | None = \
            db_session.exec(statement=statement).first()

        return bool(does_uid_exist)


def board_id_exists(db_session, board_id: int) -> bool:
    board_exists: bool = uid_exists(db_session=db_session,
                                    model=Board,
                                    unique_id_field=Board.id,
                                    unique_id_value=board_id)
    return board_exists


def board_uri_exists(db_session, board_uri: str) -> bool:
    board_exists: bool = uid_exists(db_session=db_session,
                                    model=Board,
                                    unique_id_field=Board.uri,
                                    unique_id_value=board_uri)
    return board_exists


def post_id_exists(db_session, post_id: int) -> bool:
    post_exists: bool = uid_exists(db_session=db_session,
                                    model=Post,
                                    unique_id_field=Post.id,
                                    unique_id_value=post_id)
    return post_exists


def user_id_exists(db_session, user_id: int) -> bool:
    user_exists: bool = uid_exists(db_session=db_session,
                                   model=User,
                                   unique_id_field=User.id,
                                   unique_id_value=user_id)
    return user_exists


def username_exists(db_session, username: str) -> bool:
    user_exists: bool = uid_exists(db_session=db_session,
                                    model=User,
                                    unique_id_field=User.username,
                                    unique_id_value=username)
    return user_exists


def get_thread(post_obj, max_depth=3, parent_depth=0) -> dict:
    # Thread's OP is level 1

    current_depth = parent_depth + 1

    post = post_obj.model_dump()
    post.update({"replies": list()})

    replies_list: list[Post] = post_obj.replies
    if replies_list and current_depth < max_depth:
        for reply_obj in replies_list:
            reply: dict = get_thread(post_obj=reply_obj,
                                         max_depth=max_depth,
                                         parent_depth=current_depth)
            post["replies"].append(reply)

    return post

#  def get_thread_flattened(post_obj, max_depth=3, parent_depth=0) -> list:
def get_thread_flattened(post_obj, posts=[], max_depth=3, parent_depth=0) -> list[dict]:
    # Thread's OP is level 1

    current_depth = parent_depth + 1

    #  posts: list[dict] = list()

    post: dict = post_obj.model_dump()
    posts.append(post)
    #  post.update({"replies": list()})

    replies_list: list[Post] = post_obj.replies
    if replies_list and current_depth < max_depth:
        for reply_obj in replies_list:
            reply: list = get_thread_flattened(post_obj=reply_obj,
                                               posts=posts,
                                               max_depth=max_depth,
                                               parent_depth=current_depth)
            #  post["replies"].append(reply)
            #  posts.append(reply)
            #posts.extend()(reply)

    return posts
