FROM python:3.7-slim

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "dairies.wsgi:application", "--bind", "0:8000" ]

LABEL author='rock4ts' version=1.1
