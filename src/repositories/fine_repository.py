import pyodbc
from datetime import datetime

class FineRepository:
    def __init__(self, connection):
        self.conn = connection 

    # ================= 1. QUẢN LÝ CẤU HÌNH (CONFIGS) =================
    def get_all_configs(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT config_key, config_value, description FROM system_configs")
        return cursor.fetchall()

    def update_config(self, key, new_value, admin_id):
        cursor = self.conn.cursor()
        query = """
            UPDATE system_configs 
            SET config_value = ?, updated_by = ?, updated_at = GETDATE() 
            WHERE config_key = ?
        """
        cursor.execute(query, (new_value, admin_id, key))
        self.conn.commit()

    def get_config_value(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT config_value FROM system_configs WHERE config_key = ?", (key,))
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0

    # ================= 2. QUẢN LÝ TIỀN PHẠT & THANH TOÁN =================
    def get_unpaid_fines(self, member_id):
        cursor = self.conn.cursor()
        query = """
            SELECT fine_id, fine_type, overdue_days, amount, created_at 
            FROM fines 
            WHERE member_id = ? AND status = 'UNPAID'
        """
        cursor.execute(query, (member_id,))
        return cursor.fetchall()

    def process_fine_payment(self, fine_id, librarian_id, payment_method, amount, receipt_code):
        """Thực thi ACID Transaction: Vừa thêm biên lai, vừa cập nhật trạng thái phạt"""
        cursor = self.conn.cursor()
        try:
            # 1. Thêm vào bảng fine_payments
            insert_receipt = """
                INSERT INTO fine_payments (fine_id, librarian_id, payment_method, amount_paid, receipt_code)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_receipt, (fine_id, librarian_id, payment_method, amount, receipt_code))
            
            # 2. Cập nhật bảng fines thành PAID
            update_fine = "UPDATE fines SET status = 'PAID' WHERE fine_id = ?"
            cursor.execute(update_fine, (fine_id,))
            
            self.conn.commit()
            return True, "Thanh toán thành công!"
        except Exception as e:
            self.conn.rollback()
            return False, f"Lỗi giao dịch: {str(e)}"

    # ================= 3. TRUY VẤN BÁO CÁO (REPORTS) =================
    def get_top_borrowed_books(self):
        try:
            cursor = self.conn.cursor() 
            
            query = '''
                SELECT TOP 5 
                    bt.title, 
                    COUNT(bc.copy_id) as borrow_count
                FROM book_titles bt
                JOIN book_copies bc ON bt.title_id = bc.title_id
                JOIN loan_transactions lt ON bc.copy_id = lt.copy_id
                GROUP BY bt.title
                ORDER BY borrow_count DESC
            '''
            
            cursor.execute(query)
            return cursor.fetchall()
            
        except Exception as e:
            print("Lỗi khi lấy top sách mượn:", e)
            return []

    def get_overdue_readers_report(self):
        cursor = self.conn.cursor()
        query = """
            SELECT u.card_number, u.full_name, COUNT(f.fine_id) as total_unpaid_fines, SUM(f.amount) as total_debt
            FROM fines f
            JOIN users u ON f.member_id = u.user_id
            WHERE f.status = 'UNPAID'
            GROUP BY u.card_number, u.full_name
            ORDER BY total_debt DESC
        """
        cursor.execute(query)
        return cursor.fetchall()