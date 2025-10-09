"""
Медицинская система управления пациентами с использованием Flet
"""

import sqlite3
from datetime import datetime, date
from pathlib import Path
import flet as ft
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
    
    def initialize_database(self):
        """Создание таблиц базы данных, если они не существуют"""
        schema = """
        -- Таблица специальностей врачей
        CREATE TABLE IF NOT EXISTS specialties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Таблица врачей
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            specialty_id INTEGER NOT NULL,
            phone TEXT,
            email TEXT,
            license_number TEXT UNIQUE,
            hire_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (specialty_id) REFERENCES specialties(id)
        );

        -- Таблица пациентов
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            date_of_birth DATE NOT NULL,
            gender TEXT CHECK(gender IN ('М', 'Ж')),
            phone TEXT,
            email TEXT,
            address TEXT,
            insurance_number TEXT UNIQUE,
            blood_type TEXT,
            allergies TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Таблица приёмов
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TIMESTAMP NOT NULL,
            status TEXT CHECK(status IN ('Запланирован', 'Завершён', 'Отменён', 'Не явился')) DEFAULT 'Запланирован',
            complaints TEXT,
            examination_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        -- Таблица диагнозов
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            icd_code TEXT,
            diagnosis_name TEXT NOT NULL,
            diagnosis_type TEXT CHECK(diagnosis_type IN ('Основной', 'Сопутствующий', 'Осложнение')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );

        -- Таблица анализов
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            test_type TEXT,
            ordered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_date TIMESTAMP,
            results TEXT,
            reference_range TEXT,
            status TEXT CHECK(status IN ('Назначен', 'В процессе', 'Готов')) DEFAULT 'Назначен',
            notes TEXT,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );

        -- Таблица назначений (лечение)
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            medication_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            duration TEXT,
            instructions TEXT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX IF NOT EXISTS idx_patients_last_name ON patients(last_name);
        CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
        CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
        CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
        CREATE INDEX IF NOT EXISTS idx_tests_appointment ON tests(appointment_id);
        CREATE INDEX IF NOT EXISTS idx_diagnoses_appointment ON diagnoses(appointment_id);
        CREATE INDEX IF NOT EXISTS idx_prescriptions_appointment ON prescriptions(appointment_id);
        """
        
        cursor = self.conn.cursor()
        cursor.executescript(schema)
        self.conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM specialties")
        if cursor.fetchone()[0] == 0:
            initial_specialties = [
                ('Терапевт', 'Врач общей практики'),
                ('Кардиолог', 'Специалист по сердечно-сосудистым заболеваниям'),
                ('Невролог', 'Специалист по нервной системе'),
                ('Педиатр', 'Детский врач'),
                ('Хирург', 'Специалист по хирургическим операциям'),
                ('Офтальмолог', 'Специалист по глазным заболеваниям'),
                ('ЛОР', 'Специалист по ухо-горло-носу'),
                ('Дерматолог', 'Специалист по кожным заболеваниям'),
                ('Эндокринолог', 'Специалист по эндокринной системе'),
                ('Гастроэнтеролог', 'Специалист по пищеварительной системе')
            ]
            cursor.executemany(
                "INSERT INTO specialties (name, description) VALUES (?, ?)",
                initial_specialties
            )
            self.conn.commit()
    
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


def main(page: ft.Page):
    """Главная функция приложения"""
    
    # Настройка страницы
    page.title = "Медицинская информационная система"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1400
    page.window_height = 900
    
    db.connect()
    db.initialize_database()
    
    # Переменные для хранения данных
    patients_data = []
    
    def load_patients():
        """Загрузка списка пациентов"""
        nonlocal patients_data
        patients_data = get_all_patients()
        update_patients_table()
    
    def update_patients_table():
        """Обновление таблицы пациентов"""
        patients_table.rows.clear()
        
        for patient in patients_data:
            full_name = f"{patient['last_name']} {patient['first_name']} {patient['middle_name'] or ''}"
            
            patients_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(patient['id']))),
                        ft.DataCell(ft.Text(full_name)),
                        ft.DataCell(ft.Text(patient['date_of_birth'])),
                        ft.DataCell(ft.Text(patient['gender'])),
                        ft.DataCell(ft.Text(patient['phone'] or '')),
                        ft.DataCell(ft.Text(patient['email'] or '')),
                        ft.DataCell(ft.Text(patient['insurance_number'] or '')),
                        ft.DataCell(ft.Text(patient['blood_type'] or '')),
                    ],
                    on_select_changed=lambda e, pid=patient['id']: show_patient_details(pid)
                )
            )
        
        page.update()
    
    def show_add_patient_dialog(e):
        """Диалог добавления нового пациента"""
        
        # Поля ввода
        last_name_field = ft.TextField(label="Фамилия*", width=300)
        first_name_field = ft.TextField(label="Имя*", width=300)
        middle_name_field = ft.TextField(label="Отчество", width=300)
        dob_field = ft.TextField(label="Дата рождения (ГГГГ-ММ-ДД)*", width=300)
        gender_dropdown = ft.Dropdown(
            label="Пол*",
            width=300,
            options=[
                ft.dropdown.Option("М"),
                ft.dropdown.Option("Ж"),
            ],
            value="М"
        )
        phone_field = ft.TextField(label="Телефон", width=300)
        email_field = ft.TextField(label="Email", width=300)
        insurance_field = ft.TextField(label="Страховой номер", width=300)
        blood_type_dropdown = ft.Dropdown(
            label="Группа крови",
            width=300,
            options=[
                ft.dropdown.Option("O(I)"),
                ft.dropdown.Option("A(II)"),
                ft.dropdown.Option("B(III)"),
                ft.dropdown.Option("AB(IV)"),
            ]
        )
        allergies_field = ft.TextField(label="Аллергии", width=300)
        address_field = ft.TextField(label="Адрес", width=620, multiline=True, min_lines=2, max_lines=3)
        
        def generate_fake_data(e):
            """Заполнение формы фейковыми данными"""
            fake_data = generate_fake_patient()
            last_name_field.value = fake_data['last_name']
            first_name_field.value = fake_data['first_name']
            middle_name_field.value = fake_data['middle_name']
            dob_field.value = fake_data['date_of_birth']
            gender_dropdown.value = fake_data['gender']
            phone_field.value = fake_data['phone']
            email_field.value = fake_data['email']
            address_field.value = fake_data['address']
            insurance_field.value = fake_data['insurance_number']
            blood_type_dropdown.value = fake_data['blood_type']
            allergies_field.value = fake_data['allergies']
            page.update()
        
        def save_patient(e):
            """Сохранение пациента"""
            if not last_name_field.value or not first_name_field.value or not dob_field.value:
                page.snack_bar = ft.SnackBar(ft.Text("Заполните обязательные поля!"), bgcolor=ft.Colors.RED_400)
                page.snack_bar.open = True
                page.update()
                return
            
            patient_data = {
                'first_name': first_name_field.value,
                'last_name': last_name_field.value,
                'middle_name': middle_name_field.value,
                'date_of_birth': dob_field.value,
                'gender': gender_dropdown.value,
                'phone': phone_field.value,
                'email': email_field.value,
                'address': address_field.value,
                'insurance_number': insurance_field.value,
                'blood_type': blood_type_dropdown.value,
                'allergies': allergies_field.value
            }
            
            try:
                add_patient(patient_data)
                page.snack_bar = ft.SnackBar(ft.Text("Пациент успешно добавлен!"), bgcolor=ft.Colors.GREEN_400)
                page.snack_bar.open = True
                load_patients()
                dialog.open = False
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"), bgcolor=ft.Colors.RED_400)
                page.snack_bar.open = True
                page.update()
        
        def close_dialog(e):
            dialog.open = False
            page.update()
        
        # Создание диалога
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Добавить нового пациента", size=24, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([last_name_field, first_name_field]),
                        ft.Row([middle_name_field, dob_field]),
                        ft.Row([gender_dropdown, phone_field]),
                        ft.Row([email_field, insurance_field]),
                        ft.Row([blood_type_dropdown, allergies_field]),
                        address_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=650,
                height=500,
            ),
            actions=[
                ft.TextButton("Сгенерировать данные", on_click=generate_fake_data),
                ft.TextButton("Отмена", on_click=close_dialog),
                ft.ElevatedButton("Сохранить", on_click=save_patient),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def show_patient_details(patient_id: int):
        """Показать детали пациента"""
        patient = get_patient_by_id(patient_id)
        
        if not patient:
            page.snack_bar = ft.SnackBar(ft.Text("Пациент не найден"), bgcolor=ft.Colors.RED_400)
            page.snack_bar.open = True
            page.update()
            return
        
        # Вкладка с личными данными
        info_tab = ft.Column(
            [
                ft.Text(f"ФИО: {patient['last_name']} {patient['first_name']} {patient['middle_name'] or ''}", 
                       size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Дата рождения: {patient['date_of_birth']}"),
                ft.Text(f"Пол: {patient['gender']}"),
                ft.Text(f"Телефон: {patient['phone'] or 'Не указан'}"),
                ft.Text(f"Email: {patient['email'] or 'Не указан'}"),
                ft.Text(f"Страховой номер: {patient['insurance_number'] or 'Не указан'}"),
                ft.Text(f"Группа крови: {patient['blood_type'] or 'Не указана'}"),
                ft.Text(f"Аллергии: {patient['allergies'] or 'Нет'}"),
                ft.Text(f"Адрес: {patient['address'] or 'Не указан'}"),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Вкладка с историей приёмов
        appointments = get_patient_appointments(patient['id'])
        
        if appointments:
            appointments_list = []
            for apt in appointments:
                appointments_list.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"Дата: {apt['appointment_date']}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"Врач: {apt['doctor_name']} ({apt['specialty']})"),
                            ft.Text(f"Статус: {apt['status']}"),
                            ft.Text(f"Жалобы: {apt['complaints']}") if apt['complaints'] else ft.Container(),
                            ft.Text(f"Заметки: {apt['examination_notes']}") if apt['examination_notes'] else ft.Container(),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_400),
                        border_radius=5,
                        margin=ft.margin.only(bottom=10),
                    )
                )
            history_tab = ft.Column(appointments_list, scroll=ft.ScrollMode.AUTO)
        else:
            history_tab = ft.Text("История приёмов пуста", color=ft.Colors.GREY_500)
        
        # Создание вкладок
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Личные данные", content=ft.Container(content=info_tab, padding=20)),
                ft.Tab(text="История приёмов", content=ft.Container(content=history_tab, padding=20)),
            ],
            expand=1,
        )
        
        def close_dialog(e):
            dialog.open = False
            page.update()
        
        # Создание диалога
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Карта пациента #{patient['id']}", size=24, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=tabs,
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=close_dialog),
            ],
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Создание таблицы пациентов
    patients_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("ФИО")),
            ft.DataColumn(ft.Text("Дата рождения")),
            ft.DataColumn(ft.Text("Пол")),
            ft.DataColumn(ft.Text("Телефон")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Страховой номер")),
            ft.DataColumn(ft.Text("Группа крови")),
        ],
        rows=[],
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=5,
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        heading_row_color=ft.Colors.BLUE_50,
        heading_row_height=50,
        data_row_min_height=45,
    )
    
    # Основной контент
    content = ft.Column(
        [
            # Заголовок
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.LOCAL_HOSPITAL, size=40, color=ft.Colors.WHITE),
                        ft.Text("Медицинская информационная система", 
                               size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                bgcolor=ft.Colors.BLUE_700,
                padding=20,
            ),
            
            # Панель управления
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text("Список пациентов", size=24, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    tooltip="Обновить",
                                    on_click=lambda e: load_patients(),
                                ),
                                ft.ElevatedButton(
                                    "Добавить пациента",
                                    icon=ft.Icons.PERSON_ADD,
                                    on_click=show_add_patient_dialog,
                                ),
                            ]
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=20,
            ),
            
            # Таблица пациентов
            ft.Container(
                content=ft.Column(
                    [patients_table],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=ft.padding.only(left=20, right=20, bottom=20),
                expand=True,
            ),
        ],
        expand=True,
    )
    
    # Добавление контента на страницу
    page.add(content)
    
    # Загрузка данных
    load_patients()


if __name__ == '__main__':
    ft.app(target=main)
