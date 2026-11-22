import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from typing import Callable, Optional

from src.models.user import User
from src.services.auth_service import AuthService, UserService
from src.services.catalog_service import CatalogService


class AuthCatalogView(tk.Frame):
    #Giao diện Phân hệ Tài khoản, Phân quyền & Danh mục sách (Người 1).

    def __init__(
        self,
        parent,
        auth_service: Optional[AuthService] = None,
        user_service: Optional[UserService] = None,
        catalog_service: Optional[CatalogService] = None,
        on_auth_changed: Optional[Callable[[Optional[User]], None]] = None,
    ):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()
        self.user_service = user_service or UserService()
        self.catalog_service = catalog_service or CatalogService()
        self.on_auth_changed = on_auth_changed

        self._setup_header()
        self._setup_tabs()
        self._refresh_role_access()
        self._load_categories()
        self._search_opac()

    # THANH TRẠNG THÁI ĐĂNG NHẬP PHÍA TRÊN
    def _setup_header(self):
        header = tk.Frame(self, bg="#2C3E50", padx=12, pady=8)
        header.pack(fill="x")

        tk.Label(
            header,
            text="LMS - TÀI KHOẢN & DANH MỤC SÁCH",
            font=("Calibri", 14, "bold"),
            bg="#2C3E50",
            fg="white",
        ).pack(side="left")

        self.lbl_session = tk.Label(
            header,
            text="Chế độ: Khách (Guest)",
            font=("Calibri", 11),
            bg="#2C3E50",
            fg="#ECF0F1",
        )
        self.lbl_session.pack(side="right", padx=(0, 10))

        self.btn_logout = tk.Button(
            header,
            text="Đăng xuất",
            bg="#E74C3C",
            fg="white",
            command=self._handle_logout,
        )

    def _setup_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_account = tk.Frame(self.notebook)
        self.tab_opac = tk.Frame(self.notebook)
        self.tab_catalog_mgr = tk.Frame(self.notebook)
        self.tab_user_mgr = tk.Frame(self.notebook)

        self.notebook.add(self.tab_account, text="1. Tài khoản & Hồ sơ")
        self.notebook.add(self.tab_opac, text="2. Tra cứu Sách (OPAC)")
        self.notebook.add(self.tab_catalog_mgr, text="3. Quản lý Kho Sách")
        self.notebook.add(self.tab_user_mgr, text="4. Quản trị User (Admin)")

        self._build_account_tab()
        self._build_opac_tab()
        self._build_catalog_manager_tab()
        self._build_user_manager_tab()

    def _refresh_role_access(self):
        #Cập nhật hiển thị tab & trạng thái theo phân quyền RBAC.
        user = self.auth_service.current_user
        if not user:
            self.lbl_session.config(text="Chế độ: Khách (Guest)")
            self.btn_logout.pack_forget()
            self.profile_frame.pack_forget()
            self.guest_auth_frame.pack(fill="both", expand=True, padx=15, pady=10)
            self.notebook.tab(self.tab_catalog_mgr, state="disabled")
            self.notebook.tab(self.tab_user_mgr, state="disabled")
        else:
            self.lbl_session.config(text=f"Xin chào: {user.full_name} [{user.role}] - Thẻ: {user.card_number}")
            self.btn_logout.pack(side="right", padx=5)
            self.guest_auth_frame.pack_forget()
            self._populate_profile_form(user)
            self.profile_frame.pack(fill="both", expand=True, padx=15, pady=10)

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

    # TAB 1: ĐĂNG NHẬP, ĐĂNG KÝ, QUÊN MẬT KHẨU & HỒ SƠ (UC-04..07)
    def _build_account_tab(self):
        # --- Khung dành cho Guest (Login + Register) ---
        self.guest_auth_frame = tk.Frame(self.tab_account)

        # Cột trái: Đăng nhập (SCR-01)
        login_box = tk.LabelFrame(self.guest_auth_frame, text="Đăng nhập Hệ thống (UC-04)", padx=15, pady=15)
        login_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(login_box, text="Email hoặc Mã thẻ:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_login_id = tk.Entry(login_box, width=30)
        self.ent_login_id.grid(row=0, column=1, pady=5)

        tk.Label(login_box, text="Mật khẩu:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_login_pwd = tk.Entry(login_box, width=30, show="*")
        self.ent_login_pwd.grid(row=1, column=1, pady=5)

        btn_row = tk.Frame(login_box)
        btn_row.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(btn_row, text="Đăng nhập", bg="#27AE60", fg="white", width=14, command=self._handle_login).pack(side="left", padx=5)
        tk.Button(btn_row, text="Quên mật khẩu?", command=self._handle_forgot_password).pack(side="left", padx=5)

        # Cột phải: Đăng ký thẻ độc giả (UC-05)
        reg_box = tk.LabelFrame(self.guest_auth_frame, text="Đăng ký Thẻ Độc Giả Mới (UC-05)", padx=15, pady=15)
        reg_box.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

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
            tk.Label(reg_box, text=label).grid(row=idx, column=0, sticky="w", pady=4)
            ent = tk.Entry(reg_box, width=32, show="*" if is_pwd else "")
            ent.grid(row=idx, column=1, pady=4)
            self.reg_entries[key] = ent

        tk.Button(
            reg_box, text="Đăng ký Thẻ", bg="#2980B9", fg="white", width=18, command=self._handle_register
        ).grid(row=len(fields), column=1, sticky="e", pady=10)

        # --- Khung Hồ sơ cá nhân khi đã đăng nhập (UC-06 / SCR-05) ---
        self.profile_frame = tk.LabelFrame(self.tab_account, text="Hồ sơ Cá nhân (UC-06)", padx=20, pady=15)

        tk.Label(self.profile_frame, text="Mã thẻ thư viện:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_prof_card = tk.Entry(self.profile_frame, width=35, state="readonly")
        self.ent_prof_card.grid(row=0, column=1, pady=5)

        tk.Label(self.profile_frame, text="Email (chỉ đọc):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_prof_email = tk.Entry(self.profile_frame, width=35, state="readonly")
        self.ent_prof_email.grid(row=1, column=1, pady=5)

        tk.Label(self.profile_frame, text="CCCD / MSSV (chỉ đọc):").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_prof_cccd = tk.Entry(self.profile_frame, width=35, state="readonly")
        self.ent_prof_cccd.grid(row=2, column=1, pady=5)

        tk.Label(self.profile_frame, text="Họ và tên:").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_prof_name = tk.Entry(self.profile_frame, width=35)
        self.ent_prof_name.grid(row=3, column=1, pady=5)

        tk.Label(self.profile_frame, text="Số điện thoại:").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_prof_phone = tk.Entry(self.profile_frame, width=35)
        self.ent_prof_phone.grid(row=4, column=1, pady=5)

        tk.Label(self.profile_frame, text="Địa chỉ:").grid(row=5, column=0, sticky="w", pady=5)
        self.ent_prof_addr = tk.Entry(self.profile_frame, width=35)
        self.ent_prof_addr.grid(row=5, column=1, pady=5)

        tk.Label(self.profile_frame, text="Mật khẩu mới (bỏ trống nếu giữ nguyên):").grid(row=6, column=0, sticky="w", pady=5)
        self.ent_prof_pwd = tk.Entry(self.profile_frame, width=35, show="*")
        self.ent_prof_pwd.grid(row=6, column=1, pady=5)

        tk.Button(
            self.profile_frame, text="Lưu thay đổi", bg="#27AE60", fg="white", width=18, command=self._handle_update_profile
        ).grid(row=7, column=1, sticky="e", pady=12)

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
            messagebox.showinfo(
                "Đăng ký thành công",
                f"Tạo tài khoản độc giả thành công!\nMã thẻ thư viện của bạn là: {member.card_number}",
            )
        except Exception as e:
            messagebox.showerror("Lỗi Đăng ký", str(e))

    def _handle_forgot_password(self):
        email = simpledialog.askstring("Quên mật khẩu (UC-07)", "Nhập Email đã đăng ký của bạn:")
        if not email:
            return
        try:
            temp_pwd = self.auth_service.reset_password(email)
            messagebox.showinfo(
                "Khôi phục mật khẩu",
                f"Mật khẩu tạm mới của bạn là: {temp_pwd}\nVui lòng đăng nhập và đổi lại mật khẩu.",
            )
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

    # TAB 2: TRA CỨU & LỌC DANH MỤC SÁCH OPAC (UC-01, UC-02 / SCR-02)
    def _build_opac_tab(self):
        filter_bar = tk.Frame(self.tab_opac, pady=8)
        filter_bar.pack(fill="x", padx=10)

        tk.Label(filter_bar, text="Từ khóa (Tên/Tác giả/ISBN):").grid(row=0, column=0, padx=4)
        self.ent_opac_kw = tk.Entry(filter_bar, width=28)
        self.ent_opac_kw.grid(row=0, column=1, padx=4)

        tk.Label(filter_bar, text="Thể loại:").grid(row=0, column=2, padx=4)
        self.cmb_opac_cat = ttk.Combobox(filter_bar, state="readonly", width=22)
        self.cmb_opac_cat.grid(row=0, column=3, padx=4)

        tk.Label(filter_bar, text="Sắp xếp:").grid(row=0, column=4, padx=4)
        self.cmb_opac_sort = ttk.Combobox(
            filter_bar,
            state="readonly",
            width=18,
            values=["Tên sách (A-Z)", "Năm XB (Mới nhất)", "Mượn nhiều nhất"],
        )
        self.cmb_opac_sort.current(0)
        self.cmb_opac_sort.grid(row=0, column=5, padx=4)

        tk.Button(filter_bar, text="Tìm kiếm", bg="#2980B9", fg="white", command=self._search_opac).grid(row=0, column=6, padx=6)
        tk.Button(filter_bar, text="Xem vị trí kệ", command=self._show_book_copies_popup).grid(row=0, column=7, padx=4)

        cols = ("id", "isbn", "title", "author", "category", "year", "avail")
        self.tree_opac = ttk.Treeview(self.tab_opac, columns=cols, show="headings", height=16)
        headings = [
            ("id", "ID", 45),
            ("isbn", "ISBN", 120),
            ("title", "Tên đầu sách", 260),
            ("author", "Tác giả", 170),
            ("category", "Thể loại", 130),
            ("year", "Năm XB", 70),
            ("avail", "Sẵn có / Tổng", 100),
        ]
        for col, text, w in headings:
            self.tree_opac.heading(col, text=text)
            self.tree_opac.column(col, width=w, anchor="center" if col in ("id", "year", "avail") else "w")
        self.tree_opac.pack(fill="both", expand=True, padx=10, pady=5)

    def _load_categories(self):
        self.category_map = {"Tất cả thể loại": None}
        try:
            for cid, cname in self.catalog_service.get_categories():
                self.category_map[cname] = cid
        except Exception:
            pass
        self.cmb_opac_cat["values"] = list(self.category_map.keys())
        self.cmb_opac_cat.current(0)

    def _search_opac(self):
        for item in self.tree_opac.get_children():
            self.tree_opac.delete(item)

        sort_choice = self.cmb_opac_sort.get()
        sort_by, sort_dir = "title", "ASC"
        if "Năm" in sort_choice:
            sort_by, sort_dir = "year", "DESC"
        elif "Mượn" in sort_choice:
            sort_by, sort_dir = "popularity", "DESC"

        cat_id = self.category_map.get(self.cmb_opac_cat.get())
        try:
            books, _ = self.catalog_service.browse_or_search(
                keyword=self.ent_opac_kw.get(),
                category_id=cat_id,
                sort_by=sort_by,
                sort_dir=sort_dir,
            )
            for b in books:
                self.tree_opac.insert(
                    "",
                    tk.END,
                    values=(
                        b.book_id,
                        b.isbn,
                        b.title,
                        b.author_names or "",
                        b.category_name or "",
                        b.publication_year or "",
                        f"{b.available_copies} / {b.total_copies}",
                    ),
                )
        except Exception as e:
            messagebox.showerror("Lỗi Tra cứu OPAC", str(e))

    def _show_book_copies_popup(self):
        sel = self.tree_opac.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một đầu sách trong bảng.")
            return
        book_id = int(self.tree_opac.item(sel[0])["values"][0])
        try:
            detail = self.catalog_service.get_book_details(book_id)
            if not detail:
                return
            lines = [f"Đầu sách: {detail.title} (ISBN: {detail.isbn})", f"Tóm tắt: {detail.summary or 'Không có'}\n", "Danh sách bản sao vật lý:"]
            if not detail.copies:
                lines.append(" - Chưa có bản sao nào trong kho.")
            for c in detail.copies:
                lines.append(f" • Barcode: {c.barcode} | Vị trí: {c.full_location} | Trạng thái: {c.status}")
            messagebox.showinfo("Chi tiết Sách & Vị trí kệ", "\n".join(lines))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    # TAB 3: QUẢN LÝ DANH MỤC & KHO BẢN SAO (UC-03 / SCR-06)
    def _build_catalog_manager_tab(self):
        form = tk.LabelFrame(self.tab_catalog_mgr, text="Thêm / Cập nhật Đầu sách (UC-03)", padx=10, pady=8)
        form.pack(fill="x", padx=10, pady=6)

        tk.Label(form, text="ISBN (*):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.ent_mgr_isbn = tk.Entry(form, width=20)
        self.ent_mgr_isbn.grid(row=0, column=1, padx=4, pady=3)

        tk.Label(form, text="Tên sách (*):").grid(row=0, column=2, sticky="w", padx=4, pady=3)
        self.ent_mgr_title = tk.Entry(form, width=32)
        self.ent_mgr_title.grid(row=0, column=3, padx=4, pady=3)

        tk.Label(form, text="Tác giả (cách dấu phẩy):").grid(row=0, column=4, sticky="w", padx=4, pady=3)
        self.ent_mgr_authors = tk.Entry(form, width=25)
        self.ent_mgr_authors.grid(row=0, column=5, padx=4, pady=3)

        tk.Label(form, text="Thể loại:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.ent_mgr_cat = tk.Entry(form, width=20)
        self.ent_mgr_cat.grid(row=1, column=1, padx=4, pady=3)

        tk.Label(form, text="Nhà xuất bản:").grid(row=1, column=2, sticky="w", padx=4, pady=3)
        self.ent_mgr_pub = tk.Entry(form, width=32)
        self.ent_mgr_pub.grid(row=1, column=3, padx=4, pady=3)

        tk.Label(form, text="Năm XB / Giá bìa:").grid(row=1, column=4, sticky="w", padx=4, pady=3)
        sub_num = tk.Frame(form)
        sub_num.grid(row=1, column=5, sticky="w")
        self.ent_mgr_year = tk.Entry(sub_num, width=8)
        self.ent_mgr_year.pack(side="left", padx=2)
        self.ent_mgr_price = tk.Entry(sub_num, width=14)
        self.ent_mgr_price.pack(side="left", padx=2)

        btns = tk.Frame(form)
        btns.grid(row=2, column=0, columnspan=6, pady=6)
        tk.Button(btns, text="+ Thêm Đầu Sách", bg="#27AE60", fg="white", command=self._handle_add_book).pack(side="left", padx=5)
        tk.Button(btns, text="Cập nhật Đầu Sách Đang Chọn", bg="#2980B9", fg="white", command=self._handle_update_book).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa Mềm Đầu Sách", bg="#E74C3C", fg="white", command=self._handle_soft_delete_book).pack(side="left", padx=5)
        tk.Button(btns, text="+ Thêm Bản Sao Vật Lý (Barcode)", bg="#8E44AD", fg="white", command=self._handle_add_copy_popup).pack(side="left", padx=5)

        cols = ("id", "isbn", "title", "author", "category", "publisher", "year", "price", "copies")
        self.tree_mgr_books = ttk.Treeview(self.tab_catalog_mgr, columns=cols, show="headings", height=13)
        for col, text, w in [
            ("id", "ID", 40),
            ("isbn", "ISBN", 110),
            ("title", "Tên sách", 220),
            ("author", "Tác giả", 150),
            ("category", "Thể loại", 110),
            ("publisher", "NXB", 110),
            ("year", "Năm", 55),
            ("price", "Giá bìa", 85),
            ("copies", "Sẵn/Tổng", 75),
        ]:
            self.tree_mgr_books.heading(col, text=text)
            self.tree_mgr_books.column(col, width=w)
        self.tree_mgr_books.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree_mgr_books.bind("<<TreeviewSelect>>", self._on_select_mgr_book)

    def _load_mgr_books(self):
        for item in self.tree_mgr_books.get_children():
            self.tree_mgr_books.delete(item)
        try:
            books, _ = self.catalog_service.browse_or_search(page_size=100)
            for b in books:
                self.tree_mgr_books.insert(
                    "",
                    tk.END,
                    values=(
                        b.book_id,
                        b.isbn,
                        b.title,
                        b.author_names or "",
                        b.category_name or "",
                        b.publisher_name or "",
                        b.publication_year or "",
                        str(b.cover_price),
                        f"{b.available_copies}/{b.total_copies}",
                    ),
                )
        except Exception as e:
            messagebox.showerror("Lỗi tải danh mục", str(e))

    def _on_select_mgr_book(self, _event):
        sel = self.tree_mgr_books.selection()
        if not sel:
            return
        vals = self.tree_mgr_books.item(sel[0])["values"]
        mapping = [
            (self.ent_mgr_isbn, vals[1]),
            (self.ent_mgr_title, vals[2]),
            (self.ent_mgr_authors, vals[3]),
            (self.ent_mgr_cat, vals[4]),
            (self.ent_mgr_pub, vals[5]),
            (self.ent_mgr_year, vals[6]),
            (self.ent_mgr_price, vals[7]),
        ]
        for ent, val in mapping:
            ent.delete(0, tk.END)
            ent.insert(0, str(val) if val is not None else "")

    def _handle_add_book(self):
        try:
            year = int(self.ent_mgr_year.get()) if self.ent_mgr_year.get().strip() else None
            price = Decimal(self.ent_mgr_price.get() or "0")
            self.catalog_service.add_book_title(
                actor=self.auth_service.current_user,
                isbn=self.ent_mgr_isbn.get(),
                title=self.ent_mgr_title.get(),
                author_names_csv=self.ent_mgr_authors.get(),
                category_name=self.ent_mgr_cat.get(),
                publisher_name=self.ent_mgr_pub.get(),
                publication_year=year,
                cover_price=price,
            )
            self._load_mgr_books()
            self._load_categories()
            self._search_opac()
            messagebox.showinfo("Thành công", "Đã thêm đầu sách mới.")
        except Exception as e:
            messagebox.showerror("Lỗi Thêm Sách", str(e))

    def _handle_update_book(self):
        sel = self.tree_mgr_books.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn đầu sách cần sửa.")
            return
        book_id = int(self.tree_mgr_books.item(sel[0])["values"][0])
        try:
            year = int(self.ent_mgr_year.get()) if self.ent_mgr_year.get().strip() else None
            price = Decimal(self.ent_mgr_price.get() or "0")
            self.catalog_service.update_book_title(
                actor=self.auth_service.current_user,
                book_id=book_id,
                isbn=self.ent_mgr_isbn.get(),
                title=self.ent_mgr_title.get(),
                author_names_csv=self.ent_mgr_authors.get(),
                category_name=self.ent_mgr_cat.get(),
                publisher_name=self.ent_mgr_pub.get(),
                publication_year=year,
                cover_price=price,
            )
            self._load_mgr_books()
            self._search_opac()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin đầu sách.")
        except Exception as e:
            messagebox.showerror("Lỗi Cập nhật", str(e))

    def _handle_soft_delete_book(self):
        sel = self.tree_mgr_books.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn đầu sách cần xóa.")
            return
        book_id = int(self.tree_mgr_books.item(sel[0])["values"][0])
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa mềm đầu sách này khỏi danh mục OPAC?"):
            return
        try:
            self.catalog_service.soft_delete_book_title(self.auth_service.current_user, book_id)
            self._load_mgr_books()
            self._search_opac()
            messagebox.showinfo("Thành công", "Đã ẩn đầu sách (Soft-Delete).")
        except Exception as e:
            messagebox.showerror("Không thể xóa", str(e))

    def _handle_add_copy_popup(self):
        sel = self.tree_mgr_books.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn đầu sách trước khi thêm bản sao.")
            return
        book_id = int(self.tree_mgr_books.item(sel[0])["values"][0])
        barcode = simpledialog.askstring("Thêm Bản Sao (UC-03)", "Nhập mã vạch (Barcode) duy nhất:")
        if not barcode:
            return
        zone = simpledialog.askstring("Vị trí kệ", "Khu vực (Zone, VD: Khu A):") or ""
        shelf = simpledialog.askstring("Vị trí kệ", "Kệ số (Shelf, VD: Kệ 01):") or ""
        floor = simpledialog.askstring("Vị trí kệ", "Tầng (Floor, VD: Tầng 2):") or ""
        try:
            self.catalog_service.add_physical_copy(self.auth_service.current_user, book_id, barcode, zone, shelf, floor)
            self._load_mgr_books()
            self._search_opac()
            messagebox.showinfo("Thành công", f"Đã nhập kho bản sao {barcode}.")
        except Exception as e:
            messagebox.showerror("Lỗi Thêm Bản Sao", str(e))

    # TAB 4: QUẢN TRỊ NGƯỜI DÙNG & PHÂN QUYỀN (UC-12 - ADMIN)
    def _build_user_manager_tab(self):
        top = tk.Frame(self.tab_user_mgr, pady=8)
        top.pack(fill="x", padx=10)

        tk.Label(top, text="Lọc Role:").pack(side="left", padx=4)
        self.cmb_user_role = ttk.Combobox(top, state="readonly", width=12, values=["ALL", "MEMBER", "LIBRARIAN", "ADMIN"])
        self.cmb_user_role.current(0)
        self.cmb_user_role.pack(side="left", padx=4)

        tk.Label(top, text="Trạng thái:").pack(side="left", padx=4)
        self.cmb_user_status = ttk.Combobox(top, state="readonly", width=12, values=["ALL", "ACTIVE", "LOCKED", "EXPIRED"])
        self.cmb_user_status.current(0)
        self.cmb_user_status.pack(side="left", padx=4)

        tk.Button(top, text="Lọc danh sách", command=self._load_users_grid).pack(side="left", padx=6)
        tk.Button(top, text="Khóa / Mở khóa tài khoản", bg="#E67E22", fg="white", command=self._toggle_lock_user).pack(side="left", padx=6)
        tk.Button(top, text="Cấp quyền Thủ thư (LIBRARIAN)", bg="#2980B9", fg="white", command=self._promote_to_librarian).pack(side="left", padx=6)

        cols = ("id", "card", "name", "email", "cccd", "role", "status", "expiry")
        self.tree_users = ttk.Treeview(self.tab_user_mgr, columns=cols, show="headings", height=16)
        for col, text, w in [
            ("id", "ID", 45),
            ("card", "Mã thẻ", 130),
            ("name", "Họ tên", 170),
            ("email", "Email", 180),
            ("cccd", "CCCD/MSSV", 110),
            ("role", "Vai trò", 95),
            ("status", "Trạng thái", 90),
            ("expiry", "Hết hạn thẻ", 100),
        ]:
            self.tree_users.heading(col, text=text)
            self.tree_users.column(col, width=w)
        self.tree_users.pack(fill="both", expand=True, padx=10, pady=5)

    def _load_users_grid(self):
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)
        try:
            users, _ = self.user_service.list_users(
                actor=self.auth_service.current_user,
                role_filter=self.cmb_user_role.get(),
                status_filter=self.cmb_user_status.get(),
                page_size=100,
            )
            for u in users:
                self.tree_users.insert(
                    "",
                    tk.END,
                    values=(
                        u.user_id,
                        u.card_number,
                        u.full_name,
                        u.email,
                        u.identity_number,
                        u.role,
                        u.status,
                        str(u.membership_expiry_date or ""),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Lỗi tải User", str(e))

    def _toggle_lock_user(self):
        sel = self.tree_users.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn tài khoản cần thao tác.")
            return
        vals = self.tree_users.item(sel[0])["values"]
        uid, role, current_status = int(vals[0]), vals[5], vals[6]
        new_status = "ACTIVE" if current_status == "LOCKED" else "LOCKED"
        try:
            self.user_service.update_user_access(self.auth_service.current_user, uid, role, new_status)
            self._load_users_grid()
            messagebox.showinfo("Thành công", f"Đã chuyển trạng thái tài khoản sang {new_status}.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _promote_to_librarian(self):
        sel = self.tree_users.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn tài khoản cần phân quyền.")
            return
        vals = self.tree_users.item(sel[0])["values"]
        uid, current_status = int(vals[0]), vals[6]
        try:
            self.user_service.update_user_access(self.auth_service.current_user, uid, "LIBRARIAN", current_status)
            self._load_users_grid()
            messagebox.showinfo("Thành công", "Đã cập nhật vai trò tài khoản thành LIBRARIAN.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("LMS Group 12 - Auth & Catalog Module")
    root.geometry("1080x620")
    view = AuthCatalogView(root)
    view.pack(fill="both", expand=True)
    root.mainloop()
