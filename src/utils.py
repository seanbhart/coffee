# print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))
import psycopg2
import urllib.request
from xlrd import open_workbook
from . import connect


def sql(query, *vars):
    connector = connect.connect()
    cursor = connector.cursor()

    try:
        # execute SQL
        cursor.execute(query, vars)
        connector.commit()

        # print SQL result
        records = cursor.fetchall()
        # print(records)
        return records

    except psycopg2.Error as e:
        print(e)
        # clear the error for the next query
        connector.rollback()
        return e

    # Close the db connection
    cursor.close()
    connector.close()


def get_workbook_at(link):
    file_name, headers = urllib.request.urlretrieve(link)
    return open_workbook(file_name)


def get_months():
    connector = connect.connect()
    cursor = connector.cursor()

    try:
        # execute SQL
        cursor.execute("SELECT * FROM month")
        connector.commit()

        # return SQL result
        records_raw = dict(cursor.fetchall())
        records = {y:x for x,y in records_raw.items()}
        return records

    except psycopg2.Error as e:
        print(e)
        # clear the error for the next query
        connector.rollback()

    # Close the db connection
    cursor.close()
    connector.close()


def get_coffee_types():
    connector = connect.connect()
    cursor = connector.cursor()

    try:
        # execute SQL
        cursor.execute("SELECT symbol,id FROM coffee_type")
        connector.commit()

        # return SQL result
        records = dict(cursor.fetchall())
        return records

    except psycopg2.Error as e:
        print(e)
        # clear the error for the next query
        connector.rollback()

    # Close the db connection
    cursor.close()
    connector.close()


def locations_to_db():
    # from pathlib import Path

    # base_path = Path(__file__).parent
    # file_path = (base_path / '../locations.xlsx').resolve()

    wb = open_workbook('locations.xlsx')
    for s in wb.sheets():
        print('Sheet: %s' % (s.name))
        if s.name == 'ALL':
            for row in range(1, s.nrows):
                id = int(s.cell(row, 0).value)
                parent = int(s.cell(row, 1).value)
                location = s.cell(row, 2).value
                names = tuple(s.cell(row, 3).value.split('|'))
                query = ("INSERT INTO location"
                         " (id,parent_location_id,title)"
                         " VALUES (%s, %s, %s)"
                         " RETURNING id")
                sql(query, id, parent, location)
                for name in names:
                    query = ("INSERT INTO location_name"
                             " (location_id,name)"
                             " VALUES (%s, %s)"
                             " RETURNING location_id")
                    sql(query, id, name)


def locations_to_json():
    import json
    from pathlib import Path

    base_path = Path(__file__).parent
    file_path = (base_path / '../locations.xlsx').resolve()

    wb = open_workbook(file_path)
    data = {}
    data['locations'] = []
    for s in wb.sheets():
        print('Sheet: %s' % (s.name))
        if s.name == 'ALL':
            for row in range(1, s.nrows):
                id = int(s.cell(row, 0).value)
                parent = int(s.cell(row, 1).value)
                location = s.cell(row, 2).value
                names = tuple(s.cell(row, 3).value.split('|'))
                # print('%d, %d, %s, %s' % (id, parent, location, names))
                location_object = {}
                location_object['id'] = id
                location_object['parent'] = parent
                location_object['location'] = location
                location_object['names'] = names
                data['locations'].append(location_object)

    # json_data = json.dumps(data)
    # print(json)
    with open('locations.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
