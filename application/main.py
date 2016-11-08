"""
This is server, run this file when use
"""

# import os
# import traceback
# import random

import sys
import json
import urllib2
from sqlalchemy import create_engine
import psycopg2
from flask import Flask, request, render_template, g, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from Algorithm import UseThread
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

BASE = 0.0
APP = Flask(__name__)

DATABASEURI = "postgresql://Linnan@localhost:5432/stock"
ENGINE = create_engine(DATABASEURI)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True, automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


@APP.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = ENGINE.connect()
    except Exception:
        print "uh oh, problem connecting to database"
        # traceback.print_exc()
        g.conn = None


@APP.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception:
        print exception


@APP.route('/')
def index():
    """
    access the main page
    :return:
    """
    return render_template("index.html", **locals())


@APP.route("/get_price")
@crossdomain(origin='*')
def get_price():
    QUERY = "http://localhost:8080/query?id={}"
    quote = json.loads(urllib2.urlopen(QUERY.format(1.01)).read())
    price = float(quote['top_bid']['price'])
    time_mark = str(quote['timestamp'])
    print "Quoted at {} , time is {} ".format(price, time_mark)
    info = {'time': time_mark, 'price': price}
    return jsonify(rows=info)


@APP.route("/a")
@crossdomain(origin='*')
def handle_a():
    try:
        newcurs = g.conn.execute("""SELECT * FROM info ORDER BY id""")
    except Exception as e:
        print "can not read record from database"
        return str(e)

    info = []
    for result in newcurs:
        temp = {'a': result['time_quote'], 'b': result['info'].encode("utf-8")}
        info.insert(0, temp)
    newcurs.close()
    return jsonify(rows=info)


@APP.route("/b")
@crossdomain(origin='*')
def handle_b():
    try:
        newcurs = g.conn.execute("""SELECT * FROM transact ORDER BY id""")
    except Exception as e:
        print "can not read record from database"
        return str(e)

    info = []
    for result in newcurs:
        temp = {'a': result['time_quote'], 'b': result['result'], 'c': result['price'], 'd': result['size']}
        info.insert(0, temp)
    newcurs.close()
    return jsonify(rows=info)


@APP.route("/submit", methods=['GET'])
@crossdomain(origin='*')
def handle_submit():
    global BASE
    lang = request.args.get('quantity', 0, type=float)
    UseThread(lang).start()
    print lang
    BASE = float(lang)
    return "1\n"


@APP.route("/register", methods=['POST'])
@crossdomain(origin='*')
def register():
    username = request.form['username']
    password = request.form['password']
    pw_hash = generate_password_hash(password)
    try:
        conn = psycopg2.connect("dbname='stock' user='Linnan' host='localhost' password='' ")
        cur = conn.cursor()
        query = "INSERT INTO user_info (name, pass) VALUES ('{}', '{}');".format(username, pw_hash)
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        conn.rollback()
        print "can not write record to database"
        print str(e)
        return str(e)

    return "1\n"


@APP.route("/login", methods=['POST'])
@crossdomain(origin='*')
def login():
    username = request.form['username']
    password = request.form['password']
    try:
        newcurs = g.conn.execute("""SELECT * FROM user_info WHERE name = '{}'""".format(username))
    except Exception as e:
        print "can not read record from database"
        return str(e)

    for result in newcurs:
        correct = result['pass']
        print correct
        if check_password_hash(correct, password):
            newcurs.close()
            return "1\n"
    newcurs.close()
    return "2\n"


@APP.route("/strategy", methods=['GET'])
@crossdomain(origin='*')
def strategy():
    global BASE
    print BASE
    if BASE == 0:
        return "Waiting to Start !"
    elif BASE > 0:
        return "We will sperated your $ %s order evenly into 100 each and sell them every 5 second" % BASE
    else:
        "Please try positive input !"


if __name__ == "__main__":
    # check whether the file is called directly, otherwise do not run
    reload(sys)
    sys.setdefaultencoding('utf8')

    APP.run(debug=True, port=8000)
