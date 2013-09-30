nspire-mixpanel
===============

Automatic Mixpanel Report Generator

Usage
===============

    $ virtualenv venv --distribute
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ echo 'MP_API_KEY=<api_key>' >> .env
    $ echo 'MP_API_SECRET=<api_secret>' >> .env
    $ foreman run python mixpanel.py
