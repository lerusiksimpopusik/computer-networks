from selenium import webdriver  # Для автоматизации браузера
from selenium.webdriver.common.by import By  # Для поиска элементов по атрибутам
from selenium.webdriver.support.ui import WebDriverWait  # Для ожидания элементов
from selenium.webdriver.support import expected_conditions as EC  # Условия ожидания
from selenium.common.exceptions import TimeoutException, NoSuchElementException  # Обработка ошибок
from fastapi import FastAPI, HTTPException, Depends, Request  # Для создания API
from sqlalchemy.orm import Session, sessionmaker  # Для работы с БД
from sqlalchemy import create_engine, Column, Integer, String, DateTime  # Для моделей БД
from sqlalchemy.ext.declarative import declarative_base  # Базовый класс для моделей
from urllib.parse import unquote  # Для декодирования URL
import re  # Для работы с регулярными выражениями


# Создаем экземпляр FastAPI приложения
app = FastAPI()

# Настройка подключения к базе данных PostgreSQL
DATABASE_URL = "postgresql://postgres:admin@localhost:5432/flats_db"

# SQLAlchemy для работы с БД
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для объявления моделей
Base = declarative_base()


# Модель для хранения данных о квартирах
class Flat(Base):
    """Модель таблицы flats в базе данных."""
    __tablename__ = "flats"  # Имя таблицы в БД

    # Поля таблицы:
    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор
    title = Column(String)  # Заголовок объявления
    price = Column(String)  # Цена (в виде строки, например "30 000 ₽/мес.")
    address = Column(String)  # Адрес объекта
    link = Column(String, unique=True, index=True)  # Ссылка на объявление (уникальная)


# Удаляем существующую таблицу (если есть) и создаем новую
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def get_db():
    """
    Генератор сессий базы данных.
    Обеспечивает корректное закрытие сессии после использования.
    """
    db = SessionLocal()
    try:
        yield db  # Возвращаем сессию для использования
    finally:
        db.close()  # Закрываем сессию в любом случае


def setup_driver():
    """
    Настройка и возврат драйвера Chrome для Selenium.
    Настраивает headless-режим и параметры для обхода защиты.
    """
    options = webdriver.ChromeOptions()
    # Параметры для работы в headless-режиме (без графического интерфейса)
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")  # Необходимо для работы в Docker/сервере
    options.add_argument("--disable-dev-shm-usage")  # Решение проблем с памятью
    options.add_argument("--disable-blink-features=AutomationControlled")  # Скрываем автоматизацию

    # Устанавливаем user-agent обычного браузера
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)  # Максимальное время загрузки страницы
    return driver


def parse_single_page(full_url: str, db: Session):
    """
    Парсит страницу с объявлениями и сохраняет данные в БД.
    Возвращает количество сохраненных объявлений.
    """
    driver = setup_driver()
    parsed_count = 0  # Счетчик успешно сохраненных объявлений

    try:
        print(f"Парсим страницу: {full_url}")
        driver.get(full_url)  # Открываем страницу в браузере

        # Ожидаем появления хотя бы одной карточки объявления
        # Максимальное время ожидания - 20 секунд
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-name='CardComponent']")
            )
        )

        # Находим все карточки объявлений на странице
        flats = driver.find_elements(
            By.CSS_SELECTOR, "[data-name='CardComponent']"
        )

        # Обрабатываем каждое объявление
        for flat in flats:
            try:
                # Извлекаем ссылку на объявление
                link = flat.find_element(
                    By.CSS_SELECTOR, "a[href]"
                ).get_attribute("href")

                # Проверяем, нет ли уже такого объявления в БД
                if db.query(Flat).filter(Flat.link == link).first():
                    continue  # Пропускаем, если объявление уже есть

                # Извлекаем заголовок, цену и адрес
                title = flat.find_element(
                    By.CSS_SELECTOR, "[data-mark='OfferTitle']"
                ).text.strip()  # Удаляем лишние пробелы

                price = flat.find_element(
                    By.CSS_SELECTOR, "[data-mark='MainPrice']"
                ).text.strip()

                address = flat.find_element(
                    By.CSS_SELECTOR, "[data-name='GeoLabel']"
                ).text.strip()

                # Создаем новую запись в БД
                new_flat = Flat(
                    title=title,
                    price=price,
                    address=address,
                    link=link,
                )

                db.add(new_flat)  # Добавляем в сессию
                db.commit()  # Сохраняем в БД
                parsed_count += 1  # Увеличиваем счетчик

            except NoSuchElementException as e:
                # Если не нашли какой-то элемент в карточке
                print(f"Не найдены некоторые элементы: {str(e)}")
                db.rollback()  # Отменяем изменения
                continue  # Переходим к следующему объявлению
            except Exception as e:
                # Любая другая ошибка при обработке объявления
                print(f"Ошибка при сохранении: {str(e)}")
                db.rollback()
                continue

        return parsed_count  # Возвращаем количество сохраненных объявлений

    except TimeoutException:
        # Если страница не загрузилась за отведенное время
        raise HTTPException(
            status_code=408,
            detail="Таймаут при загрузке страницы"
        )
    except Exception as e:
        # Любая другая ошибка при парсинге
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # В любом случае закрываем браузер
        driver.quit()


@app.get("/parse")
async def parse_flat_page(
        request: Request,
        db: Session = Depends(get_db)
):
    """
    API endpoint для парсинга страницы с объявлениями.
    Принимает URL в параметре запроса.
    """
    try:
        # Получаем строку запроса
        query_string = str(request.url.query)

        # Извлекаем URL из параметров запроса
        url_match = re.search(r'url=(.*)', query_string)
        if not url_match:
            raise HTTPException(
                status_code=400,
                detail="Не указан URL"
            )

        # Декодируем URL (на случай если он был закодирован)
        full_url = unquote(url_match.group(1))
        print(f"Получен URL: {full_url}")

        # Проверяем, что это действительно URL cian.ru
        if "cian.ru" not in full_url:
            raise HTTPException(
                status_code=400,
                detail="Поддерживается только парсинг с cian.ru"
            )

        # Запускаем парсинг и получаем количество сохраненных объявлений
        count = parse_single_page(full_url, db)

        # Возвращаем результат
        return {
            "status": "success",
            "parsed_flats": count,
            "url": full_url
        }

    except HTTPException:
        # Пробрасываем HTTP исключения как есть
        raise
    except Exception as e:
        # Все остальные ошибки возвращаем как 500
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get")
async def get_flats(db: Session = Depends(get_db)):
    """
    API endpoint для получения списка всех сохраненных объявлений.
    Возвращает данные в формате JSON.
    """
    # Получаем все объявления из БД, сортируем по ID в обратном порядке
    flats = db.query(Flat).order_by(Flat.id.desc()).all()

    # Формируем ответ в виде списка словарей
    return [{
        "id": flat.id,
        "title": flat.title,
        "price": flat.price,
        "address": flat.address,
        "link": flat.link,
    } for flat in flats]


# Запуск сервера при непосредственном выполнении файла
if __name__ == "__main__":
    import uvicorn

    # Запускаем сервер на всех интерфейсах (0.0.0.0) порту 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)