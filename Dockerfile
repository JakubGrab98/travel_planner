FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /app

CMD ["streamlit", "run", "Home_Page.py"]
