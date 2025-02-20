FROM python:3.10-slim

WORKDIR /app

COPY nft_search_web_swarm.py /app/
COPY index.py /app/
COPY trie.py /app/
COPY templates/ /app/templates/
COPY static/ /app/static/

RUN pip install --no-cache-dir flask requests

EXPOSE 5000

ENV FLASK_APP=nft_search_web_swarm.py
ENV FLASK_ENV=development

CMD ["flask", "run", "--host=0.0.0.0"]