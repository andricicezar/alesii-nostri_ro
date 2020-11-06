from flask import g
import os
import mysql.connector

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST'),
            user=os.environ.get('MYSQL_USER'),
            passwd=os.environ.get('MYSQL_PASSWORD'),
            database=os.environ.get('MYSQL_DATABASE')
        )

    return g.db

def get_cursor():
    return get_db().cursor()

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def query(q, args=None):
    cur = get_cursor()
    cur.execute(q, args)
    result = cur.fetchall()
    cur.close()
    return result

def init_app(app):
    app.teardown_appcontext(close_db)
