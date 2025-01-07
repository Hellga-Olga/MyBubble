from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from werkzeug.utils import secure_filename
import sqlalchemy as sa
from langdetect import detect, LangDetectException
from PIL import Image as Image_pil
from upload import validate_image, file_exist
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, MessageForm, AvatarUploadForm
from app.models import User, Post, Message, Notification, Image, Board, Avatar
from app.translate import translate
from app.main import bp
from sqlalchemy.orm import joinedload
import os
import uuid


@bp.before_request
def before_request(): # executed right before the view function
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])  #decorator creates an association between the URL given as an argument and the function
def index():
    page = request.args.get('page', 1, type=int)
    # query = sa.select(Post).order_by(Post.timestamp.desc())
    query = sa.select(Post).options(joinedload(Post.images)).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), posts=posts.items, next_url=next_url,
                           prev_url=prev_url) #converts a template into a complete HTML page


@bp.route('/board/<string:board_name>', methods=['GET', 'POST'])
def board_posts(board_name):
    form = PostForm()
    board = Board.query.filter_by(name=board_name).first_or_404()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, board=board, language=language)
        db.session.add(post)
        db.session.flush()
        if form.image.data:
            for file in form.image.data:
                if file_exist(file.stream) == 'Ok':
                    given_filename = secure_filename(
                        file.filename)  # ensures the uploaded file's name is safe for the system
                    file_ext = os.path.splitext(given_filename)[1]  # takes the file's extension
                    if file_ext == '':
                        file_ext = '.' + os.path.splitext(given_filename)[0]
                    filename = str(uuid.uuid4())  # assigns a unique name for a file
                    orig_path = os.path.join(current_app.config['UPLOAD_PATH'], f'{filename}{file_ext}')
                    file.save(orig_path)
                    db_orig_path = f'{current_app.config['STATIC_PATH']}{filename}{file_ext}'  # static path to write in database
                    file_variants = save_image_variants(file, current_app.config['UPLOAD_PATH'], current_app.config['STATIC_PATH'], filename, file_ext)
                    image = Image(post=post, thumbnail_path=file_variants['thumbnail'],
                                  original_path=db_orig_path, user_id=current_user.id)  # automatically sets post_id
                    db.session.add(image)
        db.session.commit()
        if form.image.data == [] and form.post.data == '':
            return redirect(url_for('main.board_posts', board_name=board_name))
        flash(_('Your reply is published!'))
        return redirect(url_for('main.board_posts', board_name=board_name))

    page = request.args.get('page', 1, type=int)
    query = board.posts.order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)  # Pagination object
    next_url = url_for('main.board_posts', board_name=board_name, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.board_posts', board_name=board_name, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('board_posts.html', title= board_name, board=board, form=form, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required # Flask-Login's function, allows only registered users, otherwise redirects to the login page
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username)) # sends a 404 error back to the client in the case that there are no results
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, form=form,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Changes have been saved'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
# returns a dictionary with data that the client has submitted in JSON format
def translate_text():
    data = request.get_json()
    return {'text': translate(data['text'], data['source_language'], data['dest_language'])}


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count',
                              user.unread_message_count())
        db.session.commit()
        flash(_('Your message has been sent'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=current_app.config['POSTS_PER_PAGE'],
                           error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]


def save_image_variants(uploaded_image, output_dir, static_path, filename, extension):
    sizes = {
        'thumbnail': (150, 150), # size for thumbnail
    }

    image = Image_pil.open(uploaded_image)
    variants = {}
    for size_name, dimensions in sizes.items():
        path = os.path.join(output_dir, f"{filename}_{size_name}{extension}")
        image_copy = image.copy()
        image_copy.thumbnail(dimensions)
        image_copy.save(path)
        variant_path = f'{static_path}{filename}_{size_name}{extension}'
        variants[size_name] = variant_path
    return variants


@bp.route('/reply/<board_id>/<post_id>/<post_author>', methods=['GET', 'POST'])
@login_required
def reply(board_id, post_id, post_author):
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, parent_post=post_id, board_id=board_id, language=language)
        db.session.add(post)
        db.session.flush()
        if form.image.data:
            for file in form.image.data:
                if file_exist(file.stream) == 'Ok':
                    given_filename = secure_filename(file.filename) # ensures the uploaded file's name is safe for the system
                    file_ext = os.path.splitext(given_filename)[1] # takes the file's extension
                    if file_ext == '':
                        file_ext = '.' + os.path.splitext(given_filename)[0]
                    filename = str(uuid.uuid4()) # assigns a unique name for a file
                    orig_path = os.path.join(current_app.config['UPLOAD_PATH'], f'{filename}{file_ext}')
                    file.save(orig_path)
                    db_orig_path = f'{current_app.config['STATIC_PATH']}{filename}{file_ext}' # static path to write in database
                    file_variants = save_image_variants(file, current_app.config['UPLOAD_PATH'], current_app.config['STATIC_PATH'], filename, file_ext)
                    image = Image(post=post, thumbnail_path=file_variants['thumbnail'],
                                original_path=db_orig_path, user_id=current_user.id ) # automatically sets post_id
                    db.session.add(image)
        db.session.commit()
        board = db.session.scalar(sa.select(Board).where(Board.id == board_id))
        if form.image.data == [] and form.post.data == '':
            return redirect(url_for('main.board_posts', board_name=board.name))
        flash(_('Your reply is published!'))
        return redirect(url_for('main.board_posts', board_name=board.name))
    return render_template('reply.html', title='Reply', form=form, recipient=post_author)


@bp.route('/avatar_upload', methods=['GET', 'POST'])
@login_required
def avatar_upload():
    form = AvatarUploadForm()
    if form.validate_on_submit():
        if form.avatar.data:
            file = form.avatar.data
            if file_exist(file.stream) == 'Ok':
                given_filename = secure_filename(file.filename) # ensures the uploaded file's name is safe for the system
                file_ext = os.path.splitext(given_filename)[1] # takes the file's extension
                if file_ext == '':
                    file_ext = '.' + os.path.splitext(given_filename)[0]

                avatar_to_delete = Avatar.query.filter_by(user_id=current_user.id).first()
                if avatar_to_delete:
                    thumb_delete_path = os.path.join(current_app.config['AVATAR_DELETE_PATH'], avatar_to_delete.thumbnail_path)
                    orig_delete_path = os.path.join(current_app.config['AVATAR_DELETE_PATH'],
                                                     avatar_to_delete.original_path)
                    os.remove(thumb_delete_path)
                    os.remove(orig_delete_path)
                    db.session.delete(avatar_to_delete)
                    db.session.flush()
                filename = str(uuid.uuid4()) # assigns a unique name for a file
                orig_path = os.path.join(current_app.config['AVATAR_UPLOAD_PATH'], f'{filename}{file_ext}')
                file.save(orig_path)
                db_orig_path = f'{current_app.config['AVATAR_STATIC_PATH']}{filename}{file_ext}' # static path to write in database
                file_variants = save_image_variants(file, current_app.config['AVATAR_UPLOAD_PATH'], current_app.config['AVATAR_STATIC_PATH'], filename, file_ext)
                avatar = Avatar(user_id=current_user.id, thumbnail_path=file_variants['thumbnail'],
                                original_path=db_orig_path)
                db.session.add(avatar)
                db.session.commit()
                flash(_('Your avatar has been updated!'))
                return redirect(url_for('main.user', username=current_user.username))
    else:
        return render_template('avatar_upload.html', title='Avatar Upload', form=form)

