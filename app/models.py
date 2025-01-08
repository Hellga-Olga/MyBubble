from app import db, login
from datetime import datetime, timezone
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, url_for
from flask_login import UserMixin
from hashlib import md5
from time import time
import json
import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

followers = sa.Table(
    'followers',
    db.metadata,
    # compound primary keys:
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)

# defines the initial database structure (schema)
# represent users stored in the database
class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)  # type declaration defines the type of the column
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256)) # this column is allowed to be empty or nullable
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    following: so.WriteOnlyMapped['User'] = so.relationship( # the users a given user is following
        secondary=followers, primaryjoin=(followers.c.follower_id==id), # the user must match the follower_id attribute of the association table
        secondaryjoin=(followers.c.followed_id==id), back_populates='followers') # the user on the other side must match the followed_id attribute
    followers: so.WriteOnlyMapped['User'] = so.relationship( # the users that follow a given user
        secondary=followers, primaryjoin=(followers.c.followed_id==id),
        secondaryjoin=(followers.c.follower_id==id), back_populates='following')
    last_message_read_time: so.Mapped[Optional[datetime]]
    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.sender_id', back_populates='author')
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.recipient_id', back_populates='recipient')
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(
        back_populates='user')

    def __repr__(self): # tells Python how to print objects of this class
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        user_id = self.id
        avatar_img = Avatar.query.filter_by(user_id=user_id).first()
        if avatar_img:
            return url_for('static', filename=avatar_img.thumbnail_path)
        digest = md5(self.email.lower().encode('utf-8')).hexdigest() # encodes the email string as bytes before passing it on to the hash function
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    # SQLAlchemy ORM allows working with the following and followers relationships as if they were lists
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id==user.id)
        return db.session.scalar(query) is not None

    # these methods return the follower and following counts for the user
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        # SQLAlchemy requires the inner query to be converted to a sub-query by calling the subquery()
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        # creates two references to the User model allowing to
        # refer to users independently as authors and as followers
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (sa.select(Post).join(Post.author.of_type(Author)) # select() defines the entity that needs to be obtained
                .join(Author.followers.of_type(Follower), isouter=True) # join() is a database operation that combines rows from two tables, according to a given criteria
                .where(sa.or_(Follower.id==self.id, Author.id==self.id,)) # filters the items in the joined table that have a given user as a follower and as an author
                .group_by(Post).order_by(Post.timestamp.desc())) # eliminates any duplicates of the provided argument (Post) and then sorts them

    # returns a JWT token as a string
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod # it can be invoked directly from the class
    def verify_reset_password_token(token):
        try:
            # the value of the reset_password key from the token's payload is the ID of the user
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)

    def unread_message_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        query = sa.select(Message).where(Message.recipient == self,
                                         Message.timestamp > last_read_time)
        return db.session.scalar(sa.select(sa.func.count()).select_from(
            query.subquery()))

    def add_notification(self, name, data):
        db.session.execute(self.notifications.delete().where(
            Notification.name == name))
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc)) # index is useful for retrieving posts in chronological order
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True) # the use of a foreign key "user_id" on the "many" side "post"
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5))
    parent_post: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('post.id', name='fk_parent_post'), index=True)
    board_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('board.id', name='fk_board_id'), nullable=False)

    author: so.Mapped[User] = so.relationship(back_populates='posts')
    board: so.Mapped['Board'] = so.relationship('Board', back_populates="posts")
    images: so.Mapped[list['Image']] = so.relationship(back_populates='post', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def parent(self, id): # method which returns a parent post object
        parent_post = db.first_or_404(sa.select(Post).where(Post.id == id))
        return parent_post

class Message(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                 index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                    index=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    author: so.Mapped[User] = so.relationship(
        foreign_keys='Message.sender_id',
        back_populates='messages_sent')
    recipient: so.Mapped[User] = so.relationship(
        foreign_keys='Message.recipient_id',
        back_populates='messages_received')

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    timestamp: so.Mapped[float] = so.mapped_column(index=True, default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)

    user: so.Mapped[User] = so.relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(str(self.payload_json))


class Image(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id), index=True)
    thumbnail_path: so.Mapped[str] = so.mapped_column(sa.String(255))
    original_path: so.Mapped[str] = so.mapped_column(sa.String(255))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    post: so.Mapped['Post'] = so.relationship(back_populates='images')
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return '<Image {}>'.format(self.id)


class Avatar(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    thumbnail_path: so.Mapped[str] = so.mapped_column(sa.String(255))
    original_path: so.Mapped[str] = so.mapped_column(sa.String(255))
    user_id: so.Mapped[int] = so.mapped_column(db.ForeignKey(User.id))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return '<Avatar {}>'.format(self.name)


class Board(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True, nullable=False)
    posts: so.Mapped[list['Post']] = so.relationship('Post', back_populates="board", lazy="dynamic")

    def __repr__(self):
        return 'Board {}'.format(self.name)