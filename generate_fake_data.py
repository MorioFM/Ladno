"""
Скрипт для генерации фейковых данных для медицинской системы
"""

import sqlite3
from pathlib import Path
from faker import Faker
import random
from datetime import datetime, timedelta

# Инициализация Faker
fake = Faker('ru_RU')

# Путь к базе данных
DB_PATH = Path(__file__).parent / 'medical_clinic.db'


def generate_patients(count: int = 50):
    """Генерация фейковых пациентов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Генерация {count} пациентов...")
    
    for i in range(count):
        gender = random.choice(['М', 'Ж'])
        
        if gender == 'М':
            first_name = fake.first_name_male()
            middle_name = fake.middle_name_male()
        else:
            first_name = fake.first_name_female()
            middle_name = fake.middle_name_female()
        
        patient_data = (
            first_name,
            fake.last_name(),
            middle_name,
            fake.date_of_birth(minimum_age=1, maximum_age=90).strftime('%Y-%m-%d'),
            gender,
            fake.phone_number(),
            fake.email(),
            fake.address().replace('\n', ', '),
            fake.bothify(text='####-####-####-####'),
            random.choice(['O(I)', 'A(II)', 'B(III)', 'AB(IV)']),
            random.choice(['Нет', 'Пенициллин', 'Пыльца', 'Орехи', 'Лактоза', ''])
        )
        
        cursor.execute("""
            INSERT INTO patients (first_name, last_name, middle_name, date_of_birth,
                                gender, phone, email, address, insurance_number,
                                blood_type, allergies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, patient_data)
    
    conn.commit()
    conn.close()
    print(f"✓ Создано {count} пациентов")


def generate_doctors(count: int = 20):
    """Генерация фейковых врачей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем ID специальностей
    cursor.execute("SELECT id FROM specialties")
    specialty_ids = [row[0] for row in cursor.fetchall()]
    
    if not specialty_ids:
        print("⚠ Сначала создайте специальности!")
        conn.close()
        return
    
    print(f"Генерация {count} врачей...")
    
    for i in range(count):
        gender = random.choice(['М', 'Ж'])
        
        if gender == 'М':
            first_name = fake.first_name_male()
            middle_name = fake.middle_name_male()
        else:
            first_name = fake.first_name_female()
            middle_name = fake.middle_name_female()
        
        doctor_data = (
            first_name,
            fake.last_name(),
            middle_name,
            random.choice(specialty_ids),
            fake.phone_number(),
            fake.email(),
            fake.bothify(text='??-########'),
            fake.date_between(start_date='-20y', end_date='today').strftime('%Y-%m-%d')
        )
        
        cursor.execute("""
            INSERT INTO doctors (first_name, last_name, middle_name, specialty_id,
                               phone, email, license_number, hire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, doctor_data)
    
    conn.commit()
    conn.close()
    print(f"✓ Создано {count} врачей")


def generate_appointments(count: int = 100):
    """Генерация фейковых приёмов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем ID пациентов и врачей
    cursor.execute("SELECT id FROM patients")
    patient_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM doctors")
    doctor_ids = [row[0] for row in cursor.fetchall()]
    
    if not patient_ids or not doctor_ids:
        print("⚠ Сначала создайте пациентов и врачей!")
        conn.close()
        return
    
    print(f"Генерация {count} приёмов...")
    
    complaints_list = [
        'Головная боль',
        'Повышенная температура',
        'Боль в горле',
        'Кашель',
        'Боль в животе',
        'Слабость',
        'Головокружение',
        'Боль в спине',
        'Насморк',
        'Профилактический осмотр'
    ]
    
    for i in range(count):
        appointment_data = (
            random.choice(patient_ids),
            random.choice(doctor_ids),
            fake.date_time_between(start_date='-1y', end_date='+30d').strftime('%Y-%m-%d %H:%M:%S'),
            random.choice(['Запланирован', 'Завершён', 'Отменён', 'Не явился']),
            random.choice(complaints_list),
            fake.text(max_nb_chars=200) if random.random() > 0.3 else None
        )
        
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status,
                                    complaints, examination_notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, appointment_data)
    
    conn.commit()
    conn.close()
    print(f"✓ Создано {count} приёмов")


def generate_tests(count: int = 150):
    """Генерация фейковых анализов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем ID завершённых приёмов
    cursor.execute("SELECT id FROM appointments WHERE status = 'Завершён'")
    appointment_ids = [row[0] for row in cursor.fetchall()]
    
    if not appointment_ids:
        print("⚠ Нет завершённых приёмов для создания анализов!")
        conn.close()
        return
    
    print(f"Генерация {count} анализов...")
    
    test_types = [
        ('Общий анализ крови', 'Гематология'),
        ('Биохимический анализ крови', 'Биохимия'),
        ('Общий анализ мочи', 'Урология'),
        ('Анализ на глюкозу', 'Биохимия'),
        ('Анализ на холестерин', 'Биохимия'),
        ('ЭКГ', 'Кардиология'),
        ('Рентген грудной клетки', 'Рентгенология'),
        ('УЗИ брюшной полости', 'УЗИ'),
    ]
    
    for i in range(count):
        test_name, test_type = random.choice(test_types)
        status = random.choice(['Назначен', 'В процессе', 'Готов'])
        
        test_data = (
            random.choice(appointment_ids),
            test_name,
            test_type,
            fake.date_time_between(start_date='-6m', end_date='today').strftime('%Y-%m-%d %H:%M:%S'),
            fake.date_time_between(start_date='-6m', end_date='today').strftime('%Y-%m-%d %H:%M:%S') if status == 'Готов' else None,
            fake.text(max_nb_chars=100) if status == 'Готов' else None,
            'В пределах нормы' if status == 'Готов' else None,
            status,
            fake.text(max_nb_chars=50) if random.random() > 0.7 else None
        )
        
        cursor.execute("""
            INSERT INTO tests (appointment_id, test_name, test_type, ordered_date,
                             completed_date, results, reference_range, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_data)
    
    conn.commit()
    conn.close()
    print(f"✓ Создано {count} анализов")


def generate_prescriptions(count: int = 120):
    """Генерация фейковых назначений"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем ID завершённых приёмов
    cursor.execute("SELECT id FROM appointments WHERE status = 'Завершён'")
    appointment_ids = [row[0] for row in cursor.fetchall()]
    
    if not appointment_ids:
        print("⚠ Нет завершённых приёмов для создания назначений!")
        conn.close()
        return
    
    print(f"Генерация {count} назначений...")
    
    medications = [
        ('Парацетамол', '500 мг', '3 раза в день', '5 дней'),
        ('Ибупрофен', '400 мг', '2 раза в день', '7 дней'),
        ('Амоксициллин', '500 мг', '3 раза в день', '10 дней'),
        ('Лоратадин', '10 мг', '1 раз в день', '14 дней'),
        ('Омепразол', '20 мг', '1 раз в день утром', '30 дней'),
        ('Метформин', '850 мг', '2 раза в день', '90 дней'),
        ('Аспирин', '100 мг', '1 раз в день', '30 дней'),
    ]
    
    for i in range(count):
        medication, dosage, frequency, duration = random.choice(medications)
        start_date = fake.date_between(start_date='-6m', end_date='today')
        
        prescription_data = (
            random.choice(appointment_ids),
            medication,
            dosage,
            frequency,
            duration,
            fake.text(max_nb_chars=100) if random.random() > 0.5 else 'Принимать после еды',
            start_date.strftime('%Y-%m-%d'),
            (start_date + timedelta(days=int(duration.split()[0]))).strftime('%Y-%m-%d')
        )
        
        cursor.execute("""
            INSERT INTO prescriptions (appointment_id, medication_name, dosage, frequency,
                                     duration, instructions, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, prescription_data)
    
    conn.commit()
    conn.close()
    print(f"✓ Создано {count} назначений")


if __name__ == '__main__':
    print("🏥 Генерация фейковых данных для медицинской системы\n")
    
    # Генерируем данные
    generate_patients(50)
    generate_doctors(20)
    generate_appointments(100)
    generate_tests(150)
    generate_prescriptions(120)
    
    print("\n✅ Генерация данных завершена!")
    print("\nСтатистика:")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM patients")
    print(f"  Пациентов: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM doctors")
    print(f"  Врачей: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM appointments")
    print(f"  Приёмов: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM tests")
    print(f"  Анализов: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM prescriptions")
    print(f"  Назначений: {cursor.fetchone()[0]}")
    
    conn.close()
