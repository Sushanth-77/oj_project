From python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++

RUN pip install django

COPY . /app/

CMD ["python", "manage.py", "runserver", "0.0.0:8000"]