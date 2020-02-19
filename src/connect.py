#!/usr/bin/python3
import psycopg2
import sys


def connect():
    try:
        conn = psycopg2.connect("host='localhost' dbname='coffee'" +
                                "user='coffeeadmin' password='password'")
        # print("connected to database")
        return conn

    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e)
        sys.exit(1)
