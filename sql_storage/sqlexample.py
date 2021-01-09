# Copyright (c) Microsoft Corporation.

"""
Example using pyodbc, create an environment and execute 

pip install pyodbc

You will need an 
- SQL Server
- Table
- Username
- Password

Then you can either execute queries you generate here or queries stored in a file. 
Results can be saved to a CSV file or simply printed out. 

Fo the example below, it assumes a database with the following table:

CREATE TABLE Employee (
    PersonID int,
    LastName varchar(255),
    FirstName varchar(255),
    Address varchar(255),
    City varchar(255)
);

"""
from utils import SqlConn

server = 'YOUSVR.database.windows.net'
database = 'DB_NAME'
username = 'USER_NAME'
password = 'USER_PASSWORD'   
driver= '{ODBC Driver 17 for SQL Server}'

table_name = "Employee"

with SqlConn(server,username, password, driver) as sql:

    query_result = sql.execute(database, "SELECT * from {}".format(table_name))
    for r in query_result:
        # Note that results return a python object that have made column
        # values first class properties of the object.
        print("You found:", r.FirstName)

    # Save your results as a CSV
    SqlConn.dump_sql_data_to_csv('query_results.csv', query_result)

    # You can also execute SQL queries that are stored in files (easy)
    print("Load from file")
    query_result = sql.execute_sql_file(database, './test.sql')
    if(query_result):
        for r in query_result:
            print(vars(r))

    # Not sure if this is useful for you, but insert uses a dictionary 
    # to store row data.
    new_person = {
        "PersonID" : 4,
        "LastName" : "McMahon",
        "FirstName" : "Joey",
        "Address" : "Main St",
        "City" : "Boston"
    }
    # Static generate takes table name and dict for row
    statement = SqlConn.create_insert(table_name, new_person)
    sql.execute(database, statement)

