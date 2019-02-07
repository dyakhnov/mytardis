FROM python:2.7 AS base

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get install -qy \
        curl \
        git \
		gnupg \
		libldap2-dev \
		libsasl2-dev \
		libssl-dev \
		libxml2-dev \
		libxslt1-dev \
		libmagic-dev \
		libmagickwand-dev \
	&& apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -

RUN apt-get update && apt-get install -qy \
		nodejs \
	&& apt-get clean

RUN pip install --upgrade --no-cache-dir pip

WORKDIR /app

COPY requirements-base.txt ./
# don't install Git repos in 'edit' mode
RUN sed -i 's/-e git+/git+/g' requirements-base.txt
RUN pip install -r requirements-base.txt

COPY requirements-postgres.txt ./
RUN pip install -r requirements-postgres.txt

COPY tardis/apps/social_auth/requirements*.txt ./tardis/apps/social_auth/
RUN pip install -r tardis/apps/social_auth/requirements.txt

RUN git clone https://github.com/wettenhj/mytardis-app-mydata.git ./tardis/apps/mydata/
RUN pip install -r tardis/apps/mydata/requirements.txt

COPY package.json .

RUN npm set progress=false && \
    npm config set depth 0 && \
    npm install

COPY . .
COPY settings.py ./tardis/

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--config", "gunicorn_settings.py", "wsgi:application"]

FROM base AS test

#COPY --from=base . .
RUN pip install -r requirements-mysql.txt
RUN pip install -r requirements-test.txt

RUN mkdir -p var/store

CMD ["cat"]
