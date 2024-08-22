import psycopg2
from faker import Faker

conn = psycopg2.connect(
    dbname="irmtestdb", user="postgres", password="hXEXiNCbCs", host="127.0.0.1", port="5441"
)
cursor = conn.cursor()

fake = Faker()

for _ in range(100000):
    cursor.execute("INSERT INTO teacher (name) VALUES (%s) RETURNING id", (fake.name(),))
    teacher_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO student (teacher_id, student_name, course) VALUES (%s, %s, %s)",
        (teacher_id, fake.name(), fake.text()),
    )
conn.commit()
cursor.close()
conn.close()

