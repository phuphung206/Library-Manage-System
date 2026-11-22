import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from datetime import date
from typing import Callable, Optional

from src.models.user import User, Admin, Librarian, Member
from src.models.book import BookTitle, BookCopy
from src.services.auth_service import AuthService, UserService
from src.services.catalog_service import CatalogService


class AuthCatalogView(tk.Frame):
    """Giao diện Phân hệ Tài khoản, Phân quyền & Danh mục sách (Tương thích MainWindow Arcadia)."""

    BG_PRIMARY = "#1a362f"
    BG_HOVER = "#234940"
    BG_MAIN = "#f4f7f6"
    ACCENT_GREEN = "#1e7e5c"
    ACCENT_BLUE = "#2563eb"
    ACCENT_RED = "#dc2626"
    ACCENT_ORANGE = "#d97706"
    ACCENT_PURPLE = "#6d28d9"

    def __init__(
        self,
        parent,
        catalog_service: Optional[CatalogService] = None,
        auth_service: Optional[AuthService] = None,
        user_service: Optional[UserService] = None,
        on_auth_changed: Optional[Callable[[Optional[User]], None]] = None,
        default_tab: int = 1,
    ):
        super().__init__(parent, bg=self.BG_MAIN)

        # Hỗ trợ linh hoạt tham số truyền từ MainWindow(parent, catalog_service)
        if isinstance(catalog_service, AuthService):
            auth_service = catalog_service
            catalog_service = None

        self.catalog_service = catalog_service or CatalogService()
        self.auth_service = auth_service or AuthService()
        self.user_service = user_service or UserService()
        self.on_auth_changed = on_auth_changed

        # Giả lập phiên đăng nhập Head Librarian / Admin khớp với MainWindow để demo mượt mà
        if not self.auth_service.current_user:
            self.auth_service.current_user = Admin(
                user_id=1,
                card_number="LIB-2026-000001",
                full_name="Phùng Gia Phú",
                email="admin@library.edu.vn",
                password_hash="",
                identity_number="079200000001",
                phone="0901234567",
                address="TP. Hồ Chí Minh",
                status="ACTIVE",
                membership_expiry_date=date(2028, 12, 31),
            )

        self._setup_header()
        self._setup_tabs()
        self._refresh_role_access()
        self._load_categories()
        self._search_opac()

        if 0 <= default_tab < 4:
            self.notebook.select(default_tab)

    def select_mode(self, mode: str):
        """Chuyển nhanh tab khi bấm 'catalog' hoặc 'members' từ Sidebar."""
        if mode == "members":
            self.notebook.select(self.tab_user_mgr)
        else:
            self.notebook.select(self.tab_opac)

    def _setup_header(self):
        header = tk.Frame(self, bg=self.BG_PRIMARY, padx=16, pady=10)
        header.pack(fill="x")

        tk.Label(
            header,
            text="📖 CATALOG, MEMBERS & AUTHENTICATION (MODULE 1)",
            font=("Segoe UI", 13, "bold"),
            bg=self.BG_PRIMARY,
            fg="white",
        ).pack(side="left")

        right_box = tk.Frame(header, bg=self.BG_PRIMARY)
        right_box.pack(side="right")

        self.lbl_session = tk.Label(
            right_box,
            text="Chế độ: Khách (Guest)",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_PRIMARY,
            fg="#a7f3d0",
        )
        self.lbl_session.pack(side="left", padx=(0, 12))

        self.btn_logout = tk.Button(
            right_box,
            text="Đăng xuất (Test Guest)",
            font=("Segoe UI", 9, "bold"),
            bg=self.ACCENT_RED,
            fg="white",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._handle_logout,
        )

    def _setup_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=12)

        self.tab_account = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_opac = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_catalog_mgr = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_user_mgr = tk.Frame(self.notebook, bg=self.BG_MAIN)

        self.notebook.add(self.tab_account, text="1. Tài khoản & Hồ sơ (UC-04..07)")
        self.notebook.add(self.tab_opac, text="2. Tra cứu Sách OPAC (UC-01..02)")
        self.notebook.add(self.tab_catalog_mgr, text="3. Quản lý Kho Sách (UC-03)")
        self.notebook.add(self.tab_user_mgr, text="4. Quản trị Thành viên & Phân quyền (UC-12)")

        self._build_account_tab()
        self._build_opac_tab()
        self._build_catalog_manager_tab()
        self._build_user_manager_tab()

    def _refresh_role_access(self):
        user = self.auth_service.current_user
        if not user:
            self.lbl_session.config(text="Chế độ: Khách (Guest)", fg="#fde68a")
            self.btn_logout.pack_forget()
            self.profile_frame.pack_forget()
            self.guest_auth_frame.pack(fill="both", expand=True, padx=15, pady=12)
            self.notebook.tab(self.tab_catalog_mgr, state="disabled")
            self.notebook.tab(self.tab_user_mgr, state="disabled")
        else:
            self.lbl_session.config(
                text=f"● {user.full_name} [{user.role}] — Thẻ: {user.card_number}",
                fg="#a7f3d0",
            )
            self.btn_logout.pack(side="left")
            self.guest_auth_frame.pack_forget()
            self._populate_profile_form(user)
            self.profile_frame.pack(fill="both", expand=True, padx=20, pady=15)

            staff_state = "normal" if user.role in ("LIBRARIAN", "ADMIN") else "disabled"
            admin_state = "normal" if user.role == "ADMIN" else "disabled"
            self.notebook.tab(self.tab_catalog_mgr, state=staff_state)
            self.notebook.tab(self.tab_user_mgr, state=admin_state)

            if staff_state == "normal":
                self._load_mgr_books()
            if admin_state == "normal":
                self._load_users_grid()

        if self.on_auth_changed:
            self.on_auth_changed(user)

    # --- TAB 1: TÀI KHOẢN & HỒ SƠ ---
    def _build_account_tab(self):
        self.guest_auth_frame = tk.Frame(self.tab_account, bg=self.BG_MAIN)
        self.guest_auth_frame.columnconfigure(0, weight=1)
        self.guest_auth_frame.columnconfigure(1, weight=1)

        login_box = tk.LabelFrame(
            self.guest_auth_frame,
            text=" Đăng nhập Hệ thống (UC-04) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            padx=20,
            pady=20,
        )
        login_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)

        tk.Label(login_box, text="Email hoặc Mã thẻ:", bg="white").grid(row=0, column=0, sticky="w", pady=6)
        self.ent_login_id = tk.Entry(login_box, width=30)
        self.ent_login_id.grid(row=0, column=1, pady=6, padx=8)

        tk.Label(login_box, text="Mật khẩu:", bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.ent_login_pwd = tk.Entry(login_box, width=30, show="•")
        self.ent_login_pwd.grid(row=1, column=1, pady=6, padx=8)

        btn_row = tk.Frame(login_box, bg="white")
        btn_row.grid(row=2, column=0, columnspan=2, pady=15)
        tk.Button(btn_row, text="Đăng nhập", bg=self.ACCENT_GREEN, fg="white", width=14, bd=0, pady=5, command=self._handle_login).pack(side="left", padx=5)
        tk.Button(btn_row, text="Quên mật khẩu?", bg="#e2e8f0", width=16, bd=0, pady=5, command=self._handle_forgot_password).pack(side="left", padx=5)

        reg_box = tk.LabelFrame(
            self.guest_auth_frame,
            text=" Đăng ký Thẻ Độc Giả Mới (UC-05) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            padx=20,
            pady=20,
        )
        reg_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        fields = [
            ("Họ và tên (*):", "reg_name", False),
            ("Email (*):", "reg_email", False),
            ("CCCD / MSSV (*):", "reg_cccd", False),
            ("Số điện thoại:", "reg_phone", False),
            ("Địa chỉ:", "reg_addr", False),
            ("Mật khẩu (>=6 ký tự) (*):", "reg_pwd", True),
        ]
        self.reg_entries = {}
        for idx, (label, key, is_pwd) in enumerate(fields):
            tk.Label(reg_box, text=label, bg="white").grid(row=idx, column=0, sticky="w", pady=4)
            ent = tk.Entry(reg_box, width=32, show="•" if is_pwd else "")
            ent.grid(row=idx, column=1, pady=4, padx=8)
            self.reg_entries[key] = ent

        tk.Button(
            reg_box, text="Đăng ký Cấp Thẻ", bg=self.ACCENT_BLUE, fg="white", width=18, bd=0, pady=5, command=self._handle_register
        ).grid(row=len(fields), column=1, sticky="e", pady=10)

        self.profile_frame = tk.LabelFrame(
            self.tab_account,
            text=" Hồ sơ Cá nhân Đang Đăng Nhập (UC-06) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            padx=25,
            pady=20,
        )

        prof_rows = [
            ("Mã thẻ thư viện:", "ent_prof_card", True, False),
            ("Email (chỉ đọc):", "ent_prof_email", True, False),
            ("CCCD / MSSV (chỉ đọc):", "ent_prof_cccd", True, False),
            ("Họ và tên:", "ent_prof_name", False, False),
            ("Số điện thoại:", "ent_prof_phone", False, False),
            ("Địa chỉ:", "ent_prof_addr", False, False),
            ("Mật khẩu mới (để trống nếu giữ nguyên):", "ent_prof_pwd", False, True),
        ]
        for idx, (label, attr_name, readonly, is_pwd) in enumerate(prof_rows):
            tk.Label(self.profile_frame, text=label, bg="white").grid(row=idx, column=0, sticky="w", pady=5)
            ent = tk.Entry(
                self.profile_frame,
                width=36,
                state="readonly" if readonly else "normal",
                show="•" if is_pwd else "",
            )
            ent.grid(row=idx, column=1, pady=5, padx=12)
            setattr(self, attr_name, ent)

        tk.Button(
            self.profile_frame, text="Lưu thay đổi", bg=self.ACCENT_GREEN, fg="white", width=18, bd=0, pady=6, command=self._handle_update_profile
        ).grid(row=len(prof_rows), column=1, sticky="e", pady=12)

    def _populate_profile_form(self, user: User):
        for ent, val in [
            (self.ent_prof_card, user.card_number),
            (self.ent_prof_email, user.email),
            (self.ent_prof_cccd, user.identity_number),
        ]:
            ent.config(state="normal")
            ent.delete(0, tk.END)
            ent.insert(0, val or "")
            ent.config(state="readonly")

        self.ent_prof_name.delete(0, tk.END)
        self.ent_prof_name.insert(0, user.full_name or "")
        self.ent_prof_phone.delete(0, tk.END)
        self.ent_prof_phone.insert(0, user.phone or "")
        self.ent_prof_addr.delete(0, tk.END)
        self.ent_prof_addr.insert(0, user.address or "")
        self.ent_prof_pwd.delete(0, tk.END)

    def _handle_login(self):
        try:
            user = self.auth_service.login(self.ent_login_id.get(), self.ent_login_pwd.get())
            self.ent_login_pwd.delete(0, tk.END)
            messagebox.showinfo("Đăng nhập thành công", f"Chào mừng {user.full_name} ({user.role})!")
            self._refresh_role_access()
        except Exception as e:
            messagebox.showerror("Lỗi Đăng nhập", str(e))

    def _handle_logout(self):
        self.auth_service.logout()
        self._refresh_role_access()
        self.notebook.select(self.tab_account)

    def _handle_register(self):
        try:
            member = self.auth_service.register_member(
                full_name=self.reg_entries["reg_name"].get(),
                email=self.reg_entries["reg_email"].get(),
                password=self.reg_entries["reg_pwd"].get(),
                identity_number=self.reg_entries["reg_cccd"].get(),
                phone=self.reg_entries["reg_phone"].get(),
                address=self.reg_entries["reg_addr"].get(),
            )
            for ent in self.reg_entries.values():
                ent.delete(0, tk.END)
            messagebox.showinfo("Đăng ký thành công", f"Mã thẻ thư viện của bạn: {member.card_number}")
        except Exception as e:
            messagebox.showerror("Lỗi Đăng ký", str(e))

    def _handle_forgot_password(self):
        email = simpledialog.askstring("Quên mật khẩu (UC-07)", "Nhập Email đã đăng ký:")
        if not email:
            return
        try:
            temp_pwd = self.auth_service.reset_password(email)
            messagebox.showinfo("Khôi phục mật khẩu", f"Mật khẩu tạm mới: {temp_pwd}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _handle_update_profile(self):
        user = self.auth_service.current_user
        if not user:
            return
        try:
            new_pwd = self.ent_prof_pwd.get().strip() or None
            updated = self.auth_service.update_profile(
                user_id=user.user_id,
                full_name=self.ent_prof_name.get(),
                phone=self.ent_prof_phone.get(),
                address=self.ent_prof_addr.get(),
                new_password=new_pwd,
            )
            self._refresh_role_access()
            messagebox.showinfo("Thành công", f"Đã cập nhật hồ sơ cho {updated.full_name}.")
        except Exception as e:
            messagebox.showerror("Lỗi Cập nhật", str(e))

    # --- TAB 2: TRA CỨU OPAC ---
    def _build_opac_tab(self):
        filter_bar = tk.Frame(self.tab_opac, bg="white", padx=10, pady=10, bd=1, relief="groove")
        filter_bar.pack(fill="x", padx=10, pady=8)

        tk.Label(filter_bar, text="Từ khóa:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=4)
        self.ent_opac_kw = tk.Entry(filter_bar, width=28)
        self.ent_opac_kw.grid(row=0, column=1, padx=4)

        tk.Label(filter_bar, text="Thể loại:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=4)
        self.cmb_opac_cat = ttk.Combobox(filter_bar, state="readonly", width=20)
        self.cmb_opac_cat.grid(row=0, column=3, padx=4)

        tk.Label(filter_bar, text="Sắp xếp:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=4)
        self.cmb_opac_sort = ttk.Combobox(
            filter_bar,
            state="readonly",
            width=18,
            values=["Tên sách (A-Z)", "Năm XB (Mới nhất)", "Mượn nhiều nhất"],
        )
        self.cmb_opac_sort.current(0)
        self.cmb_opac_sort.grid(row=0, column=5, padx=4)

        tk.Button(filter_bar, text="🔍 Tìm kiếm", bg=self.ACCENT_GREEN, fg="white", bd=0, padx=12, pady=4, command=self._search_opac).grid(row=0, column=6, padx=6)
        tk.Button(filter_bar, text="📍 Xem vị trí kệ & Barcode", bg=self.ACCENT_BLUE, fg="white", bd=0, padx=12, pady=4, command=self._show_book_copies_popup).grid(row=0, column=7, padx=4)

        cols = ("id", "isbn", "title", "author", "category", "year", "avail")
        self.tree_opac = ttk.Treeview(self.tab_opac, columns=cols, show="headings", height=16)
        for col, text, w in [
            ("id", "ID", 45),
            ("isbn", "ISBN", 125),
            ("title", "Tên đầu sách", 280),
            ("author", "Tác giả", 180),
            ("category", "Thể loại", 135),
            ("year", "Năm XB", 70),
            ("avail", "Sẵn có /
