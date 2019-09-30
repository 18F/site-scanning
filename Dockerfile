FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
RUN apt-get update && apt-get install -y jq awscli
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt
COPY . /app/
