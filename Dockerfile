# syntax=docker/dockerfile:1

FROM ubuntu:focal
WORKDIR /src
COPY . .
RUN apt-get update && apt-get install git python3-pip -y && pip install pipenv && make dep
RUN git config --global --add safe.directory /src
EXPOSE 9819
ENV ENV_FOR_DYNACONF=development
CMD pipenv run uvicorn fatcat_scholar.web:app --host 0.0.0.0 --reload --port 9819 

# Build
# docker build -t scholar .

# Run (updating the local src path as needed)
# docker run -p9819:9819 -v/home/vilmibm/src/fatcat-scholar:/src scholar

# Run, using the live search index (updating the local src path as needed)
# docker run --net host -e "ENV_FOR_DYNACONF=development-qa" -v/home/vilmibm/src/fatcat-scholar:/src scholar
