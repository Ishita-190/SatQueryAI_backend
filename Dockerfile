FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install the API dependencies and the optional CPU inference dependencies.
# requirements-models.txt has an editable reference to ./change_detection_training,
# so copy that package before installing it.
COPY backend/requirements.txt /app/backend/requirements.txt
COPY backend/requirements-models.txt /app/backend/requirements-models.txt
COPY backend/change_detection_training/ /app/backend/change_detection_training/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && cd /app/backend \
    && pip install --no-cache-dir -r requirements-models.txt

COPY backend/app/ /app/backend/app/
COPY backend/checkpoints/fusion_model.pt /app/backend/checkpoints/fusion_model.pt
COPY backend/checkpoints/optical_sar_water.pt /app/backend/checkpoints/optical_sar_water.pt
COPY backend/checkpoints/best_model.pth /app/backend/checkpoints/best_model.pth

WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
