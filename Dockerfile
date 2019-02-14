FROM ubuntu:18.04 AS base

# Upgrade OS and install packages
RUN apt-get update -yqq && \
    apt-get install -yqq --no-install-recommends \
        build-essential \
        curl \
        git \
        gnupg \
        libfreetype6-dev \
        libjpeg-dev \
        libldap2-dev \
        libmagic-dev \
        libmagickwand-dev \
        libsasl2-dev \
        libssl-dev \
        libxml2-dev \
        libxslt1-dev \
        python-dev \
        python-pip \
        python-setuptools \
        zlib1g-dev \
        unzip \
        mc \
        ncdu && \
	rm -rf /var/lib/apt/lists/*

# Install NodeJS
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get update -yqq && \
    apt-get install -yqq --no-install-recommends \
        nodejs && \
	rm -rf /var/lib/apt/lists/*

# Upgrade PIP
RUN pip install --upgrade --no-cache-dir pip

FROM base AS builder

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

COPY requirements-base.txt ./
# don't install Git repos in 'edit' mode
RUN sed -i 's/-e git+/git+/g' requirements-base.txt
RUN pip install -q -r requirements-base.txt

COPY requirements-postgres.txt ./
RUN pip install -q -r requirements-postgres.txt

COPY tardis/apps/social_auth/requirements*.txt ./tardis/apps/social_auth/
RUN pip install -q -r tardis/apps/social_auth/requirements.txt

#RUN git clone https://github.com/wettenhj/mytardis-app-mydata.git ./tardis/apps/mydata/
#RUN pip install -r tardis/apps/mydata/requirements.txt

COPY package.json .

RUN npm set progress=false && \
    npm config set depth 0 && \
    npm install --production

# Remove build junk
RUN apt-get purge -yqq \
        python3 \
        git && \
    apt-get autoremove -y

COPY . .
COPY settings.py ./tardis/

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--config", "gunicorn_settings.py", "wsgi:application"]

FROM builder AS test

# Remove production settings
RUN rm -f ./tardis/settings.py

# Install Chrome WebDriver
RUN CHROMEDRIVER_VERSION=`curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    mkdir -p /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    curl -sS -o /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip -qq /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver && \
    ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver /usr/local/bin/chromedriver

# Install Google Chrome
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    apt-get clean

# Install PhantomJS
RUN PHANTOMJS_CDNURL=https://npm.taobao.org/mirrors/phantomjs/ npm install phantomjs-prebuilt

# Install packages for testing
RUN apt-get update -yqq && \
    apt-get install -yqq --no-install-recommends \
        libmysqlclient-dev \
        libmysqlclient20 && \
    apt-get clean

# Install MySQL packages
COPY requirements-mysql.txt ./
RUN pip install -q -r requirements-mysql.txt

# Install test packages
COPY requirements-test.txt ./
RUN pip install -q -r requirements-test.txt

# Install NodeJS packages
RUN npm install

# Create default storage
RUN mkdir -p var/store

CMD ["cat"]
