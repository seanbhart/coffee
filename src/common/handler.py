import psycopg2
from .. import connect


# Setup the coffee database
def sql(sql_string):
    connector = connect.connect()
    cursor = connector.cursor()
    try:
        # execute SQL
        cursor.execute(sql_string)
        connector.commit()

        # get SQL result
        records = cursor.fetchall()

        cursor.close()
        connector.close()

        return records

    except psycopg2.Error as e:
        print(e)
        print('cursor error')
