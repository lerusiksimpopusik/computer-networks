from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

app = FastAPI()

# Конфигурация БД
DATABASE_URL = "postgresql://postgres:admin@db:5432/flats_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)


Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/add_url/")
def add_url(url: str, db: Session = Depends(get_db)):
    try:
        # Проверяем существует ли уже URL
        if db.query(URL).filter(URL.url == url).first():
            return {"status": "exists", "url": url}

        new_url = URL(url=url)
        db.add(new_url)
        db.commit()
        return {"status": "added", "url": url}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/get_urls/")  # Изменил путь
def get_urls(db: Session = Depends(get_db)):
    urls = db.query(URL).all()
    return [{"id": url.id, "url": url.url} for url in urls]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)