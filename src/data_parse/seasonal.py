from .. import utils


# Excel sheet links
link_exporters_inventory = 'http://www.ico.org/historical/1990%20onwards/Excel/1d%20-%20Gross%20Opening%20stocks.xlsx'
link_exporters_production = 'http://www.ico.org/historical/1990%20onwards/Excel/1a%20-%20Total%20production.xlsx'
link_exporters_exports = 'http://www.ico.org/historical/1990%20onwards/Excel/1e%20-%20Exports%20-%20crop%20year.xlsx'
link_exporters_consumption = 'http://www.ico.org/historical/1990%20onwards/Excel/1b%20-%20Domestic%20consumption.xlsx'

# Get the month and coffee types conversions
month_dict = utils.get_months()
coffee_type_dict = utils.get_coffee_types()

# The first column will be the location names
# The second column will be coffee type (1=A,2=R,3=Both)
# The third column will start the harvest data
location_col = 0
coffee_type_col = 1
value_col = 2


def seasonal_data_update(link, sheet_name, data_header, db_name):
    # Get the workbook from the link
    wb = utils.get_workbook_at(link)

    # Set the default harvest month
    harvest_month_id = 1

    # Find the correct sheet in the workbook
    sheet = find_sheet(wb, sheet_name)

    # Find the first row with the passed keyword in the first column
    topRow = find_data_start_row(sheet, 0, data_header)

    for col in range(value_col, sheet.ncols):
        # First get the crop year - it will be two years,
        # so grab the first two numbers for century
        # and last two numbers for year
        year = int(sheet.cell(topRow, col).value[0:2] + sheet.cell(topRow, col).value[5:7])

        # Grab the location data on each row for this crop year
        for row in range(topRow, sheet.nrows):

            # If the first column has the word 'group' in the text
            # update the harvet_month to the latest month
            group_text_start = sheet.cell(row, location_col).value.find('group')
            if group_text_start != -1:
                harvest_month_text = sheet.cell(row, location_col).value[0:group_text_start - 1]
                harvest_month_id = month_dict[harvest_month_text]

            # Ensure the row has a value in the coffee type
            # column, if it does not, it is not a location data row
            if sheet.cell(row, coffee_type_col).value != "":

                location_id = sheet.cell(row, location_col).value
                value = float(sheet.cell(row, col).value)
                id = '%s-%d-%d' % (location_id, year, harvest_month_id)

                # Translate the coffee type
                coffee_type = coffee_type_dict[sheet.cell(row, coffee_type_col).value]

                # print('%s, %s, %s, %s, %s, %s' % (id, year, harvest_month_id, location_id, coffee_type, value))

                insert = ("INSERT INTO " + db_name +
                          " (id,year,harvest_month_id,location_id,coffee_type,value)"
                          " VALUES (%s, %s, %s, %s, %s, %s)"
                          " ON CONFLICT ON CONSTRAINT " + db_name + "_pkey"
                          " DO UPDATE SET coffee_type=%s,value=%s"
                          " RETURNING id")
                utils.sql(insert, id, year, harvest_month_id, location_id, coffee_type, value, coffee_type, value)


def find_data_start_row(sheet, column, text):
    # Find the first row in the passed column with the passed text
    for row in range(sheet.nrows):
        if sheet.cell(row, column).value == text:
            return row


def find_sheet(workbook, sheet_name):
    for s in workbook.sheets():
        print('Sheet: %s' % (s.name))
        if s.name == sheet_name:
            return s


if __name__ == "__main__":
    print("seasonal update")
    seasonal_data_update(link_exporters_inventory, 'Print Table here', 'Crop years', 'seasonal_inventory')
    # seasonal_data_update(link_exporters_production, 'Production', 'Crop year', 'seasonal_production')
    # seasonal_data_update(link_exporters_exports, 'Exports', 'Crop year', 'seasonal_exports')
    # seasonal_data_update(link_exporters_consumption, 'Print Table here', 'Crop year', 'seasonal_consumption')
