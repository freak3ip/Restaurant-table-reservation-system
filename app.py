from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Table, Reservation, User, Order, Dish, Review
from forms import RegisterForm, LoginForm, AddTableForm, BookTableForm, OrderForm, SearchDishForm, AddDishForm
from datetime import datetime
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename  # Импорт для безопасного сохранения файлов
from flask_migrate import Migrate
import os
import base64
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Секретный ключ для сессий
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'  # URI для базы данных
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключение отслеживания изменений
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'timeout': 15  # Увеличение таймаута соединения
    }
}

# Определение пути к папке для загрузок изображений
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'images/images_menu')
# Установка максимального размера загружаемого файла
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
# Настройка разрешенных расширений для загружаемых файлов
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif', '.pdf']

# Инициализация базы данных и миграций
db.init_app(app)
migrate = Migrate(app, db)

# Инициализация менеджера сессий
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Переход на страницу входа при необходимости

# Функция загрузки пользователя по ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return abort(403)  # Доступ запрещён
        return f(*args, **kwargs)
    return decorated_function

# Страница, доступная только для администраторов
@app.route('/admin_only')
@admin_required
def admin_only():
    return render_template('admin_only.html')

# Декоратор для проверки прав менеджера
def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Страница, доступная только для менеджеров
@app.route('/manager_only')
@manager_required
def manager_only():
    return render_template('manager_only.html')

# Фильтр для кодирования данных в base64
@app.template_filter('b64encode')
def b64encode(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

# Страница панели управления
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'manager':
        return render_template('manager_dashboard.html')
    else:
        return render_template('user_dashboard.html')

# Создание таблиц при первом запросе
@app.before_first_request
def create_tables():
    db.create_all()

# Страница для просмотра бронирований
@app.route('/view_reservations')
@login_required
def view_reservations():
    if current_user.role in ['manager', 'admin']:
        reservations = Reservation.query.all()  # Получаем все бронирования
    else:
        # Отображаем только бронирования текущего пользователя
        reservations = Reservation.query.filter_by(client_name=current_user.username).all()
    return render_template('view_reservations.html', reservations=reservations)

# Страница для просмотра блюд
@app.route('/view_dishes', methods=['GET', 'POST'])
@login_required
def view_dishes():
    form = SearchDishForm()  # Создание экземпляра формы поиска
    dishes = Dish.query.all()  # Получаем все блюда
    return render_template('view_dishes.html', dishes=dishes, form=form)

# Страница регистрации нового пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Пользователь с таким именем уже существует.', 'danger')
        else:
            try:
                hashed_pw = generate_password_hash(form.password.data)  # Хеширование пароля
                new_user = User(username=form.username.data, password=hashed_pw, role=form.role.data)
                db.session.add(new_user)  # Добавление нового пользователя в сессию
                db.session.commit()  # Сохранение изменений в базе данных
                flash('Ваш аккаунт был создан! Теперь вы можете войти.', 'success')
                return redirect(url_for('login'))  # Перенаправление на страницу входа
            except Exception as e:
                db.session.rollback()  # Откат транзакции в случае ошибки
                flash('Ошибка при регистрации: ' + str(e), 'danger')
            finally:
                db.session.remove()  # Очистка сессии
    return render_template('register.html', form=form)

# Страница для открытия раздела "О нас"
@app.route('/discover', methods=['GET'])
def discover():
    return render_template('discover.html')

# Глобальная переменная для хранения отзывов
revreviews = []

# API для получения отзывов
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        reviews = Review.query.all()  # Получаем все отзывы из базы данных
        return jsonify([{
            'name': review.name,
            'text': review.text,
            'email': review.email
        } for review in reviews])  # Преобразуем отзывы в список словарей
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Возвращаем ошибку в случае исключения

# Страница для отправки отзыва
@app.route('/submit-review', methods=['POST'])
def submit_review():
    name = request.form.get('name')
    email = request.form.get('email')
    review_text = request.form.get('review')

    # Проверка на уникальность отзыва
    existing_review = Review.query.filter_by(name=name, text=review_text).first()
    if existing_review:
        flash('Вы уже оставили этот отзыв.', 'danger')
        return redirect(url_for('leave_review'))  # Перенаправление на страницу с отзывами

    new_review = Review(name=name, email=email, text=review_text)
    db.session.add(new_review)  # Добавление нового отзыва в сессию
    db.session.commit()  # Сохранение изменений в базе данных

    flash('Ваш отзыв был успешно отправлен!', 'success')
    return redirect(url_for('leave_review'))  # Перенаправление на страницу с отзывами

# Страница для оставления отзыва
@app.route('/leave_review', methods=['GET'])
def leave_review():
    reviews = Review.query.all()  # Получаем все отзывы
    return render_template('leave_review.html', reviews=reviews)

# Страница входа в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):  # Проверка пароля
            login_user(user)  # Вход пользователя
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))  # Перенаправление на главную страницу
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)

# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Выход пользователя
    return redirect(url_for('login'))  # Перенаправление на страницу входа

# Главная страница
@app.route('/')
def index():
    tables = Table.query.all()  # Получаем все столики
    return render_template('index.html', tables=tables)

# Страница для добавления нового столика
@app.route('/add_table', methods=['GET', 'POST'])
@login_required
def add_table():
    form = AddTableForm()
    if form.validate_on_submit():
        try:
            new_table = Table(number=form.number.data, capacity=form.capacity.data, status='available')
            db.session.add(new_table)  # Добавление нового столика в сессию
            db.session.commit()  # Сохранение изменений в базе данных
            flash('Столик успешно добавлен!', 'success')
            return redirect(url_for('view_tables'))  # Перенаправление на страницу со столиками
        except Exception as e:
            db.session.rollback()  # Откат транзакции в случае ошибки
            flash('Ошибка при добавлении столика: ' + str(e), 'danger')
        finally:
            db.session.remove()  # Очистка сессии
    return render_template('add_table.html', form=form)

# Страница для просмотра всех столиков
@app.route('/view_tables')
@login_required
def view_tables():
    tables = Table.query.filter_by(status='available').all()  # Получаем все свободные столики
    return render_template('view_tables.html', tables=tables)

# Страница для бронирования столика
@app.route('/book_table', methods=['GET', 'POST'])
@login_required
def book_table():
    form = BookTableForm()
    tables = Table.query.filter_by(status='available').all()  # Получаем все свободные столики

    # Обновляем выбор столиков, добавляя вместимость в метку
    form.table_id.choices = [(table.id, f"Столик {table.number} (вместимость: {table.capacity})") for table in tables]

    # Проверяем, есть ли у клиента уже активное бронирование
    existing_reservation = Reservation.query.filter_by(client_name=current_user.username, status='confirmed').first()
    if existing_reservation:
        flash('У вас уже есть забронированный столик. Пожалуйста, отмените его, прежде чем делать новое бронирование.', 'danger')
        return redirect(url_for('view_reservations'))  # Перенаправляем на страницу с бронированиями

    if form.validate_on_submit():
        selected_table = Table.query.get(form.table_id.data)

        if form.number_of_people.data > selected_table.capacity:
            flash('Количество человек превышает вместимость выбранного столика.', 'danger')
            return redirect(url_for('book_table'))

        reservation_datetime = form.reservation_datetime.data
        reservation = Reservation(
            table_id=form.table_id.data,
            client_name=current_user.username,
            reservation_datetime=reservation_datetime,
            number_of_people=form.number_of_people.data,
            status='confirmed'
        )
        db.session.add(reservation)  # Добавление новой резервации в сессию
        db.session.commit()  # Сохранение изменений в базе данных

        # Обновляем статус столика на 'reserved'
        selected_table.status = 'reserved'
        db.session.commit()

        # Обработка заказов на блюда
        for dish in Dish.query.all():
            quantity = request.form.get(f'quantity_{dish.id}')
            if quantity and int(quantity) > 0:  # Проверяем, что количество больше 0
                order = Order(reservation_id=reservation.id, dish_id=dish.id, quantity=int(quantity))
                db.session.add(order)  # Добавление заказа в сессию

        db.session.commit()  # Сохраняем заказы
        flash('Стол успешно забронирован и заказы добавлены!', 'success')
        return redirect(url_for('index'))

    return render_template('book_table.html', form=form, dishes=Dish.query.all())

# Страница для добавления нового блюда
@app.route('/add_dish', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def add_dish():
    form = AddDishForm()
    if form.validate_on_submit():
        try:
            # Сохранение изображения в бинарном формате
            image_file = form.image.data
            image_data = image_file.read()  # Читаем содержимое файла

            # Создание объекта Dish и сохранение в базе данных
            new_dish = Dish(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,  # Сохраняем категорию
                image_data=image_data  # Сохраняем бинарные данные изображения
            )
            db.session.add(new_dish)  # Добавление нового блюда в сессию
            db.session.commit()  # Сохранение изменений в базе данных
            flash('Блюдо успешно добавлено!', 'success')
            return redirect(url_for('view_dishes'))  # Перенаправление на страницу со всеми блюдами
        except Exception as e:
            db.session.rollback()  # Откат транзакции в случае ошибки
            flash('Ошибка при добавлении блюда: ' + str(e), 'danger')
        finally:
            db.session.remove()  # Очистка сессии

    return render_template('add_dish.html', form=form)

# Страница для просмотра конкретного блюда
@app.route('/dish/<int:dish_id>')
def view_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)  # Получаем блюдо по ID или 404, если не найдено
    return render_template('view_dish.html', dish=dish)


# Страница для редактирования блюда
@app.route('/edit_dish/<int:dish_id>', methods=['GET', 'POST'])
@login_required
@admin_required  # Доступ только для администраторов
def edit_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)  # Получаем блюдо по ID или 404, если не найдено
    form = AddDishForm(obj=dish)  # Заполняем форму данными существующего блюда
    if form.validate_on_submit():
        dish.name = form.name.data  # Обновляем имя блюда
        dish.description = form.description.data  # Обновляем описание блюда
        dish.price = form.price.data  # Обновляем цену блюда

        if form.image.data:  # Если загружено новое изображение
            image_file = form.image.data
            dish.image_data = image_file.read()  # Обновляем бинарные данные изображения

        db.session.commit()  # Сохраняем изменения в базе данных
        flash('Блюдо успешно обновлено!', 'success')
        return redirect(url_for('view_dishes'))  # Перенаправление на страницу со всеми блюдами

    return render_template('edit_dish.html', form=form, dish=dish)  # Отображаем форму редактирования

# Страница для удаления блюда
@app.route('/delete_dish/<int:dish_id>', methods=['POST'])
def delete_dish(dish_id):
    try:
        dish = Dish.query.get_or_404(dish_id)  # Получаем блюдо по ID или 404, если не найдено
        db.session.delete(dish)  # Удаляем блюдо из сессии
        db.session.commit()  # Сохраняем изменения в базе данных
        flash('Блюдо успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()  # Откат транзакции в случае ошибки
        flash('Ошибка при удалении блюда: ' + str(e), 'danger')
    finally:
        db.session.remove()  # Очистка сессии
    return redirect(url_for('view_dishes'))  # Перенаправление на страницу со всеми блюдами

# Страница для просмотра заказов по резервации
@app.route('/view_orders/<int:reservation_id>')
@login_required
def view_orders(reservation_id):
    orders = Order.query.filter_by(reservation_id=reservation_id).all()  # Получаем все заказы для данной резервации
    reservation = Reservation.query.get(reservation_id)  # Получаем объект Reservation

    # Вычисляем общую сумму заказов
    total_amount = sum(order.quantity * order.dish.price for order in orders)

    return render_template('view_orders.html', orders=orders, reservation=reservation, total_amount=total_amount)

# Страница для отмены заказа
@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)  # Получаем заказ по ID или 404, если не найден
        if order.reservation.client_name != current_user.username:  # Проверка прав пользователя
            flash('Вы не можете отменить этот заказ.', 'danger')
            return redirect(url_for('view_orders', reservation_id=order.reservation_id))

        db.session.delete(order)  # Удаляем заказ
        db.session.commit()  # Сохраняем изменения в базе данных
        flash('Заказ успешно отменен!', 'success')
    except Exception as e:
        db.session.rollback()  # Откат транзакции в случае ошибки
        flash('Ошибка при отмене заказа: ' + str(e), 'danger')
    finally:
        db.session.remove()  # Очистка сессии

    return redirect(url_for('view_orders', reservation_id=order.reservation_id))  # Перенаправление на страницу с заказами

# Страница для отмены бронирования
@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    try:
        reservation = Reservation.query.get_or_404(reservation_id)  # Получаем резервацию по ID или 404, если не найдено
        if reservation.client_name != current_user.username:  # Проверка прав пользователя
            flash('Вы не можете отменить это бронирование.', 'danger')
            return redirect(url_for('view_reservations'))

        # Удаляем все заказы, связанные с этой резервацией
        orders = Order.query.filter_by(reservation_id=reservation.id).all()
        for order in orders:
            db.session.delete(order)  # Удаляем каждый заказ

        # Обновляем статус столика на 'available'
        table = Table.query.get(reservation.table_id)
        table.status = 'available'  # Освобождаем столик

        # Удаляем бронирование
        db.session.delete(reservation)
        db.session.commit()  # Сохраняем изменения в базе данных
        flash('Бронирование успешно отменено!', 'success')
    except Exception as e:
        db.session.rollback()  # Откат транзакции в случае ошибки
        flash('Ошибка при отмене бронирования: ' + str(e), 'danger')
    finally:
        db.session.remove()  # Очистка сессии

    return redirect(url_for('view_reservations'))  # Перенаправление на страницу с бронированиями

if __name__ == '__main__':
    app.run(debug=True)  # Запуск приложения в режиме отладки