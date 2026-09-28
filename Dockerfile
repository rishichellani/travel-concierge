FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate.py app.py agent_instructions.md ./
COPY destinations/ ./destinations/

RUN mkdir -p /app/output
VOLUME ["/app/output"]

# Set at `docker run` time, e.g. -e GEMINI_API_KEY=... — never bake it into the image.
ENV GEMINI_API_KEY=""

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
