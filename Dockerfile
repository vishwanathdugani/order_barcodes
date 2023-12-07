FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONPATH /app:$PYTHONPATH
ENV DATABASE_URL "sqlite:///./tiqets.db"
ENV TEST_DATABASE_URL "sqlite:///./tests/test_tiqets.db"
CMD ["python", "main.py"]
