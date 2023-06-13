FROM python:3.11-slim
WORKDIR /usr/local/app

COPY *.py .
RUN pip install flask gunicorn -i https://pypi.doubanio.com/simple/

# gunicorn -w 1 -b :5000 main:app
ENTRYPOINT [ "gunicorn", "-w", "1", "main:app" ]
CMD [ "-b", "127.0.0.1:5000" ]
