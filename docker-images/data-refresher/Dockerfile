FROM python:3.7

ADD code /

RUN pip install -r /requirements.txt
RUN chmod +x /load.py

CMD ["python3", "/load.py"]
