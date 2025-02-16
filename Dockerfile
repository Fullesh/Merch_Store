FROM python:3

WORKDIR /code

COPY ./requirements.txt /code/

RUN pip install -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . .