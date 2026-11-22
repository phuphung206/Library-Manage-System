import tkinter as tk
from tkinter import ttk
from ttkbootstrap.constants import *
from datetime import datetime

class DashboardView(tk.Frame):
    def __init__(self, parent, bg_color, nav_callback=None, db_conn=None):
        super().__init__(parent, bg=bg_color)
        self.bg_color = bg_color
        self.nav_callback = nav_callback
        self.conn = db_conn  # Nhận kết nối CSDL
        
        # Biến tk.StringVar để tự động cập nhật số liệu KPI khi dữ liệu đổi
        self.kpi_vars = {
            "checked_out": tk.StringVar(value="0"),
            "due_today": tk.StringVar(value="0"),
            "members": tk.StringVar(value="0"),
            "reservations": tk.StringVar(value="0")
        }
        
        self.container = tk.Frame(self, bg=bg_color)
        self.container.pack(fill=BOTH, expand=True, padx=40, pady=40)
        
        self.setup_header()
        self.setup_kpi_cards()
        self.setup_content_lists()
        
        # Chạy hàm truy vấn dữ liệu thực tế
        self.refresh_data()

    def setup_header(self):
        header_frame = tk.Frame(self.container, bg=self.bg_color)
        header_frame.pack(fill=X, pady=(0, 30))
        
        left_header = tk.Frame(header_frame, bg=self.bg_color)
        left_header.pack(side=tk.LEFT)
        
        tk.Label(left_header, text="Overview", font=("Segoe UI", 12), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        tk.Label(left_header, text="Good morning, Phú.", font=("Segoe UI", 28, "bold"), fg="#111827", bg=self.bg_color).pack(anchor="w", pady=(5, 0))
        tk.Label(left_header, text="Here's what's happening across the library today.", font=("Segoe UI", 11), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        
        right_header = tk.Frame(header_frame, bg=self.bg_color)
        right_header.pack(side=tk.RIGHT, anchor="n")
        
        date_str = datetime.now().strftime("%A, %b %d")
        tk.Label(right_header, text=f"🟢 System operational   |   📅 {date_str}", font=("Segoe UI", 10), fg="#6b7280", bg=self.bg_color).pack(side=tk.TOP, anchor="e", pady=(0, 15))
        
        btn_action = tk.Button(
            right_header, 
            text="Open circulation desk", 
            font=("Segoe UI", 10, "bold"), 
            bg="#1a362f", 
            fg="white", 
            padx=15, 
            pady=8, 
            bd=0, 
            cursor="hand2",
            command=lambda: self.nav_callback("circulation") if self.nav_callback else None
        )
        btn_action.pack(side=tk.TOP, anchor="e")

    def setup_kpi_cards(self):
        cards_frame = tk.Frame(self.container, bg=self.bg_color)
        cards_frame.pack(fill=X, pady=(0, 30))
        
        kpis = [
            {"title": "Books checked out", "var": self.kpi_vars["checked_out"], "sub": "Active borrow slips", "icon": "📚", "bg": "#1a362f", "fg": "white", "sub_fg": "#a3b8b1"},
            {"title": "Due / Overdue", "var": self.kpi_vars["due_today"], "sub": "Needs attention", "icon": "⏰", "bg": "white", "fg": "#111827", "sub_fg": "#ef4444"},
            {"title": "Active members", "var": self.kpi_vars["members"], "sub": "Registered readers", "icon": "👥", "bg": "white", "fg": "#111827", "sub_fg": "#6b7280"},
            {"title": "Reservations", "var": self.kpi_vars["reservations"], "sub": "In FIFO queue", "icon": "🔖", "bg": "white", "fg": "#111827", "sub_fg": "#6b7280"}
        ]
        
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1, uniform="card")
            
        for i, kpi in enumerate(kpis):
            border_color = "#1a362f" if i == 0 else "#e5e7eb"
            card_border = tk.Frame(cards_frame, bg=border_color, padx=1, pady=1)
            card_border.grid(row=0, column=i, sticky="nsew", padx=10)
            
            card = tk.Frame(card_border, bg=kpi["bg"], padx=20, pady=20)
            card.pack(fill=BOTH, expand=True)
            
            top_frame = tk.Frame(card, bg=kpi["bg"])
            top_frame.pack(fill=X)
            tk.Label(top_frame, text=kpi["title"], font=("Segoe UI", 10), bg=kpi["bg"], fg=kpi["fg"]).pack(side=tk.LEFT)
            tk.Label(top_frame, text=kpi["icon"], font=("Segoe UI", 14), bg=kpi["bg"], fg=kpi["fg"]).pack(side=tk.RIGHT)
            
            # Gắn biến textvariable thay vì text tĩnh
            tk.Label(card, textvariable=kpi["var"], font=("Segoe UI", 32, "bold"), bg=kpi["bg"], fg=kpi["fg"]).pack(anchor="w", pady=(10, 5))
            tk.Label(card, text=kpi["sub"], font=("Segoe UI", 9), bg=kpi["bg"], fg=kpi["sub_fg"]).pack(anchor="w")

    def setup_content_lists(self):
        list_frame = tk.Frame(self.container, bg=self.bg_color)
        list_frame.pack(fill=BOTH, expand=True)
        
        list_frame.columnconfigure(0, weight=6, uniform="list")
        list_frame.columnconfigure(1, weight=4, uniform="list")
        
        # --- CỘT TRÁI: ATTENTION NEEDED ---
        left_col = tk.Frame(list_frame, bg=self.bg_color)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(10, 20))
        
        tk.Label(left_col, text="ATTENTION NEEDED", font=("Segoe UI", 9, "bold"), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        tk.Label(left_col, text="Loans due soon", font=("Segoe UI", 14, "bold"), fg="#111827", bg=self.bg_color).pack(anchor="w", pady=(0, 15))
        
        self.bg_white_left = tk.Frame(left_col, bg="white", highlightbackground="#e5e7eb", highlightthickness=1)
        self.bg_white_left.pack(fill=X)
        
        # --- CỘT PHẢI: LIVE UPDATES ---
        right_col = tk.Frame(list_frame, bg=self.bg_color)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 10))
        
        tk.Label(right_col, text="LIVE UPDATES", font=("Segoe UI", 9, "bold"), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        tk.Label(right_col, text="Recent activity", font=("Segoe UI", 14, "bold"), fg="#111827", bg=self.bg_color).pack(anchor="w", pady=(0, 15))
        
        self.bg_white_right = tk.Frame(right_col, bg="white", highlightbackground="#e5e7eb", highlightthickness=1)
        self.bg_white_right.pack(fill=BOTH, expand=True)

    def refresh_data(self):
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            
            # 1. CẬP NHẬT CÁC THẺ KPI
            # Sách đang được mượn
            cursor.execute("SELECT COUNT(*) FROM BORROW_SLIP WHERE Status = 'BORROWED' AND ActualReturnDate IS NULL")
            self.kpi_vars["checked_out"].set(str(cursor.fetchone()[0] or 0))
            
            # Sách quá hạn hoặc tới hạn hôm nay
            cursor.execute("SELECT COUNT(*) FROM BORROW_SLIP WHERE (Status = 'OVERDUE' OR DueDate <= GETDATE()) AND ActualReturnDate IS NULL")
            self.kpi_vars["due_today"].set(str(cursor.fetchone()[0] or 0))
            
            # Hàng đợi đặt trước
            cursor.execute("SELECT COUNT(*) FROM RESERVATION WHERE Status IN ('WAITING', 'READY')")
            self.kpi_vars["reservations"].set(str(cursor.fetchone()[0] or 0))
            
            # Thành viên (thử query nếu có bảng users)
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'ACTIVE'")
                self.kpi_vars["members"].set(str(cursor.fetchone()[0] or 0))
            except:
                pass
            
            # 2. CẬP NHẬT DANH SÁCH BÊN TRÁI (Loans due soon)
            for widget in self.bg_white_left.winfo_children():
                widget.destroy()
                
            cursor.execute('''
                SELECT TOP 3 BorrowSlipID, ReaderID, DueDate, Status 
                FROM BORROW_SLIP 
                WHERE ActualReturnDate IS NULL 
                ORDER BY DueDate ASC
            ''')
            loans = cursor.fetchall()
            
            if not loans:
                tk.Label(self.bg_white_left, text="No upcoming due loans.", font=("Segoe UI", 10), bg="white", fg="#6b7280", pady=20).pack()
            else:
                for i, r in enumerate(loans):
                    slip_id, reader_id, due, status = r
                    due_str = due.strftime("%b %d") if hasattr(due, 'strftime') else str(due)
                    color = "#ef4444" if status == "OVERDUE" else "#f59e0b"
                    
                    row = tk.Frame(self.bg_white_left, bg="white", pady=15, padx=20)
                    row.pack(fill=X)
                    
                    tk.Label(row, text="📘", font=("Segoe UI", 16), bg="white").pack(side=tk.LEFT, padx=(0, 15))
                    
                    info = tk.Frame(row, bg="white")
                    info.pack(side=tk.LEFT)
                    tk.Label(info, text=f"Borrow Slip #{slip_id}", font=("Segoe UI", 11, "bold"), bg="white", fg="#111827").pack(anchor="w")
                    tk.Label(info, text=f"Reader ID: {reader_id}", font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w")
                    
                    badge = tk.Frame(row, bg=color, padx=10, pady=2)
                    badge.pack(side=tk.RIGHT, padx=15)
                    tk.Label(badge, text=f"{due_str} ({status})", font=("Segoe UI", 9, "bold"), bg=color, fg="white").pack()

                    if i < len(loans) - 1:
                        tk.Frame(self.bg_white_left, bg="#f3f4f6", height=1).pack(fill=X, padx=20)
                        
            # 3. CẬP NHẬT DANH SÁCH BÊN PHẢI (Recent activity)
            for widget in self.bg_white_right.winfo_children():
                widget.destroy()
                
            cursor.execute('''
                SELECT TOP 4 BorrowSlipID, ReaderID, BorrowDate, Status 
                FROM BORROW_SLIP 
                ORDER BY BorrowDate DESC
            ''')
            activities = cursor.fetchall()
            
            if not activities:
                tk.Label(self.bg_white_right, text="No recent activities.", font=("Segoe UI", 10), bg="white", fg="#6b7280", pady=20).pack()
            else:
                for i, r in enumerate(activities):
                    slip_id, reader_id, b_date, status = r
                    date_str = b_date.strftime("%Y-%m-%d") if hasattr(b_date, 'strftime') else str(b_date)
                    icon = "📗" if status == 'RETURNED' else "📚"
                    
                    row = tk.Frame(self.bg_white_right, bg="white", pady=15, padx=20)
                    row.pack(fill=X)
                    
                    tk.Label(row, text=icon, font=("Segoe UI", 14), bg="white").pack(side=tk.LEFT, padx=(0, 15))
                    
                    info = tk.Frame(row, bg="white")
                    info.pack(side=tk.LEFT)
                    tk.Label(info, text=f"Slip #{slip_id} ({status})", font=("Segoe UI", 10, "bold"), bg="white", fg="#111827").pack(anchor="w")
                    tk.Label(info, text=f"Reader ID: {reader_id} - {date_str}", font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w")

        except Exception as e:
            print("Lỗi load dữ liệu Dashboard:", e)
