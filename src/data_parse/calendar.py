from .. import utils


# Excel sheet links
link_importers_inventory = 'http://www.ico.org/historical/1990%20onwards/Excel/4a%20-%20Inventories.xlsx'
link_importers_imports = 'http://www.ico.org/historical/1990%20onwards/Excel/2b%20-%20Imports.xlsx'
link_importers_other_imports = 'http://www.ico.org/historical/1990%20onwards/Excel/5a%20-%20Non-member%20imports.xlsx'
link_importers_exports = 'http://www.ico.org/historical/1990%20onwards/Excel/2c%20-%20Re-exports.xlsx'
link_importers_other_exports = 'http://www.ico.org/historical/1990%20onwards/Excel/5b%20-%20Non-member%20re-exports.xlsx'
link_importers_consumption = 'http://www.ico.org/historical/1990%20onwards/Excel/4b%20-%20Disappearance.xlsx'

# The first column will be the location names
# The second column will start the data
location_col = 0
value_col = 1

# Store the data in a local dict to sum any split locations
# data is stored in id:value format
data = {}


def calendar_data_update(link, sheet_name, db_name):
    # Reset the dict
    global data
    data = {}

    # Get the workbook from the link
    wb = utils.get_workbook_at(link)

    # Find the correct sheet in the workbook
    sheet = find_sheet(wb, sheet_name)

    # Find the first row that is not blank
    topRow = find_data_start_row(sheet, 1)

    for col in range(value_col, sheet.ncols):
        # First get the calendar year - it will be two years,
        # so grab the first two numbers for century
        # and last two numbers for year
        year = int(sheet.cell(topRow, col).value)

        # Grab the location data on each row for this year
        # skip the header row
        for row in range(topRow+1, sheet.nrows):

            # If the location cell contains the word 'inventories'
            # or is empty it is not a countable cell
            inventories_text_start = sheet.cell(row, location_col).value.find('Inventories')
            if inventories_text_start == -1 and sheet.cell(row, location_col).value != "":

                # If you get to the 'Total' row, stop
                if sheet.cell(row, location_col).value == 'Total':
                    break

                # If the first column might have two spaces at the beginning
                # of the cell - be sure to clean up the text
                location_name = sheet.cell(row, location_col).value
                location_name = location_name.strip()
                # print(location_name)

                # Find the location id based off of the used name
                location_result = utils.sql("SELECT location_id FROM location_name WHERE name=%s", location_name)
                # Raise error and skip if the location cannot be found
                if len(location_result) < 1:
                    print("ERROR - LOCATION '%s' NOT FOUND" % (location_name))
                    continue

                # If the results have more than one tuple, we have duplicate location names
                if len(location_result[0]) != 1:
                    print("ERROR - LOCATION '%s' ENTRY ERROR" % (location_name))
                    continue

                location_id = location_result[0][0]
                # print(location_id)
                id = '%d-%d' % (location_id, year)

                # Check to ensure the value is not empty, if so assign 0
                value = float(0)
                if sheet.cell(row, col).value != '':
                    value = float(sheet.cell(row, col).value)

                # Get the value to use after checking for split locations
                value = calculate_location_total(id, value)

                # print("%s, %d, %d, %d" % (id, year, location_id, value))
                insert = ("INSERT INTO " + db_name +
                          " (id,year,location_id,value)"
                          " VALUES (%s, %s, %s, %s)"
                          " ON CONFLICT ON CONSTRAINT " + db_name + "_pkey"
                          " DO UPDATE SET value=%s"
                          " RETURNING id")
                utils.sql(insert, id, year, location_id, value, value)


# If a location has been split over several location names
# the values will need to be summed
def calculate_location_total(id, value):
    # Check whether the id already exists - if it does,
    # sum the previous value with the new value and
    # return the new total value for overwriting the old value
    new_value = 0
    if id in data:
        print('%s: %f' % (id, value))
        new_value = data[id] + value
    else:
        new_value = value

    # Record the entry in the data dict
    data[id] = new_value
    return new_value


def find_data_start_row(sheet, column):
    # Find the first row in the passed column with the passed text
    for row in range(sheet.nrows):
        if sheet.cell(row, column).value != '':
            return row


def find_sheet(workbook, sheet_name):
    for s in workbook.sheets():
        print('Sheet: %s' % (s.name))
        if s.name == sheet_name:
            return s


if __name__ == "__main__":
    print("ICO calendar year data update")
    calendar_data_update(link_importers_inventory, 'Inventories', 'calendar_inventory')
    calendar_data_update(link_importers_imports, 'Imports', 'calendar_imports')
    calendar_data_update(link_importers_other_imports, 'Imports', 'calendar_imports')
    calendar_data_update(link_importers_exports, 'Re-exports', 'calendar_exports')
    calendar_data_update(link_importers_other_exports, 'Re-exports', 'calendar_exports')
    calendar_data_update(link_importers_consumption, 'Disappearance', 'calendar_consumption')
