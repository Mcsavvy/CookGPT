FROM python:3.7-alpine
COPY . /app
WORKDIR /app
RUN pip install .
RUN cookgpt create-db
RUN cookgpt populate-db
RUN cookgpt add-user -u admin -p admin
EXPOSE 5000
CMD ["cookgpt", "run"]
