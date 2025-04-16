from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, LargeBinary

# Инициализация SQLAlchemy
db = SQLAlchemy()

# Модель пользователя
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор пользователя, автоинкрементируемый
    username = db.Column(db.String(80), unique=True, nullable=False)  # Имя пользователя, уникальное и обязательное
    password = db.Column(db.String(128), nullable=False)  # Хранение пароля (в хешированном виде)
    role = db.Column(db.String(20), nullable=False)  # Роль пользователя (admin или client)

# Модель столика
class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор столика
    number = db.Column(db.Integer, nullable=False)  # Номер столика
    capacity = db.Column(db.Integer, nullable=False)  # Вместимость столика
    status = db.Column(db.String(20), nullable=False)  # Статус столика (например, доступен или занят)

    def __repr__(self):
        return f'<Table {self.number}>'  # Представление объекта столика

# Модель бронирования
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор бронирования
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)  # Внешний ключ на столик
    client_name = db.Column(db.String(100), nullable=False)  # Имя клиента, сделавшего бронирование
    reservation_datetime = db.Column(db.DateTime, nullable=False)  # Дата и время бронирования
    number_of_people = db.Column(db.Integer, nullable=False)  # Количество человек
    status = db.Column(db.String(20), nullable=False)  # Статус бронирования (например, подтверждено или отменено)
    table = db.relationship('Table', backref='reservations')  # Связь с моделью Table

# Модель заказа
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор заказа
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)  # Внешний ключ на бронирование
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)  # Внешний ключ на блюдо
    quantity = db.Column(db.Integer, nullable=False)  # Количество заказанного блюда
    reservation = db.relationship('Reservation', backref='orders')  # Связь с моделью Reservation
    dish = db.relationship('Dish', backref='orders')  # Связь с моделью Dish

# Модель блюда
class Dish(db.Model):
    id = Column(Integer, primary_key=True)  # Уникальный идентификатор блюда
    name = Column(String(100), nullable=False)  # Название блюда
    description = Column(String(500), nullable=False)  # Описание блюда
    price = Column(db.Float, nullable=False)  # Цена блюда
    image_data = Column(LargeBinary)  # Данные изображения блюда в бинарном формате
    category = Column(String(100), nullable=False)  # Категория блюда

# Модель отзыва
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор отзыва
    name = db.Column(db.String(100), nullable=False)  # Имя автора отзыва
    email = db.Column(db.String(100), nullable=False)  # Email автора отзыва
    text = db.Column(db.Text, nullable=False)  # Текст отзыва

    def __repr__(self):
        return f'<Review {self.name}>'  # Представление объекта отзыва