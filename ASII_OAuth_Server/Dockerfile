FROM python:3

ADD . /oauth_server
WORKDIR /oauth_server

RUN pip install -r requirements.txt
CMD [ "python", "app.py" ]