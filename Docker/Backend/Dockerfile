FROM python:3.12-slim

COPY ./tools/ .
RUN chmod +x /setup.sh

WORKDIR /backend

ENTRYPOINT [ "bash", "/setup.sh" ]