import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from datetime import datetime
from tkinter.constants import *

class DashboardView(tk.Frame):
    def __init__(self, parent, bg_color):
        super().__init__(parent, bg=bg_color)
        self.bg_color = bg_color
        
        # Main container với padding
        self.container = tk.Frame(self, bg=bg_color)
        self.container.pack(fill=BOTH, expand=True, padx=40, pady=40)
        
        self.setup_header()
        self.setup_kpi_cards()
        self.setup_content_lists()

    def setup_header(self):
        header_frame = tk.Frame(self.container, bg=self.bg_color)
        header_frame.pack(fill=X, pady=(0, 30))
        
        # Left Header
        left_header = tk.Frame(header_frame, bg=self.bg_color)
        left_header.pack(side=tk.LEFT)
        
        tk.Label(left_header, text="Overview", font=("Segoe UI", 12), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        tk.Label(left_header, text="Good morning, Phú.", font=("Segoe UI", 28, "bold"), fg="#111827", bg=self.bg_color).pack(anchor="w", pady=(5, 0))
        tk.Label(left_header, text="Here's what's happening across the library today.", font=("Segoe UI", 11), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        
        # Right Header
        right_header = tk.Frame(header_frame, bg=self.bg_color)
        right_header.pack(side=tk.RIGHT, anchor="n")
        
        date_str = datetime.now().strftime("%A, %b %d")
        tk.Label(right_header, text=f"🟢 System operational   |   📅 {date_str}", font=("Segoe UI", 10), fg="#6b7280", bg=self.bg_color).pack(side=tk.TOP, anchor="e", pady=(0, 15))
        
        # Action Button
        btn_action = tk.Button(
            right_header, 
            text="Open circulation desk", 
            font=("Segoe UI", 10, "bold"), 
            bg="#1a362f", 
            fg="white", 
            padx=15, 
            pady=8, 
            bd=0, 
            cursor="hand2"
        )
        btn_action.pack(side=tk.TOP, anchor="e")

    def setup_kpi_cards(self):
        cards_frame = tk.Frame(self.container, bg=self.bg_color)
        cards_frame.pack(fill=X, pady=(0, 30))
        
        # Cấu hình 4 thẻ KPI
        kpis = [
            {"title": "Books checked out", "value": "128", "sub": "+12 since yesterday", "icon": "📚", "bg": "#1a362f", "fg": "white", "sub_fg": "#a3b8b1"},
            {"title": "Due today", "value": "24", "sub": "7 reminders pending", "icon": "⏰", "bg": "white", "fg": "#111827", "sub_fg": "#6b7280"},
            {"title": "Active members", "value": "2,846", "sub": "+38 this month", "icon": "👥", "bg": "white", "fg": "#111827", "sub_fg": "#6b7280"},
            {"title": "Reservations", "value": "36", "sub": "8 ready for pickup", "icon": "🔖", "bg": "white", "fg": "#111827", "sub_fg": "#6b7280"}
        ]
        
        # Layout dạng Grid chia đều 4 cột
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1, uniform="card")
            
        for i, kpi in enumerate(kpis):
            # Khung viền ngoài (để tạo cảm giác đổ bóng nhẹ hoặc border)
            border_color = "#1a362f" if i == 0 else "#e5e7eb"
            card_border = tk.Frame(cards_frame, bg=border_color, padx=1, pady=1)
            card_border.grid(row=0, column=i, sticky="nsew", padx=10)
            
            # Nội dung Card
            card = tk.Frame(card_border, bg=kpi["bg"], padx=20, pady=20)
            card.pack(fill=BOTH, expand=True)
            
            top_frame = tk.Frame(card, bg=kpi["bg"])
            top_frame.pack(fill=X)
            tk.Label(top_frame, text=kpi["title"], font=("Segoe UI", 10), bg=kpi["bg"], fg=kpi["fg"]).pack(side=tk.LEFT)
            tk.Label(top_frame, text=kpi["icon"], font=("Segoe UI", 14), bg=kpi["bg"], fg=kpi["fg"]).pack(side=tk.RIGHT)
            
            tk.Label(card, text=kpi["value"], font=("Segoe UI", 32, "bold"), bg=kpi["bg"], fg=kpi["fg"]).pack(anchor="w", pady=(10, 5))
            tk.Label(card, text=kpi["sub"], font=("Segoe UI", 9), bg=kpi["bg"], fg=kpi["sub_fg"]).pack(anchor="w")

    def setup_content_lists(self):
        list_frame = tk.Frame(self.container, bg=self.bg_color)
        list_frame.pack(fill=BOTH, expand=True)
        
        list_frame.columnconfigure(0, weight=6, uniform="list") # Cột trái to hơn
        list_frame.columnconfigure(1, weight=4, uniform="list") # Cột phải nhỏ hơn
        
        # --- CỘT TRÁI: ATTENTION NEEDED ---
        left_col = tk.Frame(list_frame, bg=self.bg_color)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(10, 20))
        
        tk.Label(left_col, text="ATTENTION NEEDED", font=("Segoe UI", 9, "bold"), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        tk.Label(left_col, text="Loans due soon", font=("Segoe UI", 14, "bold"), fg="#111827", bg=self.bg_color).pack(anchor="w", pady=(0, 15))
        
        loans = [
            ("Introduction to Algorithms", "Sofia Perez - #M-0382", "Today", "#ef4444"),
            ("Thinking, Fast and Slow", "Minh Tran - #M-0431", "Tomorrow", "#f59e0b"),
            ("The Pragmatic Programmer", "Alex Morgan - #M-0894", "May 24", "#6b7280")
        ]
        
        # Khung trắng chứa danh sách
        bg_white_left = tk.Frame(left_col, bg="white", highlightbackground="#e5e7eb", highlightthickness=1)
        bg_white_left.pack(fill=X)
        
        for i, (title, user, due, color) in enumerate(loans):
            row = tk.Frame(bg_white_left, bg="white", pady=15, padx=20)
            row.pack(fill=X)
            
            tk.Label(row, text="📘", font=("Segoe UI", 16), bg="white").pack(side=tk.LEFT, padx=(0, 15))
            
            info = tk.Frame(row, bg="white")
            info.pack(side=tk.LEFT)
            tk.Label(info, text=title, font=("Segoe UI", 11, "bold"), bg="white", fg="#111827").pack(anchor="w")
            tk.Label(info, text=user, font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w")
            
            # Nút mũi tên và Badge
            tk.Label(row, text=">", font=("Segoe UI", 12), bg="white", fg="#9ca3af").pack(side=tk.RIGHT)
            
            # Badge
            badge = tk.Frame(row, bg=color, padx=10, pady=2)
            badge.pack(side=tk.RIGHT, padx=15)
            tk.Label(badge, text=due, font=("Segoe UI", 9, "bold"), bg=color, fg="white").pack()

            if i < len(loans) - 1:
                tk.Frame(bg_white_left, bg="#f3f4f6", height=1).pack(fill=X, padx=20)

        # --- CỘT PHẢI: LIVE UPDATES ---
        right_col = tk.Frame(list_frame, bg=self.bg_color)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 10))
        
        tk.Label(right_col, text="LIVE UPDATES", font=("Segoe UI", 9, "bold"), fg="#6b7280", bg=self.bg_color).pack(anchor="w")
        tk.Label(right_col, text="Recent activity", font=("Segoe UI", 14, "bold"), fg="#111827", bg=self.bg_color).pack(anchor="w", pady=(0, 15))
        
        bg_white_right = tk.Frame(right_col, bg="white", highlightbackground="#e5e7eb", highlightthickness=1)
        bg_white_right.pack(fill=BOTH, expand=True)
        
        activities = [
            ("Book returned", "Dune - 12 mins ago", "📗"),
            ("Hold ready for pickup", "Atomic Habits - 34 mins ago", "📦"),
            ("New member registered", "Jamie Chen - 2 hrs ago", "👤"),
            ("3 books checked out", "Card #M-0954 - 3 hrs ago", "📚")
        ]
        
        for i, (act, sub, icon) in enumerate(activities):
            row = tk.Frame(bg_white_right, bg="white", pady=15, padx=20)
            row.pack(fill=X)
            
            tk.Label(row, text=icon, font=("Segoe UI", 14), bg="white").pack(side=tk.LEFT, padx=(0, 15))
            
            info = tk.Frame(row, bg="white")
            info.pack(side=tk.LEFT)
            tk.Label(info, text=act, font=("Segoe UI", 10, "bold"), bg="white", fg="#111827").pack(anchor="w")
            tk.Label(info, text=sub, font=("Segoe UI", 9), bg="white", fg="#6b7280").pack(anchor="w")
