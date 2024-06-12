import os

from flask import Flask, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import func, Integer, desc
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, ValidationError
from sqlalchemy.orm import joinedload


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rfr;tdsvtyzpft,fkb'


basedir = os.path.abspath(os.path.dirname(__file__))  # получаем из ос раб. директорию для базы
sync_engine = "sqlite:///" + os.path.join(basedir, 'instance', 'my.db')

app = Flask(__name__)  # включаем Фласк
app.config['SQLALCHEMY_DATABASE_URI'] = sync_engine  # указываем ему адрес базы
app.config.from_object(Config)  # передаем в конфиг секретный ключ
db = SQLAlchemy(app)  # подключаем SQLAlchemy
login = LoginManager(app)  # подключаем фласк логины


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # id (номер для записи в таблице. ключевое поле)
    description = db.Column(db.String(30))  # название статьи
    text = db.Column(db.Text)  # текст статьи

    comments = db.relationship('Comments',
                               back_populates='posts')  # связь relationship с таблицей Comment для вывода таблиц
    rating = db.relationship('Rating', back_populates='posts')


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # id (номер для записи в таблице. ключевое поле)
    text = db.Column(db.Text)  # текст комменатрия

    id_post = db.Column(db.Integer, db.ForeignKey('posts.id'))  #связь один ко многим с таблицей Posts
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))  #связь один ко многим с таблицей user

    posts = db.relationship('Posts', back_populates='comments')  # связь relationship с таблицей Posts для вывода таблиц
    user = db.relationship('User', back_populates='comments')


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)

    id_post = db.Column(db.Integer, db.ForeignKey('posts.id'))
    posts = db.relationship('Posts', back_populates='rating')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    comments = db.relationship('Comments', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Function:

    @staticmethod
    def create_tables():  # создаем все таблицы наcледуемые от db
        """Функция удаления и создания всех таблиц"""
        with app.app_context():
            # db.drop_all()
            db.create_all()

    @staticmethod
    def insert_tables_posts(temp_description, temp_text):
        """Функция выбора вставки данных в таблицы post. temp_description - название статьи, temp_text - текст """
        with app.app_context():  # замена сессиям в связки Фласк+Алхимия
            post = Posts(description=temp_description, text=temp_text)
            db.session.add(post)
            db.session.commit()

    @staticmethod
    def insert_tables_rating(temp_rating, temp_id):
        """Функция выбора вставки данных в таблицы rating. temp_rating - рейтинг, temp_id - id статьи """
        with app.app_context():  # замена сессиям в связки Фласк+Алхимия
            rating = Rating(rating=temp_rating, id_post=temp_id)
            db.session.add(rating)
            db.session.commit()

    @staticmethod
    def insert_tables_comments(temp_text, temp_id, temp_user_id):
        """Функция выбора вставки вставки данных в таблицы comments. temp_text - текст комментария, temp_id -
        id статьи, temp_user_id  -id user"""
        with app.app_context():  # замена сессиям в связки Фласк+Алхимия
            comment = Comments(text=temp_text, id_post=temp_id, id_user=temp_user_id)
            db.session.add(comment)
            db.session.commit()

    @staticmethod
    def edit_posts(temp_description, temp_id):
        """Функция выбора вставки таблицы post. temp_description - название статьи, temp_text - текст """
        with app.app_context():  # замена сессиям в связки Фласк+Алхимия
            post = Posts(description=temp_description, id=temp_id)
            db.session.update(post)
            db.session.commit()

    @staticmethod
    def get_post(temp_id):
        """Функция получения поста по id"""
        with app.app_context():
            result = db.session.get(Posts, temp_id)  # для вывода ожного достаточно использовать get
            post = result
            return post

    @staticmethod
    def del_post(temp_id):
        """Функция удаления поста по id"""
        with app.app_context():
            post_to_delete = db.session.get(Posts, temp_id)
            if post_to_delete:
                db.session.delete(post_to_delete)
                db.session.commit()
                return True
            else:
                return False

    @staticmethod
    def get_posts():
        """Функция выгрузки всех клиентов"""
        with app.app_context():
            query = db.select(Posts)  # для выбора всех выбирае всю таблицу целиком
            result = db.session.execute(query)  # экзекьютим/выполняем ее
            posts = result.scalars().all()  # отображаем выбранных клиентво (скаляр для отсеива ненужных скобок)
            return posts

    @staticmethod
    def search_user(username):
        """Функция поиска пользователя в базе по логину. username - логин"""
        with app.app_context():
            query = db.select(User)
            result = db.session.execute(query)
            user = result.scalars().all()
            for i in user:
                if i.username == username:
                    return i

    def get_posts_comment_rating(temp_id):
        with app.app_context():
            post_query = (
                db.session.query(Posts)
                .options(joinedload(Posts.comments), joinedload(Posts.rating))
                .filter(Posts.id == temp_id)
            )
            post = post_query.one_or_none()

            if post:
                comments = post.comments
                ratings = [rating.rating for rating in post.rating]
                average_rating = sum(ratings) / len(ratings) if ratings else None

                return {
                    'post': post,
                    'comments': comments,
                    'average_rating': average_rating
                }
            else:
                return None

    @staticmethod
    def chek_value(username, password):
        """Функция проверки логина и пароля. username -логин, password -пароль"""
        with app.app_context():
            query = db.select(User)
            result = db.session.execute(query)
            user = result.scalars().all()
            for i in user:
                if i.username == username:
                    return User.check_password(i, password)


#
#
class LoginForm(FlaskForm):
    """Класс для полей логин-пароль"""
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """Класс для регистрации пользователей"""
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повтор пароля', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

    def validate_password2(self, field):
        if self.password.data != field.data:
            raise ValidationError('Пароли не совпадают')


class PostForm(FlaskForm):
    """Класс для полей для добавления статьи"""
    # validators=[DataRequired() проверяет не пустой ли поле
    descriptionPost = StringField('Название статьи', validators=[DataRequired()])
    textPost = StringField('Текст статьи', validators=[DataRequired()])
    create_post = SubmitField('Разместить статью')


class CommentForm(FlaskForm):
    """Класс для полей для добавления комментария"""
    # validators=[DataRequired() проверяет не пустой ли поле
    textComment = StringField('Текст комментария', validators=[DataRequired()])
    create_comment = SubmitField('Разместить комментарий')


class RatingForm(FlaskForm):
    """Класс для кнопок для добавления комментария"""
    # validators=[DataRequired() проверяет не пустой ли поле
    example_select = SelectField('Дайте оценку статье. От 1 до 5',
                                 choices=[('val1', '1'), ('val2', '2'), ('val3', '3'), ('val4', '4'), ('val5', '5')])
    create_rating = SubmitField('Разместить оценку')


Function.create_tables()  #создаем таблицы


#
@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])  # Функция обработки входа в админку
def login():
    if current_user.is_authenticated:
        redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        if Function.chek_value(form.username.data, form.password.data) is True:
            flash(f"Добрый день {form.username.data}", "success")
            # Перенаправление на страницу входа или другую страницу
            temp_user = Function.search_user(form.username.data)
            login_user(temp_user, remember=form.remember_me.data)
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))


#     return render_template('login.html', title='Войти', form=form)

@app.route('/logout', methods=['GET'])  # Функция выхода из админки
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/')  # Функция обработки стартовой страницы
def index():
    posts = Function.get_posts()
    return render_template('index.html', posts=posts)
    # return render_template('index.html')


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    comment_form = CommentForm()
    rating_form = RatingForm()

    if comment_form.validate_on_submit():
        comment = Comments(text=comment_form.textComment.data)
        db.session.add(comment)
        db.session.commit()
        flash("Ваш комментарий добавлен!", "success")

    if rating_form.validate_on_submit():
        rating = Rating(rating=rating_form.example_select)
        db.session.add(rating)
        db.session.commit()
        flash("Ваша оценка добавлена!", "success")

    content = Function.get_posts_comment_rating(post_id)
    return render_template('post.html', **content)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)  # Хешируем пароль
        db.session.add(user)
        db.session.commit()
        flash("Вы успешно зарегистрировались!", "success")
        return redirect(url_for('index'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    form = PostForm()

    if form.validate_on_submit():

        post = Posts(description=form.descriptionPost.data, text=form.textPost.data)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('new_post.html', form=form)


@app.route('/<int:post_id>/update_post', methods=['GET', 'POST'])
def update_post(post_id):
    post = Posts.query.get_or_404(post_id)  # Получаем пост или возвращаем 404 ошибку, если пост не найден
    form = PostForm(obj=post)  # Инициализируем форму данными из поста

    if form.validate_on_submit():
        form.populate_obj(post)  # Обновляем объект post данными из формы
        db.session.commit()  # Сохраняем изменения в базе данных
        return redirect(url_for('index'))  # Перенаправляем пользователя на главную страницу
    return render_template('update_post.html', form=form)  # Отображаем форму для редактирования


@app.route('/<int:post_id>')
def delete_post(post_id):
    Function.del_post(post_id)
    return redirect(url_for('index'))


@app.route('/<int:post_id>')
def add_comment(post_id):
    Function.del_post(post_id)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
