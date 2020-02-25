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
#------------------------------------------------
# Find Parent Locations - Compare EXISTS vs DISTINCT (EXISTS wins 80+%)
EXPLAIN ANALYZE
SELECT title
FROM location l
WHERE EXISTS (
        SELECT id
        FROM location
        WHERE parent_location_id=l.id
    )
ORDER BY title;

EXPLAIN ANALYZE
SELECT DISTINCT l.title
FROM location l
INNER JOIN location lo ON lo.parent_location_id=l.id
ORDER BY title;
#------------------------------------------------
# List Production by Location - Compare CROSS join vs INNER join (INNER wins slightly more)
EXPLAIN ANALYZE
SELECT l.title, p.value
FROM seasonal_production p
CROSS JOIN location l
WHERE p.location_id=l.id;

EXPLAIN ANALYZE
SELECT l.title, p.value
FROM seasonal_production p
INNER JOIN location l ON p.location_id=l.id;
#------------------------------------------------
# Compare HAVING vs FROM sub-query (very similar results)
EXPLAIN ANALYZE
SELECT p.location_id, SUM(p.value) / COUNT(p.location_id)
FROM seasonal_production p
GROUP BY p.location_id
HAVING SUM(p.value) / COUNT(p.location_id) > 1000
ORDER BY p.location_id;

EXPLAIN ANALYZE
SELECT x.location_id, SUM(x.production_average)
FROM (
    SELECT p.location_id, SUM(p.value) / COUNT(p.location_id) production_average
    FROM seasonal_production p
    GROUP BY p.location_id
) x
WHERE x.production_average > 1000
GROUP BY x.location_id
ORDER BY x.location_id;
#------------------------------------------------
# Compare INNER JOIN vs INTERSECT (INTERSECT much faster)
EXPLAIN ANALYZE
SELECT DISTINCT ci.location_id FROM calendar_imports ci 
INNER JOIN calendar_exports ce ON ce.location_id = ci.location_id
ORDER BY ci.location_id
LIMIT 50;

EXPLAIN ANALYZE
SELECT ci.location_id FROM calendar_imports ci 
INTERSECT
SELECT ce.location_id FROM calendar_exports ce
ORDER BY location_id
LIMIT 50;
#------------------------------------------------
# CROSS JOIN LATERAL
EXPLAIN ANALYZE
SELECT l.title, cal.year, cal.type, cal.value 
FROM location l 
INNER JOIN
    (
        SELECT ci.location_id, ci.year, t.* 
        FROM calendar_imports ci 
        INNER JOIN calendar_exports ce ON ci.location_id=ce.location_id AND ci.year=ce.year 
        CROSS JOIN LATERAL
        (
            VALUES
            (ci.value, 'imports'),
            (ce.value, 'exports')
        ) AS t(value, type)
    ) AS cal
ON cal.location_id=l.id 
WHERE l.title='USA' AND cal.year>2014 
ORDER BY cal.year ASC;

# All USA calendar year data
SELECT l.title, cal3.year, cal3.inventory * 66.138679 AS inventory, cal3.imports * 66.138679 AS imports, cal3.exports * 66.138679 AS exports, cal3.consumption * 66.138679 AS consumption, (cal3.inventory + cal3.imports + cal3.exports + cal3.consumption) * 66.138679 AS net
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
WHERE l.title='EU' AND cal3.year>2008
ORDER BY cal3.year ASC;

# Compare calculated ending inventory with reported next year inventory
SELECT cal2.year, TO_CHAR(ROUND(SUM(inv.value * 66.138679)::NUMERIC,0),'9,999,999') AS "reported", TO_CHAR(ROUND(SUM((pinv.value + cal2.imports + cal2.exports + cal2.consumption) * 66.138679)::NUMERIC,0),'9,999,999') AS "calculated", TO_CHAR(ROUND((SUM(inv.value * 66.138679) - SUM((pinv.value + cal2.imports + cal2.exports + cal2.consumption) * 66.138679))::NUMERIC,0),'9,999,999') AS discrepancy
FROM calendar_inventory inv 
INNER JOIN
    (
        SELECT cons.location_id, cons.year, cal.imports, cal.exports,
            CASE 
                WHEN cons.value > 0 THEN cons.value * -1 
            END AS consumption 
        FROM calendar_consumption cons 
        INNER JOIN
            (
                SELECT ci.location_id, ci.year, ci.value AS imports,  
                    CASE  
                        WHEN ce.value > 0 THEN ce.value * -1 
                    END AS exports 
                FROM calendar_imports ci 
                INNER JOIN calendar_exports ce ON ci.location_id=ce.location_id AND ci.year=ce.year
            ) AS cal
        ON cal.location_id=cons.location_id AND cons.year=cal.year
    ) AS cal2
ON cal2.location_id=inv.location_id AND inv.year=cal2.year
INNER JOIN calendar_inventory pinv ON pinv.location_id=cal2.location_id AND pinv.year=cal2.year-1
WHERE cal2.year>2008
GROUP BY cal2.year
ORDER BY cal2.year ASC;

# (TODO) Compare calculated ending inventory with reported next year inventory at regional levels
SELECT title
FROM location l
WHERE EXISTS (
        SELECT id
        FROM location
        WHERE parent_location_id=l.id
    )
ORDER BY title;

SELECT title
FROM location l
ON cal4.location_id=l.id
WHERE parent_location_id=0
ORDER BY title;



SELECT relation::regclass, * FROM pg_locks WHERE NOT GRANTED;

ALTER TABLE production DROP CONSTRAINT production_pkey;
ALTER TABLE production ALTER COLUMN value float;
ALTER TABLE production ADD COLUMN region text;
ALTER TABLE production RENAME COLUMN production TO id;
ALTER TABLE production ADD PRIMARY KEY (id);
ALTER TABLE consumption ADD CONSTRAINT consumption_pkey PRIMARY KEY (id);

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


SELECT l.title, ci.value
FROM calendar_imports ci
INNER JOIN location l ON l.id=ci.location_id
WHERE ci.value > (
        SELECT ce.value
        FROM calendar_exports ce
        WHERE ce.location_id=ci.location_id
        AND ce.year=ci.year
    );



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
- Disappearance (consumption) - End of Year | 4B | CALC   | `4B_importers_consumption.xlsx`     | db: `calendar_consumption` <<-- 2014+ DATA INCORRECT

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
- ADD LOCATION GROUPING TABLE - ALLOW CUSTOM GROUPING FOR ANALYSIS (cannot separate child/parent/regions effectively otherwise)
- Fix overall analysis graphs - importers cannot compare reported vs. calc because consumption is calculated
- DO NOT USE IMPORTER CONSUMPTION DATA
- Global trade flows - any holes in the data?
- Production outflow - discrepancy in calc inv vs. reported?
- Consumption outflow - discrepancy in calc inv vs. reported?
- Explain difference in "Exports (Supply)" vs. "Exports (Trade Statistics)"






# PANDAS
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
