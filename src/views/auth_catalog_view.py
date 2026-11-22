import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
from typing import Callable, Optional
import pyodbc

# --- MÔ PHỎNG MODEL ---
class User:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
class Admin(User): pass

# --- FILE GIAO DIỆN AUTH & CATALOG ---
class AuthCatalogView(tk.Frame):
    BG_PRIMARY = "#1a362f"
    BG_HOVER = "#234940"
    BG_MAIN = "#f4f7f6"
    ACCENT_GREEN = "#1e7e5c"
    ACCENT_BLUE = "#2563eb"
    ACCENT_RED = "#dc2626"

    def __init__(self, parent, catalog_service=None, auth_service=None, user_service=None, on_auth_changed=None, default_tab=1):
        super().__init__(parent, bg=self.BG_MAIN)
        
        # Nhận kết nối trực tiếp hoặc qua service (ở đây lấy từ parent.conn để demo)
        self.conn = getattr(parent.master, "conn", None) if hasattr(parent, "master") else None
        if not self.conn and hasattr(parent, "master") and hasattr(parent.master.master, "conn"):
             self.conn = parent.master.master.conn
             
        # Mock current user for UI to show
        self.current_user = Admin(
            user_id=1, card_number="LIB-2026-001", full_name="Phùng Gia Phú", 
            email="phu.admin@library.com", role="ADMIN"
        )
        
        self._setup_header()
        self._setup_tabs()
        
        # Tự động nạp dữ liệu khi mở
        self._load_categories()
        self._search_opac()
        self._load_mgr_books()
        self._load_users_grid()
        
        if 0 <= default_tab < 4:
            self.notebook.select(default_tab)

    def select_mode(self, mode: str):
        if mode == "members":
            self.notebook.select(self.tab_user_mgr)
        else:
            self.notebook.select(self.tab_opac)

    def _setup_header(self):
        header = tk.Frame(self, bg=self.BG_PRIMARY, padx=16, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="📖 CATALOG, MEMBERS & AUTHENTICATION", font=("Segoe UI", 13, "bold"), bg=self.BG_PRIMARY, fg="white").pack(side="left")
        right_box = tk.Frame(header, bg=self.BG_PRIMARY)
        right_box.pack(side="right")
        self.lbl_session = tk.Label(right_box, text=f"● {self.current_user.full_name} [{self.current_user.role}] — Card: {self.current_user.card_number}", font=("Segoe UI", 10, "bold"), bg=self.BG_PRIMARY, fg="#a7f3d0")
        self.lbl_session.pack(side="left", padx=(0, 12))

    def _setup_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=12)

        self.tab_account = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_opac = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_catalog_mgr = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_user_mgr = tk.Frame(self.notebook, bg=self.BG_MAIN)

        self.notebook.add(self.tab_account, text="1. Account & Profile (UC-04..07)")
        self.notebook.add(self.tab_opac, text="2. OPAC Search (UC-01..02)")
        self.notebook.add(self.tab_catalog_mgr, text="3. Catalog Management (UC-03)")
        self.notebook.add(self.tab_user_mgr, text="4. Members & Roles (UC-12)")

        self._build_account_tab()
        self._build_opac_tab()
        self._build_catalog_manager_tab()
        self._build_user_manager_tab()

    def _build_account_tab(self):
        tk.Label(self.tab_account, text="Account settings go here.", bg=self.BG_MAIN).pack(pady=20)

    # ==========================================
    # TAB 2: OPAC SEARCH
    # ==========================================
    def _build_opac_tab(self):
        filter_bar = tk.Frame(self.tab_opac, bg="white", padx=10, pady=10, bd=1, relief="groove")
        filter_bar.pack(fill="x", padx=10, pady=8)

        tk.Label(filter_bar, text="Keyword:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=4)
        self.ent_opac_kw = tk.Entry(filter_bar, width=28)
        self.ent_opac_kw.grid(row=0, column=1, padx=4)

        tk.Label(filter_bar, text="Category:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=4)
        self.cmb_opac_cat = ttk.Combobox(filter_bar, state="readonly", width=20)
        self.cmb_opac_cat.grid(row=0, column=3, padx=4)

        tk.Button(filter_bar, text="🔍 Search", bg=self.ACCENT_GREEN, fg="white", bd=0, padx=12, pady=4, command=self._search_opac).grid(row=0, column=6, padx=6)

        cols = ("id", "isbn", "title", "author", "category", "year", "avail")
        self.tree_opac = ttk.Treeview(self.tab_opac, columns=cols, show="headings", height=16)
        for col, text, w in [("id", "ID", 45), ("isbn", "ISBN", 125), ("title", "Book Title", 280), ("author", "Author", 180), ("category", "Category", 135), ("year", "Year", 70), ("avail", "Available / Total", 110)]:
            self.tree_opac.heading(col, text=text)
            self.tree_opac.column(col, width=w, anchor="center" if col in ("id", "year", "avail") else "w")
        self.tree_opac.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_categories(self):
        self.cmb_opac_cat["values"] = ["All", "Khoa học Máy tính", "Tâm lý học", "Kinh tế & Quản trị", "Tiểu thuyết viễn tưởng", "Văn học Việt Nam", "Lịch sử & Khoa học", "Kỹ năng sống"]
        self.cmb_opac_cat.current(0)

    def _search_opac(self):
        for item in self.tree_opac.get_children():
            self.tree_opac.delete(item)
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            kw = self.ent_opac_kw.get().strip()
            cat = self.cmb_opac_cat.get().strip()
            
            query = '''
                SELECT b.title_id, '978-0' + CAST(b.title_id AS VARCHAR), b.title, a.author_name, c.name, b.publish_year,
                (SELECT COUNT(*) FROM book_copies WHERE title_id = b.title_id AND status = 'AVAILABLE') AS avail,
                (SELECT COUNT(*) FROM book_copies WHERE title_id = b.title_id) AS total
                FROM book_titles b
                LEFT JOIN book_authors ba ON b.title_id = ba.title_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN categories c ON b.category_id = c.category_id
                WHERE (b.title LIKE ? OR a.author_name LIKE ?)
            '''
            params = [f"%{kw}%", f"%{kw}%"]
            if cat != "All":
                query += " AND c.name = ?"
                params.append(cat)
                
            cursor.execute(query, params)
            for r in cursor.fetchall():
                avail_str = f"{r[6]} / {r[7]}"
                self.tree_opac.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5], avail_str))
        except Exception as e:
            print("Lỗi Search OPAC:", e)

    # ==========================================
    # TAB 3: CATALOG MANAGEMENT
    # ==========================================
    def _build_catalog_manager_tab(self):
        tk.Label(self.tab_catalog_mgr, text="Catalog & Physical Copy Management (UC-03)", font=("Segoe UI", 12, "bold"), bg=self.BG_MAIN).pack(anchor="w", padx=16, pady=12)
        
        cols = ("id", "title", "publisher", "year", "desc")
        self.tree_cat_mgr = ttk.Treeview(self.tab_catalog_mgr, columns=cols, show="headings", height=15)
        for col, text, w in [("id", "ID", 50), ("title", "Title", 300), ("publisher", "Publisher", 150), ("year", "Year", 80), ("desc", "Description", 350)]:
            self.tree_cat_mgr.heading(col, text=text)
            self.tree_cat_mgr.column(col, width=w)
        self.tree_cat_mgr.pack(fill="both", expand=True, padx=16, pady=10)

    def _load_mgr_books(self):
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT title_id, title, publisher, publish_year, description FROM book_titles")
            for r in cursor.fetchall():
                self.tree_cat_mgr.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4]))
        except: pass

    # ==========================================
    # TAB 4: MEMBERS & ROLES
    # ==========================================
    def _build_user_manager_tab(self):
        tk.Label(self.tab_user_mgr, text="Member & Role Administration (UC-12)", font=("Segoe UI", 12, "bold"), bg=self.BG_MAIN).pack(anchor="w", padx=16, pady=12)
        
        cols = ("id", "card", "name", "email", "role", "status")
        self.tree_users = ttk.Treeview(self.tab_user_mgr, columns=cols, show="headings", height=15)
        for col, text, w in [("id", "ID", 50), ("card", "Card Number", 150), ("name", "Full Name", 200), ("email", "Email", 250), ("role", "Role", 100), ("status", "Status", 100)]:
            self.tree_users.heading(col, text=text)
            self.tree_users.column(col, width=w)
        self.tree_users.pack(fill="both", expand=True, padx=16, pady=10)

    def _load_users_grid(self):
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, card_number, full_name, email, role, status FROM users")
            for r in cursor.fetchall():
                self.tree_users.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5]))
        except: pass
