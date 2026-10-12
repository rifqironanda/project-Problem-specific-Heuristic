FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml requirements.lock ./
COPY psh ./psh
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-deps .
COPY app.py ./
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000 8501
CMD ["python", "-m", "uvicorn", "psh.api:app", "--host", "0.0.0.0", "--port", "8000"]
