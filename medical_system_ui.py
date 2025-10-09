"""
Медицинская система управления пациентами с использованием NiceGUI
"""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from flet import ui, app
from faker import Faker
import random

# Инициализация Faker для русского языка
fake = Faker('ru_RU')

# Путь к базе данных
DB_PATH = Path(__file__).parent / 'medical_clinic.db'


class MedicalDatabase:
    """Класс для работы с базой данных медицинской клиники"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        """Выполнение SQL запроса"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query: str, params: tuple = ()):
        """Получение всех результатов запроса"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Получение одного результата запроса"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()


# Глобальный экземпляр базы данных
db = MedicalDatabase(DB_PATH)


def generate_fake_patient():
    """Генерация фейковых данных пациента с помощью Faker"""
    gender = random.choice(['М', 'Ж'])
    
    if gender == 'М':
        first_name = fake.first_name_male()
        middle_name = fake.middle_name_male()
    else:
        first_name = fake.first_name_female()
        middle_name = fake.middle_name_female()
    
    patient_data = {
        'first_name': first_name,
        'last_name': fake.last_name(),
        'middle_name': middle_name,
        'date_of_birth': fake.date_of_birth(minimum_age=1, maximum_age=90).strftime('%Y-%m-%d'),
        'gender': gender,
        'phone': fake.phone_number(),
        'email': fake.email(),
        'address': fake.address().replace('\n', ', '),
        'insurance_number': fake.bothify(text='####-####-####-####'),
        'blood_type': random.choice(['O(I)', 'A(II)', 'B(III)', 'AB(IV)']),
        'allergies': random.choice(['Нет', 'Пенициллин', 'Пыльца', 'Орехи', 'Лактоза', ''])
    }
    
    return patient_data


def add_patient(patient_data: dict):
    """Добавление пациента в базу данных"""
    query = """
        INSERT INTO patients (first_name, last_name, middle_name, date_of_birth, 
                            gender, phone, email, address, insurance_number, 
                            blood_type, allergies)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        patient_data['first_name'],
        patient_data['last_name'],
        patient_data['middle_name'],
        patient_data['date_of_birth'],
        patient_data['gender'],
        patient_data['phone'],
        patient_data['email'],
        patient_data['address'],
        patient_data['insurance_number'],
        patient_data['blood_type'],
        patient_data['allergies']
    )
    
    db.execute_query(query, params)


def get_all_patients():
    """Получение всех пациентов"""
    query = """
        SELECT id, first_name, last_name, middle_name, date_of_birth, 
               gender, phone, email, address, insurance_number, 
               blood_type, allergies, created_at
        FROM patients
        ORDER BY last_name, first_name
    """
    return db.fetch_all(query)


def get_patient_by_id(patient_id: int):
    """Получение пациента по ID"""
    query = "SELECT * FROM patients WHERE id = ?"
    return db.fetch_one(query, (patient_id,))


def update_patient(patient_id: int, patient_data: dict):
    """Обновление данных пациента"""
    query = """
        UPDATE patients 
        SET first_name = ?, last_name = ?, middle_name = ?, date_of_birth = ?,
            gender = ?, phone = ?, email = ?, address = ?, insurance_number = ?,
            blood_type = ?, allergies = ?
        WHERE id = ?
    """
    params = (
        patient_data['first_name'],
        patient_data['last_name'],
        patient_data['middle_name'],
        patient_data['date_of_birth'],
        patient_data['gender'],
        patient_data['phone'],
        patient_data['email'],
        patient_data['address'],
        patient_data['insurance_number'],
        patient_data['blood_type'],
        patient_data['allergies'],
        patient_id
    )
    
    db.execute_query(query, params)


def delete_patient(patient_id: int):
    """Удаление пациента"""
    query = "DELETE FROM patients WHERE id = ?"
    db.execute_query(query, (patient_id,))


def get_patient_appointments(patient_id: int):
    """Получение всех приёмов пациента"""
    query = """
        SELECT a.*, d.first_name || ' ' || d.last_name as doctor_name, s.name as specialty
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN specialties s ON d.specialty_id = s.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """
    return db.fetch_all(query, (patient_id,))


# Глобальные переменные для UI
patients_table = None
current_patient_id = None


def refresh_patients_table():
    """Обновление таблицы пациентов"""
    global patients_table
    
    patients = get_all_patients()
    
    rows = []
    for patient in patients:
        rows.append({
            'id': patient['id'],
            'ФИО': f"{patient['last_name']} {patient['first_name']} {patient['middle_name'] or ''}",
            'Дата рождения': patient['date_of_birth'],
            'Пол': patient['gender'],
            'Телефон': patient['phone'],
            'Email': patient['email'],
            'Страховой номер': patient['insurance_number'],
            'Группа крови': patient['blood_type']
        })
    
    patients_table.rows = rows
    patients_table.update()


def show_add_patient_dialog():
    """Диалог добавления нового пациента"""
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        ui.label('Добавить нового пациента').classes('text-2xl font-bold mb-4')
        
        with ui.grid(columns=2).classes('w-full gap-4'):
            last_name_input = ui.input('Фамилия*').classes('w-full')
            first_name_input = ui.input('Имя*').classes('w-full')
            middle_name_input = ui.input('Отчество').classes('w-full')
            dob_input = ui.input('Дата рождения (ГГГГ-ММ-ДД)*').classes('w-full')
            
            gender_select = ui.select(
                ['М', 'Ж'], 
                label='Пол*',
                value='М'
            ).classes('w-full')
            
            phone_input = ui.input('Телефон').classes('w-full')
            email_input = ui.input('Email').classes('w-full')
            insurance_input = ui.input('Страховой номер').classes('w-full')
            
            blood_type_select = ui.select(
                ['O(I)', 'A(II)', 'B(III)', 'AB(IV)'],
                label='Группа крови'
            ).classes('w-full')
            
            allergies_input = ui.input('Аллергии').classes('w-full')
        
        address_input = ui.textarea('Адрес').classes('w-full mt-4')
        
        def generate_fake_data():
            """Заполнение формы фейковыми данными"""
            fake_data = generate_fake_patient()
            last_name_input.value = fake_data['last_name']
            first_name_input.value = fake_data['first_name']
            middle_name_input.value = fake_data['middle_name']
            dob_input.value = fake_data['date_of_birth']
            gender_select.value = fake_data['gender']
            phone_input.value = fake_data['phone']
            email_input.value = fake_data['email']
            address_input.value = fake_data['address']
            insurance_input.value = fake_data['insurance_number']
            blood_type_select.value = fake_data['blood_type']
            allergies_input.value = fake_data['allergies']
        
        def save_patient():
            """Сохранение пациента"""
            if not last_name_input.value or not first_name_input.value or not dob_input.value:
                ui.notify('Заполните обязательные поля!', type='negative')
                return
            
            patient_data = {
                'first_name': first_name_input.value,
                'last_name': last_name_input.value,
                'middle_name': middle_name_input.value,
                'date_of_birth': dob_input.value,
                'gender': gender_select.value,
                'phone': phone_input.value,
                'email': email_input.value,
                'address': address_input.value,
                'insurance_number': insurance_input.value,
                'blood_type': blood_type_select.value,
                'allergies': allergies_input.value
            }
            
            try:
                add_patient(patient_data)
                ui.notify('Пациент успешно добавлен!', type='positive')
                refresh_patients_table()
                dialog.close()
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')
        
        with ui.row().classes('w-full justify-between mt-4'):
            ui.button('Сгенерировать данные', on_click=generate_fake_data).props('outline color=secondary')
            with ui.row():
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Сохранить', on_click=save_patient).props('color=primary')
    
    dialog.open()


def show_patient_details(patient_id: int):
    """Показать детали пациента"""
    patient = get_patient_by_id(patient_id)
    
    if not patient:
        ui.notify('Пациент не найден', type='negative')
        return
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl'):
        ui.label(f"Карта пациента #{patient['id']}").classes('text-2xl font-bold mb-4')
        
        with ui.tabs().classes('w-full') as tabs:
            tab_info = ui.tab('Личные данные')
            tab_history = ui.tab('История приёмов')
        
        with ui.tab_panels(tabs, value=tab_info).classes('w-full'):
            with ui.tab_panel(tab_info):
                with ui.grid(columns=2).classes('w-full gap-4'):
                    ui.label(f"ФИО: {patient['last_name']} {patient['first_name']} {patient['middle_name'] or ''}").classes('col-span-2 text-lg font-semibold')
                    ui.label(f"Дата рождения: {patient['date_of_birth']}")
                    ui.label(f"Пол: {patient['gender']}")
                    ui.label(f"Телефон: {patient['phone'] or 'Не указан'}")
                    ui.label(f"Email: {patient['email'] or 'Не указан'}")
                    ui.label(f"Страховой номер: {patient['insurance_number'] or 'Не указан'}").classes('col-span-2')
                    ui.label(f"Группа крови: {patient['blood_type'] or 'Не указана'}")
                    ui.label(f"Аллергии: {patient['allergies'] or 'Нет'}")
                    ui.label(f"Адрес: {patient['address'] or 'Не указан'}").classes('col-span-2')
            
            with ui.tab_panel(tab_history):
                appointments = get_patient_appointments(patient['id'])
                
                if appointments:
                    for apt in appointments:
                        with ui.card().classes('w-full mb-2'):
                            ui.label(f"Дата: {apt['appointment_date']}").classes('font-bold')
                            ui.label(f"Врач: {apt['doctor_name']} ({apt['specialty']})")
                            ui.label(f"Статус: {apt['status']}")
                            if apt['complaints']:
                                ui.label(f"Жалобы: {apt['complaints']}")
                            if apt['examination_notes']:
                                ui.label(f"Заметки: {apt['examination_notes']}")
                else:
                    ui.label('История приёмов пуста').classes('text-gray-500')
        
        ui.button('Закрыть', on_click=dialog.close).classes('mt-4')
    
    dialog.open()


@ui.page('/')
def main_page():
    """Главная страница приложения"""
    global patients_table
    
    # Подключение к базе данных
    db.connect()
    
    ui.colors(primary='#1976D2', secondary='#26A69A', accent='#9C27B0')
    
    with ui.header().classes('items-center justify-between bg-primary text-white'):
        ui.label('🏥 Медицинская информационная система').classes('text-2xl font-bold')
        ui.label('Поликлиника').classes('text-sm')
    
    with ui.left_drawer(bordered=True).classes('bg-gray-100'):
        ui.label('Меню').classes('text-xl font-bold p-4')
        with ui.column().classes('w-full'):
            ui.button('📋 Пациенты', on_click=lambda: None).props('flat align=left').classes('w-full')
            ui.button('👨‍⚕️ Врачи', on_click=lambda: ui.notify('В разработке')).props('flat align=left').classes('w-full')
            ui.button('📅 Приёмы', on_click=lambda: ui.notify('В разработке')).props('flat align=left').classes('w-full')
            ui.button('🧪 Анализы', on_click=lambda: ui.notify('В разработке')).props('flat align=left').classes('w-full')
            ui.button('💊 Назначения', on_click=lambda: ui.notify('В разработке')).props('flat align=left').classes('w-full')
    
    with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
        ui.button(icon='add', on_click=show_add_patient_dialog).props('fab color=primary').tooltip('Добавить пациента')
    
    with ui.column().classes('w-full p-4'):
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label('Список пациентов').classes('text-3xl font-bold')
            with ui.row():
                ui.button('Обновить', icon='refresh', on_click=refresh_patients_table).props('outline')
                ui.button('Добавить пациента', icon='person_add', on_click=show_add_patient_dialog).props('color=primary')
        
        # Таблица пациентов
        patients_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                {'name': 'ФИО', 'label': 'ФИО', 'field': 'ФИО', 'align': 'left'},
                {'name': 'Дата рождения', 'label': 'Дата рождения', 'field': 'Дата рождения', 'align': 'left'},
                {'name': 'Пол', 'label': 'Пол', 'field': 'Пол', 'align': 'center'},
                {'name': 'Телефон', 'label': 'Телефон', 'field': 'Телефон', 'align': 'left'},
                {'name': 'Email', 'label': 'Email', 'field': 'Email', 'align': 'left'},
                {'name': 'Страховой номер', 'label': 'Страховой номер', 'field': 'Страховой номер', 'align': 'left'},
                {'name': 'Группа крови', 'label': 'Группа крови', 'field': 'Группа крови', 'align': 'center'},
            ],
            rows=[],
            row_key='id',
            pagination={'rowsPerPage': 10, 'sortBy': 'ФИО'}
        ).classes('w-full')
        
        patients_table.add_slot('body-cell-id', '''
            <q-td :props="props">
                <q-btn flat dense color="primary" :label="props.value" @click="$parent.$emit('row_click', props.row)" />
            </q-td>
        ''')
        
        patients_table.on('row_click', lambda e: show_patient_details(e.args['id']))
        
        # Загрузка данных
        refresh_patients_table()


if __name__ in {'__main__', '__mp_main__'}:
    # Запуск приложения
    ui.run(
        title='Медицинская информационная система',
        port=8080,
        reload=False,
        show=True
    )
