# Copyright (c) Microsoft Corporation.

import pyodbc # pylint: disable=E0401,E0611


class SqlData:
    def __init__(self, columns, data):
        if len(columns) != len(data):
            raise Exception("Columns must equal data {} != {}".format(len(columns), len(data)))

        for idx in range(len(columns)):
            setattr(self, columns[idx], data[idx])


class SqlConn:
    def __init__(self, server, user, credential, driver):
        self.connections = {}
        self.server = server
        self.user = user
        self.credential = credential
        self.driver = driver

    def execute_sql_file(self, database, sql_file):
        file_content = None

        with open(sql_file,'r') as sql_data:
            file_content = sql_data.readlines()
            file_content = "\n".join(file_content)

        return self.execute(database, file_content)

    def execute(self, database, query):
        return_data = []

        connection = self._connect(database)
        with connection.cursor() as cursor:
            cursor.execute(query)
            
            if cursor.description:
                columns = []
    
                for desc in cursor.description:
                    columns.append(desc[0])
    
                row = cursor.fetchone()
                while row:
                    if columns:
                        return_data.append(SqlData(columns, row))
                    row = cursor.fetchone()        
            else:
                # If no description we can find out if there are row counts 
                # which will reflect insert/delete rows affected, etc.
                return_data.append(SqlData(["rows"], [cursor.rowcount]))

        return return_data

    @staticmethod
    def dump_sql_data_to_csv(filename, sqldatalist):
        
        if len(sqldatalist):
            columns = []
            for var in vars(sqldatalist[0]).keys():
                columns.append(var)

            with open(filename, "w") as query_output:
                query_output.write("{}\n".format(",".join(columns)))

                for sqldata in sqldatalist:
                    data = []
                    for col in columns:
                        data.append(str(getattr(sqldata,col,'')))

                    query_output.write("{}\n".format(",".join(data)))

    @staticmethod
    def create_insert(table_name, record_data):
        """
        table_name : str
            Name of the table to insert into
        record_data:
            Key is name of field, value is value to insert

        INSERT INTO Employee (PersonId, LastName, FirstName, Address, City)
        VALUES (3, 'Grecoe','Elle', 'Carmel', 'Andover');
        """

        fields = ",".join(record_data.keys())

        raw_values = []
        for k in record_data.keys():
            if isinstance(record_data[k], str):
                raw_values.append("'{}'".format(record_data[k]))
            else:
                raw_values.append("{}".format(record_data[k]))

        values = ",".join(raw_values)

        return "INSERT INTO {} ({}) VALUES ({})".format(table_name, fields, values)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        #Exception handling here, if any, close all connections
        self._disconnect()

    def _disconnect(self):
        for conn in self.connections:
            self.connections[conn].close()

    def _connect(self, database):

        if database not in self.connections:
            if not self.server:
                raise Exception("Server must be identified")                                
            if not self.user:
                raise Exception("User must be identified")                                
            if not self.credential:
                raise Exception("User Credential must be identified")                                
            if not self.driver:
                raise Exception("ODBC Driver must be identified")   

            # 'DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password
            conn_str = 'DRIVER={};SERVER={};PORT=1433;DATABASE={};UID={};PWD={}'.format(
                self.driver,
                self.server,
                database,
                self.user,
                self.credential
            )

            self.connections[database] = pyodbc.connect(conn_str)                                                                  

        return self.connections[database]