import pyodbc

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        # 1. Cấu hình chính xác Server và Database cho máy của bạn
        server_name = r'LAPTOP-PP8RNT1R\SQLEXPRESS'
        database_name = 'library_management_system'
        
        # 2. Gán trực tiếp vào biến self.connection_string mà hệ thống cần
        self.connection_string = (
            r'DRIVER={ODBC Driver 11 for SQL Server};'
            rf'SERVER={server_name};'
            rf'DATABASE={database_name};'
            r'Trusted_Connection=yes;'
        )
        self._conn = None

    def get_connection(self):
        if self._conn is None:
            try:
                self._conn = pyodbc.connect(self.connection_string)
                print("✅ Kết nối cơ sở dữ liệu SQL Server thành công!")
            except pyodbc.Error as e:
                print(f"❌ Lỗi kết nối CSDL. Chi tiết: {e}")
                self._conn = None
        return self._conn