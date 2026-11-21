import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import uuid

class ReportFineService:
    def __init__(self, fine_repo):
        self.fine_repo = fine_repo

    # --- Nghiệp vụ Tiền phạt ---
    def calculate_overdue_amount(self, overdue_days):
        daily_rate = self.fine_repo.get_config_value('FINE_PER_DAY_VND')
        return overdue_days * daily_rate

    def pay_fine(self, fine_id, librarian_id, payment_method, amount):
        # Sinh mã biên lai tự động (VD: RCP-20261102-1234)
        date_str = datetime.now().strftime("%Y%m%d")
        unique_suffix = str(uuid.uuid4().hex)[:6].upper()
        receipt_code = f"RCP-{date_str}-{unique_suffix}"
        
        return self.fine_repo.process_fine_payment(fine_id, librarian_id, payment_method, amount, receipt_code)

    # --- Nghiệp vụ Báo cáo & Xuất file ---
    def export_top_books_excel(self, file_path="Top_Books_Report.xlsx"):
        data = self.fine_repo.get_top_borrowed_books()
        if not data:
            return False, "Không có dữ liệu báo cáo."
        
        # Chuyển đổi dữ liệu sang Pandas DataFrame
        df = pd.DataFrame([tuple(row) for row in data], columns=['Tên Sách', 'Số lượt mượn'])
        df.to_excel(file_path, index=False)
        return True, f"Đã xuất báo cáo thành công tại: {file_path}"

    def plot_top_books_chart(self):
        data = self.fine_repo.get_top_borrowed_books()
        if not data:
            print("Không có dữ liệu để vẽ biểu đồ.")
            return

        titles = [row[0][:20] + '...' if len(row[0]) > 20 else row[0] for row in data]
        counts = [row[1] for row in data]

        plt.figure(figsize=(10, 6))
        plt.barh(titles, counts, color='#2B6CB0')
        plt.xlabel('Số lượt mượn')
        plt.ylabel('Tên Sách')
        plt.title('Top 10 Sách Được Mượn Nhiều Nhất')
        plt.gca().invert_yaxis() # Đảo ngược trục y để sách mượn nhiều nhất ở trên cùng
        plt.tight_layout()
        plt.show()