"""
This is server, run this file when use
"""

# import os
# import traceback
# import random

import sys
import json
import urllib2
from datetime import timedelta
from functools import update_wrapper
from sqlalchemy import create_engine
import psycopg2
from flask import Flask, request, render_template, g, \
    jsonify, make_response, current_app  # , redirect
from werkzeug.security import generate_password_hash, check_password_hash
from Algorithm import UseThread

APP = Flask(__name__)

DATABASEURI = "postgresql://Linnan@localhost:5432/stock"
ENGINE = create_engine(DATABASEURI)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True, automatic_options=True):
    """
        This is function quoted to solve cross domain issue

        Args:
            origin
            methods
            headers
            max_age
            attach_to_all
            automatic_options

        Returns:
            none
        """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """
        return http method if it is not None

        """
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(func):
        """
        return function decorator

        Args:
            func: function that used by request

        """
        def wrapped_function(*args, **kwargs):
            """
            return wrapped function decorator

            Args:
                args
                kwargs

            """
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(func(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            head = resp.headers
            head['Access-Control-Allow-Origin'] = origin
            head['Access-Control-Allow-Methods'] = get_methods()
            head['Access-Control-Max-Age'] = str(max_age)
            head['Access-Control-Allow-Credentials'] = 'true'
            head['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                head['Access-Control-Allow-Headers'] = headers
            return resp

        func.provide_automatic_options = False
        return update_wrapper(wrapped_function, func)

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
    Args:
        exception
    Return:
        none
    """
    try:
        g.conn.close()
    except Exception:
        print exception


@APP.route('/')
def index():
    """
    access the main page

    """
    return render_template("index.html", **locals())


@APP.route("/get_price")
@crossdomain(origin='*')
def get_price():
    """
    handle request of getting time and price

    """
    query = "http://localhost:8080/query?id={}"
    quote = json.loads(urllib2.urlopen(query.format(1.01)).read())
    price = float(quote['top_bid']['price'])
    time_mark = str(quote['timestamp'])
    print "Quoted at {} , time is {} ".format(price, time_mark)
    info = {'time': time_mark, 'price': price}
    return jsonify(rows=info)


@APP.route("/a")
@crossdomain(origin='*')
def handle_a():
    """
    handle request of getting time and price

    """
    try:
        newcurs = g.conn.execute("""SELECT * FROM info ORDER BY id""")
    except Exception as info:
        print "can not read record from database"
        return str(info)

    info = []
    for result in newcurs:
        temp = {'a': result['time_quote'], 'b': result['info'].encode("utf-8")}
        info.insert(0, temp)
    newcurs.close()
    return jsonify(rows=info)


@APP.route("/b")
@crossdomain(origin='*')
def handle_b():
    """
    handle request of getting transaction history

    """
    try:
        newcurs = g.conn.execute("""SELECT * FROM transact ORDER BY id""")
    except Exception as info:
        print "can not read record from database"
        return str(info)

    info = []
    for result in newcurs:
        temp = {'a': result['time_quote'], 'b': result['result'],
                'c': result['price'], 'd': result['size']}
        info.insert(0, temp)
    newcurs.close()
    return jsonify(rows=info)


@APP.route("/submit", methods=['GET'])
@crossdomain(origin='*')
def handle_submit():
    """
    handle request of start an order

    """
    lang = request.args.get('quantity', 0, type=float)
    UseThread(lang).start()
    print lang
    return "1\n"


@APP.route("/register", methods=['POST'])
@crossdomain(origin='*')
def register():
    """
    store information into database when user send register request

    """
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
    except Exception as info:
        conn.rollback()
        print "can not write record to database"
        print str(info)
        return str(info)

    return "1\n"


@APP.route("/del_user", methods=['POST'])
@crossdomain(origin='*')
def del_user():
    """
    delete a user information

    """
    username = request.form['username']
    try:
        conn = psycopg2.connect("dbname='stock' user='Linnan' host='localhost' password='' ")
        cur = conn.cursor()
        query = "DELETE FROM user_info WHERE name='{}';".format(username)
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as info:
        conn.rollback()
        print "can not write record to database"
        print str(info)
        return str(info)
    return "1\n"


@APP.route("/login", methods=['POST'])
@crossdomain(origin='*')
def login():
    """
    verify user information and jump to main page if success

    """
    username = request.form['username']
    password = request.form['password']
    try:
        newcurs = g.conn.execute("""SELECT * FROM user_info WHERE name = '{}'""".format(username))
    except Exception as info:
        print "can not read record from database"
        return str(info)

    for result in newcurs:
        correct = result['pass']
        if check_password_hash(correct, password):
            newcurs.close()
            return "1\n"
    newcurs.close()
    return "2\n"


@APP.route("/strategy", methods=['GET'])
@crossdomain(origin='*')
def strategy():
    """
    show user how the strategy of trading is being calculated

    """
    return "a database need to added"


if __name__ == "__main__":
    # check whether the file is called directly, otherwise do not run
    reload(sys)
    sys.setdefaultencoding('utf8')

    APP.run(debug=False, port=8000)
