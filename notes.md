# COFFEE DB NOTES

## PostgreSQL

`brew services start postgresql`  
`createdb coffee`  
OR  
`initdb [OPTION]... [DATADIR]`  
`psql coffee`  


## SETUP DB
### Add tables
CREATE USER coffeeadmin WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE coffee TO coffeeadmin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO coffeeadmin;

CREATE TABLE month (id int PRIMARY KEY, title text);
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO coffeeadmin;
INSERT INTO month (id, title) VALUES (1,'January');
INSERT INTO month (id, title) VALUES (2,'February');
INSERT INTO month (id, title) VALUES (3,'March');
INSERT INTO month (id, title) VALUES (4,'April');
INSERT INTO month (id, title) VALUES (5,'May');
INSERT INTO month (id, title) VALUES (6,'June');
INSERT INTO month (id, title) VALUES (7,'July');
INSERT INTO month (id, title) VALUES (8,'August');
INSERT INTO month (id, title) VALUES (9,'September');
INSERT INTO month (id, title) VALUES (10,'October');
INSERT INTO month (id, title) VALUES (11,'November');
INSERT INTO month (id, title) VALUES (12,'December');

CREATE TABLE coffee_type (id int, title text, symbol text);
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO coffeeadmin;
INSERT INTO coffee_type (id, title, symbol) VALUES (1,'Arabica','(A)');
INSERT INTO coffee_type (id, title, symbol) VALUES (2,'Robusta','(R)');
INSERT INTO coffee_type (id, title, symbol) VALUES (3,'Both','(A/R)');
INSERT INTO coffee_type (id, title, symbol) VALUES (3,'Both','(R/A)');

CREATE TABLE location (id int PRIMARY KEY, title text, parent_location_id int);
CREATE TABLE location_name (location_id int, name text);

CREATE TABLE seasonal_inventory (id text PRIMARY KEY, year int, harvest_month_id int, location_id int, coffee_type int, value float);
CREATE TABLE seasonal_production (id text PRIMARY KEY, year int, harvest_month_id int, location_id int, coffee_type int, value float);
CREATE TABLE seasonal_exports (id text PRIMARY KEY, year int, harvest_month_id int, location_id int, coffee_type int, value float);
CREATE TABLE seasonal_consumption (id text PRIMARY KEY, year int, harvest_month_id int, location_id int, coffee_type int, value float);

CREATE TABLE calendar_inventory (id text PRIMARY KEY, year int, location_id int, value float);
CREATE TABLE calendar_imports (id text PRIMARY KEY, year int, location_id int, value float);
CREATE TABLE calendar_exports (id text PRIMARY KEY, year int, location_id int, value float);
CREATE TABLE calendar_consumption (id text PRIMARY KEY, year int, location_id int, value float);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO coffeeadmin;


## OTHER SQL
SELECT relation::regclass, * FROM pg_locks WHERE NOT GRANTED;

ALTER TABLE production DROP CONSTRAINT production_pkey;
ALTER TABLE production ALTER COLUMN value float;
ALTER TABLE production ADD COLUMN region text;
ALTER TABLE production RENAME COLUMN production TO id;
ALTER TABLE production ADD PRIMARY KEY (id);

ALTER TABLE consumption ADD CONSTRAINT consumption_pkey PRIMARY KEY (id);

SELECT * FROM calendar_consumption WHERE year=2018 ORDER BY location_id DESC LIMIT 5;
SELECT lid.title AS location,pid.title AS parent,cons.year,cons.value AS consumption
FROM calendar_consumption cons
INNER JOIN location lid ON cons.location_id=lid.id
INNER JOIN location pid ON lid.parent_location_id=pid.id
WHERE year=2018 ORDER BY location_id ASC LIMIT 5;

SELECT location.location,calendar_imports.year,calendar_imports.value
FROM calendar_imports
INNER JOIN location
ON calendar_imports.location=location.id
WHERE year=1990;

SELECT location.location,location.parent,calendar_exports.year,calendar_exports.value
FROM calendar_exports
INNER JOIN location
ON calendar_exports.location=location.id
WHERE year=1990
ORDER BY parent ASC,location ASC;

SELECT year,SUM(value) FROM calendar_exports GROUP BY year ORDER BY year;

INSERT INTO location_name (id,name) VALUES (2,'Central America & Mexico');


SELECT l.location,ce.year AS eyr,ce.value AS exports,ci.year AS iyr,ci.value AS imports 
FROM location l
INNER JOIN calendar_imports ci ON ci.location=l.id 
INNER JOIN calendar_exports ce ON ce.location=l.id 
WHERE l.location='USA' AND ci.year>2014 AND ce.year>2014 
ORDER BY ci.year ASC, ce.year ASC;


SELECT l.location, cal.year, cal.imports, cal.exports 
FROM location l 
INNER JOIN
    (
        SELECT ci.location, ci.year, ci.value AS imports,  
        CASE  
            WHEN ce.value > 0 THEN ce.value * -1 
        END AS exports 
        FROM calendar_imports ci 
        INNER JOIN calendar_exports ce ON ci.location=ce.location AND ci.year=ce.year
    ) AS cal
ON cal.location=l.id 
WHERE l.location='USA' AND cal.year>2014 
ORDER BY cal.year ASC;


SELECT l.location, cal.year, cal.type, cal.value 
FROM location l 
INNER JOIN
    (
        SELECT ci.location, ci.year, t.* 
        FROM calendar_imports ci 
        INNER JOIN calendar_exports ce ON ci.location=ce.location AND ci.year=ce.year 
        CROSS JOIN LATERAL
        (
            VALUES
            (ci.value, 'imports'),
            (ce.value, 'exports')
        ) AS t(value, type)
    ) AS cal
ON cal.location=l.id 
WHERE l.location='USA' AND cal.year>2014 
ORDER BY cal.year ASC;

SELECT l.location, cal3.year, cal3.inventory, cal3.imports, cal3.exports, cal3.consumption, cal3.inventory + cal3.imports + cal3.exports + cal3.consumption AS net
FROM location l 
INNER JOIN
    (
        SELECT cons.location, cons.year, cal2.inventory, cal2.imports, cal2.exports, 
            CASE 
                WHEN cons.value > 0 THEN cons.value * -1 
            END AS consumption 
        FROM calendar_consumption cons 
        INNER JOIN
            (
                SELECT inv.location, inv.year, inv.value as inventory, cal.imports, cal.exports 
                FROM calendar_inventory inv 
                INNER JOIN
                    (
                        SELECT ci.location, ci.year, ci.value AS imports,  
                            CASE  
                                WHEN ce.value > 0 THEN ce.value * -1 
                            END AS exports 
                        FROM calendar_imports ci 
                        INNER JOIN calendar_exports ce ON ci.location=ce.location AND ci.year=ce.year
                    ) AS cal
                ON cal.location=inv.location AND inv.year=cal.year
            ) AS cal2
        ON cal2.location=cons.location AND cons.year=cal2.year
    ) AS cal3
ON cal3.location=l.id
WHERE l.location='USA' AND cal3.year>2014
ORDER BY cal3.year ASC;


SELECT l.location, positive.year, positive.inventory, positive.imports, negative.exports, negative.consumption 
FROM location l
INNER JOIN
    (
        SELECT inv.location, inv.year, inv.value as inventory, ci.value AS imports 
        FROM calendar_inventory inv 
        INNER JOIN calendar_imports ci ON inv.location=ci.location AND inv.year=ci.year
    ) AS positive
    ON positive.location=l.id
INNER JOIN
    (
        SELECT cons.location, cons.year,  
            CASE  
                WHEN cons.value > 0 THEN cons.value * -1 
            END AS consumption,
            CASE  
                WHEN ce.value > 0 THEN ce.value * -1 
            END AS exports
        FROM calendar_consumption cons
        INNER JOIN calendar_exports ce ON cons.location=ce.location AND cons.year=ce.year
    ) AS negative
    ON negative.location=l.id
WHERE l.location='USA' AND positive.year>2014 AND negative.year>2014
ORDER BY positive.year ASC;



# [ICO Historical Data](http://www.ico.org/new_historical.asp?section=Statistics)
```
Supply Data
- Total production - Crop Year              | 1A | SOURCE | `1A_exporters_production.xlsx`      | db: `seasonal_production`
- Domestic consumption - Crop Year          | 1B | SOURCE | `1B_exporters_consumption.xlsx`     | db: `seasonal_consumption`
- Exportable production - Crop Year         | 1C | CALC   | ``
- Gross opening stocks - Crop Year          | 1D | SOURCE | `1D_exporters_inventory.xlsx`       | db: `seasonal_inventory`
- Exports - Crop Year                       | 1E | SOURCE | `1E_exporters_exports.xlsx`         | db: `seasonal_exports`

Trade Statistics Data
- Exports - Calendar Year                   | 2A | SOURCE | `2A_exporters_exports.xlsx`         | db: `calendar_exports` <<-- NOT ADDED YET
- Imports - Calendar Year                   | 2B | SOURCE | `2B_importers_imports.xlsx`         | db: `calendar_imports`
- Re-exports - Calendar Year                | 2C | SOURCE | `2C_importers_exports.xlsx`         | db: `calendar_exports`

Price Data (US cents per lb)
- Prices to Growers - Annual Averages       | 3A | SOURCE | ``
- Retail Prices - Annual Averages           | 3B | ``
- ICO Composite & Group                     | 3C | ``
- Indicator Prices - Monthly Averages       | 3D | ``
- ICO Composite & Group                     | 3E | ``
- Indicator Prices - Daily Prices           | 3F | ``

Inventories/Consumption Data
- Inventories - End of Year                 | 4A | SOURCE | `4A_importers_inventory.xlsx`       | db: `calendar_inventory`
- Disappearance (consumption) - End of Year | 4B | CALC   | `4B_importers_consumption.xlsx`     | db: `calendar_consumption`

Non-Member Data
- Imports - Calendar Year                   | 5A | SOURCE | `5A_importers_other_imports.xlsx`   | db: `calendar_imports`
- Re-exports - Calendar Year                | 5B | SOURCE | `5B_importers_other_exports.xlsx`   | db: `calendar_exports`

OTHER (NOT ICO)
- Imports of Exporters                      | 6A | ``
```
## Analysis Logic (year n)
- Coffee Flow Exporters: 1D(n) + 1A(n) + 6A(n) - 1E(n) - 1B(n) = 1D(n+1)
- Coffee Flow Importers: 4A(n) + 2B(n) - 2C(n) - 4B(n) = 4A(n+1)


# TO-DO
- Rework databases - separate exporters & importers? (need to distinguish year vs. crop year?)
- Explain difference in "Exports (Supply)" vs. "Exports (Trade Statistics)"
- Setup consumer "Imports"
- Check "Non-member data"






import sys
sys.path.append('../')
import pandas as pd
from matplotlib import pyplot as plt
from src import connect
conn = connect.connect()
# colors = ["#CFC4AC","#C7C0A4","#8E9B82","#4D352D","#211F1C"]"#70193D"
colors = ["#839B7F","#A5A181","#B18558","#2B1504","#00494F"]

df = pd.read_sql("SELECT value FROM seasonal_production WHERE coffee_type=3 AND location='Brazil' ORDER BY year",conn)
# list = [i[0] for i in query]
# s = pd.Series(list)
graph = pd.plotting.bootstrap_plot(df, size=10, samples=500, color='yellow')

df = pd.read_sql("SELECT location,value FROM production WHERE crop_year=2019 AND value>3000 ORDER BY value DESC",conn) #,SUM(value)
# locations = [i[0] for i in p]
# production = [i[1] for i in p]
# s = pd.Series(production, index=locations)
bar = df.plot.bar(figsize=(16,5), color='green')
yt = bar.set_yticklabels([f'{x:,.0f}' for x in bar.get_yticks()])

df = pd.read_sql("SELECT location,value FROM production WHERE crop_year=2019 AND value<3000 ORDER BY value DESC",conn)
# locations = [i[0] for i in p]
# production = [i[1] for i in p]
# s = pd.Series(production, index=locations)
bar = df.plot.bar(figsize=(16,5), color='green')
yt = bar.set_yticklabels([f'{x:,.0f}' for x in bar.get_yticks()])

df = pd.read_sql("SELECT crop_year,value FROM production WHERE location='Brazil';",conn)
df.columns=['crop_year','value']
bar = df.plot.bar(y='value', figsize=(16,5), color='green', legend=False)
labels = bar.set_xticklabels(df['crop_year'].tolist(), rotation=0)
b=bar.set_yticklabels([f'{x:,.0f}' for x in bar.get_yticks()])
# b=bar.set_ylim(15000,65000)
b=bar.set_xlabel("")
b=bar.set_ylabel("")

df = pd.read_sql("SELECT location,region,value FROM inventory WHERE year='2018' AND location=region ORDER BY value DESC;",conn)
df.columns=['location','region','value']
bar = df.plot.bar(y='value', figsize=(16,5), color='tan', legend=False)
labels = bar.set_xticklabels(df['region'].tolist(), rotation=90)
b=bar.set_yticklabels([f'{x:,.0f}' for x in bar.get_yticks()])
# b=bar.set_ylim(15000,65000)
b=bar.set_xlabel("")
b=bar.set_ylabel("")

df = pd.read_sql("""SELECT l.title, cal3.year, cal3.inventory, cal3.imports, cal3.exports, cal3.consumption, cal3.inventory + cal3.imports + cal3.exports + cal3.consumption AS net
FROM location l 
INNER JOIN
    (
        SELECT cons.location_id, cons.year, cal2.inventory, cal2.imports, cal2.exports, 
            CASE 
                WHEN cons.value > 0 THEN cons.value * -1 
            END AS consumption 
        FROM calendar_consumption cons 
        INNER JOIN
            (
                SELECT inv.location_id, inv.year, inv.value as inventory, cal.imports, cal.exports 
                FROM calendar_inventory inv 
                INNER JOIN
                    (
                        SELECT ci.location_id, ci.year, ci.value AS imports,  
                            CASE  
                                WHEN ce.value > 0 THEN ce.value * -1 
                            END AS exports 
                        FROM calendar_imports ci 
                        INNER JOIN calendar_exports ce ON ci.location_id=ce.location_id AND ci.year=ce.year
                    ) AS cal
                ON cal.location_id=inv.location_id AND inv.year=cal.year
            ) AS cal2
        ON cal2.location_id=cons.location_id AND cons.year=cal2.year
    ) AS cal3
ON cal3.location_id=l.id
WHERE l.title='USA' AND cal3.year>2014
ORDER BY cal3.year ASC;""",conn)
print(df)
b1=df.loc[:,['inventory','imports','exports','consumption']].plot.bar(stacked=True, color=colors, figsize=(15,7))
b1.set_xticklabels(df['year'].tolist(), rotation=0)
b1.set_yticklabels([f'{x:,.0f}' for x in b1.get_yticks()])
b1.set_ylim([min(b1.get_yticks()),max(b1.get_yticks())])
b1.legend(loc='lower left')
l1 = b1.twinx()
l1.set_yticklabels([])
l1.set_ylim([min(b1.get_yticks()),max(b1.get_yticks())])
l1.plot(b1.get_xticks(), df['net'], label='net', marker='o', color=colors[4])
l1.legend(loc='upper left')
for i,x in enumerate(df['net']):
    label = f'{x:,.0f}'
    l1.annotate(label,
                (i,x),
                textcoords="offset points", # how to position the text
                xytext=(0,10), # distance from text to points (x,y)
                ha='center') # horizontal alignment can be left, right or center

