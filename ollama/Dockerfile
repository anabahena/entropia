FROM ollama/ollama

# Instalar curl para mejorar el healthcheck si fuera necesario
# RUN apt-get update && apt-get install -y curl

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/bin/sh", "/start.sh"]