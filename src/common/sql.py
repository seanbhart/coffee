import psycopg2
from .. import connect


month_dict = {
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12,
}
month_dict2 = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December',
}
# sql_string = """
#     SELECT value
#     FROM production
#     WHERE coffee_type=3
#     AND location='Brazil'
#     ORDER BY crop_year
# """


# Setup the coffee database
def sql():
    # id = 'Texas-2020-6'
    # crop_year = 2020
    # harvest_month = 6
    # location = 'Texas'
    # coffee_type = 2
    # value = 100

    connector = connect.connect()
    cursor = connector.cursor()

    for m in range(1, 13):

        try:
            # execute SQL
            cursor.execute("INSERT INTO month"
                "(month,id)"
                "VALUES (%s, %s)"
                "RETURNING month"
                , (month_dict2[m], m))
            connector.commit()

            # get SQL result
            records = cursor.fetchall()
            print(records)

        except psycopg2.Error as e:
            print(e)
            # clear the error for the next query
            connector.rollback()

    cursor.close()
    connector.close()


if __name__ == "__main__":
    sql()
