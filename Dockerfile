FROM python:3.11-slim
WORKDIR /usr/local/app

COPY *.py .
RUN pip install flask gunicorn -i https://pypi.doubanio.com/simple/ && \
     apt update && apt install git

## TODO: hugo & mdbook

# gunicorn -w 1 -b :5000 main:app
ENTRYPOINT [ "gunicorn", "-w", "1", "-b", ":5000", "main:app" ]
