# 📱 bananafingersbot

This telegram bot will help you find the best deals on climbing gear
on [bananafingers.co.uk](https://bananafingers.co.uk).
You select category and the minimum sale percentage and the bot will send you a message with the best deals.

### 📝 Requirements

1. Python 3.10
2. Docker
3. MongoDB
4. Redis

### Setup

1. Clone the repository ```git clone https://github.com/artemkka12/bananafingersbot.git```
2. Install poetry ```pip install poetry```
3. Install dependencies ```poetry install```
4. Install pre-commit hooks ```pre-commit install```

### 🔧 .env

```python
BOT_TOKEN=

CELERY_BROKER_URL=

MONGOENGINE_LINK=

MONGOENGINE_DATABASE=
MONGOENGINE_COLLECTION=
```

### 🚀 Run

```python bot.py```

### Deployment with Docker 🐳

#### Build docker image

``` python
docker-compose build
```

#### Run docker container

``` python
docker-compose up -d
```
