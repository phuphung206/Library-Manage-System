import tkinter as tk
from tkinter import ttk, messagebox

class ReportConfigView(tk.Frame):
    def __init__(self, parent, report_fine_service, admin_id):
        super().__init__(parent)
        self.service = report_fine_service
        self.admin_id = admin_id
        self.setup_ui()
        self.load_configs()

    def setup_ui(self):
        tk.Label(self, text="QUẢN LÝ CẤU HÌNH HỆ THỐNG", font=('Calibri', 16, 'bold')).pack(pady=10)
        
        # Bảng Treeview hiển thị cấu hình
        columns = ('Key', 'Value', 'Description')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=8)
        self.tree.heading('Key', text='Mã Cấu Hình')
        self.tree.heading('Value', text='Giá Trị')
        self.tree.heading('Description', text='Mô tả')
        self.tree.column('Key', width=200)
        self.tree.column('Value', width=100)
        self.tree.column('Description', width=400)
        self.tree.pack(padx=20, pady=10)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Form chỉnh sửa
        edit_frame = tk.Frame(self)
        edit_frame.pack(pady=10)
        
        tk.Label(edit_frame, text="Giá trị mới:").grid(row=0, column=0, padx=5)
        self.val_entry = tk.Entry(edit_frame, width=20)
        self.val_entry.grid(row=0, column=1, padx=5)
        
        tk.Button(edit_frame, text="Cập nhật", bg='#2B6CB0', fg='white', command=self.update_config).grid(row=0, column=2, padx=10)

        # Nút xuất báo cáo & Biểu đồ
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Vẽ Biểu Đồ Top Sách", command=self.service.plot_top_books_chart).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Xuất Excel Báo Cáo", command=self.export_excel).grid(row=0, column=1, padx=10)

    def load_configs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        configs = self.service.fine_repo.get_all_configs()
        for row in configs:
            self.tree.insert('', tk.END, values=(row[0], row[1], row[2]))

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            self.val_entry.delete(0, tk.END)
            self.val_entry.insert(0, item['values'][1])

    def update_config(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn cấu hình cần cập nhật.")
            return
        key = self.tree.item(selected[0])['values'][0]
        new_val = self.val_entry.get()
        
        try:
            self.service.fine_repo.update_config(key, new_val, self.admin_id)
            messagebox.showinfo("Thành công", f"Đã cập nhật {key} thành {new_val}")
            self.load_configs()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def export_excel(self):
        success, msg = self.service.export_top_books_excel()
        if success:
            messagebox.showinfo("Thành công", msg)
        else:
            messagebox.showerror("Lỗi", msg)