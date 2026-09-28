FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt /app/backend/requirements.txt
COPY requirements-models.txt /app/backend/requirements-models.txt
COPY change_detection_training/ /app/backend/change_detection_training/

RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && cd /app/backend \
    && pip install --no-cache-dir -r requirements-models.txt

COPY app/ /app/backend/app/
COPY checkpoints/fusion_model.pt /app/backend/checkpoints/fusion_model.pt
COPY checkpoints/optical_sar_water.pt /app/backend/checkpoints/optical_sar_water.pt
COPY checkpoints/best_model.pth /app/backend/checkpoints/best_model.pth

WORKDIR /app/backend
EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]