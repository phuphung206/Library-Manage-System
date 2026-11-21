import pyodbc

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        """
        Cấu hình thông tin kết nối đến Microsoft SQL Server
        """
        server_name = 'LAPTOP-PP8RNT1R\\SQLEXPRESS' 
        database_name = 'library_management_system'
        
        conn_str = (
            r'DRIVER={ODBC Driver 11 for SQL Server};'
            rf'SERVER={server_name};'
            rf'DATABASE={database_name};'
            r'Trusted_Connection=yes;'
        )
        
        try:
            self.connection = pyodbc.connect(conn_str)
            print("✅ Kết nối cơ sở dữ liệu SQL Server thành công!")
        except pyodbc.Error as e:
            print("❌ Lỗi kết nối CSDL. Vui lòng kiểm tra lại Server Name hoặc Driver.")
            print(f"Chi tiết lỗi: {e}")
            self.connection = None

    def get_connection(self):
        return self.connection

if __name__ == "__main__":
    db = DatabaseConnection()
    conn = db.get_connection()