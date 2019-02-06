FROM python:2.7

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

RUN mkdir /tmp/phantomjs && \
    curl -L https://github.com/Medium/phantomjs/releases/download/v2.1.1/phantomjs-2.1.1-linux-x86_64.tar.bz2  | tar -xj --strip-components=1 -C /tmp/phantomjs && \
    cd /tmp/phantomjs && \
    mv bin/phantomjs /usr/local/bin && \
    rm -rf /tmp/*

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -

RUN apt-get update && apt-get install -qy \
		nodejs \
	&& apt-get clean

RUN pip install --upgrade --no-cache-dir pip

RUN pip install pyyaml

RUN mkdir -p /app
RUN mkdir -p /app/var/store

WORKDIR /app

COPY ./ ./
COPY ./settings.py ./tardis

RUN git clone https://github.com/wettenhj/mytardis-app-mydata.git ./tardis/apps/mydata

# don't install Git repos in 'edit' mode
RUN sed -i 's/-e git+/git+/g' requirements-base.txt

RUN pip install -r requirements.txt
RUN pip install -r requirements-postgres.txt
RUN pip install -r requirements-mysql.txt
RUN pip install -r tardis/apps/mydata/requirements.txt

RUN npm install

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--config", "gunicorn_settings.py", "wsgi:application"]
