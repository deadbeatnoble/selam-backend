from app.database import SessionLocal
from app.models import Professional


def seed_professionals():
    db = SessionLocal()
    if db.query(Professional).count() > 0:
        db.close()
        return

    professionals = [
        Professional(name="Dr. Selam Tadesse", profession="Psychologist", city="Addis Ababa", phone="+251911000001", email="selam.tadesse@selammind.et", available=True),
        Professional(name="Dr. Abebe Kebede", profession="Psychiatrist", city="Addis Ababa", phone="+251911000002", email="abebe.kebede@selammind.et", available=True),
        Professional(name="Ms. Hanna Girma", profession="Counselor", city="Bahir Dar", phone="+251911000003", email="hanna.girma@selammind.et", available=True),
        Professional(name="Dr. Yonas Haile", profession="Psychologist", city="Hawassa", phone="+251911000004", email="yonas.haile@selammind.et", available=True),
        Professional(name="Dr. Meron Assefa", profession="Psychiatrist", city="Mekelle", phone="+251911000005", email="meron.assefa@selammind.et", available=True),
        Professional(name="Mr. Daniel Worku", profession="Counselor", city="Addis Ababa", phone="+251911000006", email="daniel.worku@selammind.et", available=True),
    ]
    db.add_all(professionals)
    db.commit()
    db.close()
