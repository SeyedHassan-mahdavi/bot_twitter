from app.models import get_engine, get_session, Tweet, Campaign, City, Meta

engine = get_engine()
session = get_session(engine)

# اول تمام توییت‌ها را پاک کن (وابسته به کمپین و شهر هستند)
session.query(Tweet).delete()
session.query(Campaign).delete()
session.query(City).delete()
session.query(Meta).delete()
session.commit()
print("✅ همه رکوردهای tweets، campaigns و cities پاک شدند!")
