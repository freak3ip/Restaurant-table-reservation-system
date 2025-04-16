from flask_wtf import FlaskForm
from wtforms import SelectField, PasswordField, StringField, IntegerField, DateTimeField, SubmitField, FloatField, TextAreaField, FileField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileRequired, FileAllowed

# Форма регистрации нового пользователя
class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])  # Поле для имени пользователя
    password = PasswordField('Пароль', validators=[DataRequired()])  # Поле для пароля
    role = SelectField('Роль', choices=[('client', 'Клиент'), ('manager', 'Менеджер'), ('admin', 'Администратор')], validators=[DataRequired()])  # Поле для выбора роли
    submit = SubmitField('Зарегистрироваться')  # Кнопка для отправки формы

# Форма входа пользователя
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])  # Поле для имени пользователя
    password = PasswordField('Пароль', validators=[DataRequired()])  # Поле для пароля
    submit = SubmitField('Войти')  # Кнопка для отправки формы

# Форма для добавления нового столика
class AddTableForm(FlaskForm):
    number = IntegerField('Номер', validators=[DataRequired()])  # Поле для номера столика
    capacity = IntegerField('Вместимость', validators=[DataRequired()])  # Поле для вместимости столика
    submit = SubmitField('Добавить')  # Кнопка для отправки формы

# Форма для добавления заказа на блюдо
class OrderForm(FlaskForm):
    dish_name = StringField('Название блюда', validators=[DataRequired()])  # Поле для названия блюда
    quantity = IntegerField('Количество', validators=[DataRequired()])  # Поле для количества блюда
    submit = SubmitField('Добавить заказ')  # Кнопка для отправки формы

# Форма для поиска блюда
class SearchDishForm(FlaskForm):
    search = StringField('Поиск блюда', validators=[DataRequired()])  # Поле для ввода поискового запроса
    submit = SubmitField('Поиск')  # Кнопка для отправки формы

# Форма для добавления нового блюда
class AddDishForm(FlaskForm):
    name = StringField('Название блюда', validators=[DataRequired()])  # Поле для названия блюда
    description = TextAreaField('Описание', validators=[DataRequired()])  # Поле для описания блюда
    price = FloatField('Цена', validators=[DataRequired()])  # Поле для цены блюда
    category = StringField('Категория', validators=[DataRequired()])  # Поле для категории блюда
    image = FileField('Изображение', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')])  # Поле для загрузки изображения
    submit = SubmitField('Добавить блюдо')  # Кнопка для отправки формы

# Форма для бронирования столика
class BookTableForm(FlaskForm):
    client_name = StringField('Имя клиента', validators=[DataRequired()])  # Поле для имени клиента
    table_id = SelectField('Выберите столик', coerce=int, validators=[DataRequired()])  # Поле для выбора столика
    reservation_datetime = DateTimeField('Дата и время', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])  # Поле для выбора даты и времени бронирования
    number_of_people = IntegerField('Количество человек', validators=[DataRequired()])  # Поле для количества человек
    submit = SubmitField('Забронировать')  # Кнопка для отправки формы