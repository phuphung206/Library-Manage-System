import pyodbc


class DatabaseConnection:
    _instance = None

    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=LMS_DB;"
            "Trusted_Connection=yes;"
        )
        self._conn = None

    @classmethod
    def get_instance(cls, connection_string: str = None):
        if cls._instance is None:
            cls._instance = cls(connection_string)
        return cls._instance

    def get_connection(self):
        if self._conn is None:
            self._conn = pyodbc.connect(self.connection_string)
        return self._conn