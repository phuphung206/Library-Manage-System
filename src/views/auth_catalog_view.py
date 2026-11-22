import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
from typing import Callable, Optional

from src.models.user import User, Admin
from src.services.auth_service import AuthService, UserService
from src.services.catalog_service import CatalogService


class AuthCatalogView(tk.Frame):
    """Account, Authorization & Catalog View (Arcadia MainWindow compatible)."""

    BG_PRIMARY = "#1a362f"
    BG_HOVER = "#234940"
    BG_MAIN = "#f4f7f6"
    ACCENT_GREEN = "#1e7e5c"
    ACCENT_BLUE = "#2563eb"
    ACCENT_RED = "#dc2626"

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

        if isinstance(catalog_service, AuthService):
            auth_service = catalog_service
            catalog_service = None

        self.catalog_service = catalog_service or CatalogService()
        self.auth_service = auth_service or AuthService()
        self.user_service = user_service or UserService()
        self.on_auth_changed = on_auth_changed

        if not getattr(self.auth_service, "current_user", None):
            self.auth_service.current_user = Admin(
                user_id=1,
                card_number="LIB-2026-000001",
                full_name="Phùng Gia Phú",
                email="admin@library.edu.vn",
                password_hash="",
                identity_number="079200000001",
                phone="0901234567",
                address="Ho Chi Minh City",
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
        """Switch tab when 'catalog' or 'members' is selected from Sidebar."""
        if mode == "members":
            self.notebook.select(self.tab_user_mgr)
        else:
            self.notebook.select(self.tab_opac)

    def _setup_header(self):
        header = tk.Frame(self, bg=self.BG_PRIMARY, padx=16, pady=10)
        header.pack(fill="x")

        tk.Label(
            header,
            text="📖 CATALOG, MEMBERS & AUTHENTICATION",
            font=("Segoe UI", 13, "bold"),
            bg=self.BG_PRIMARY,
            fg="white",
        ).pack(side="left")

        right_box = tk.Frame(header, bg=self.BG_PRIMARY)
        right_box.pack(side="right")

        self.lbl_session = tk.Label(
            right_box,
            text="Mode: Guest",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_PRIMARY,
            fg="#a7f3d0",
        )
        self.lbl_session.pack(side="left", padx=(0, 12))

        self.btn_logout = tk.Button(
            right_box,
            text="Logout (Test Guest)",
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

        self.notebook.add(self.tab_account, text="1. Account & Profile (UC-04..07)")
        self.notebook.add(self.tab_opac, text="2. OPAC Search (UC-01..02)")
        self.notebook.add(self.tab_catalog_mgr, text="3. Catalog Management (UC-03)")
        self.notebook.add(self.tab_user_mgr, text="4. Members & Roles (UC-12)")

        self._build_account_tab()
        self._build_opac_tab()
        self._build_catalog_manager_tab()
        self._build_user_manager_tab()

    def _refresh_role_access(self):
        user = getattr(self.auth_service, "current_user", None)
        if not user:
            self.lbl_session.config(text="Mode: Guest", fg="#fde68a")
            self.btn_logout.pack_forget()
            self.profile_frame.pack_forget()
            self.guest_auth_frame.pack(fill="both", expand=True, padx=15, pady=12)
            self.notebook.tab(self.tab_catalog_mgr, state="disabled")
            self.notebook.tab(self.tab_user_mgr, state="disabled")
        else:
            self.lbl_session.config(
                text=f"● {user.full_name} [{user.role}] — Card: {user.card_number}",
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

            if staff_state == "normal" and hasattr(self, "_load_mgr_books"):
                self._load_mgr_books()
            if admin_state == "normal" and hasattr(self, "_load_users_grid"):
                self._load_users_grid()

        if self.on_auth_changed:
            self.on_auth_changed(user)

    def _build_account_tab(self):
        self.guest_auth_frame = tk.Frame(self.tab_account, bg=self.BG_MAIN)
        self.guest_auth_frame.columnconfigure(0, weight=1)
        self.guest_auth_frame.columnconfigure(1, weight=1)

        login_box = tk.LabelFrame(
            self.guest_auth_frame,
            text=" Sign In (UC-04) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            padx=20,
            pady=20,
        )
        login_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)

        tk.Label(login_box, text="Email or Card Number:", bg="white").grid(row=0, column=0, sticky="w", pady=6)
        self.ent_login_id = tk.Entry(login_box, width=30)
        self.ent_login_id.grid(row=0, column=1, pady=6, padx=8)

        tk.Label(login_box, text="Password:", bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.ent_login_pwd = tk.Entry(login_box, width=30, show="•")
        self.ent_login_pwd.grid(row=1, column=1, pady=6, padx=8)

        btn_row = tk.Frame(login_box, bg="white")
        btn_row.grid(row=2, column=0, columnspan=2, pady=15)
        tk.Button(
            btn_row, text="Sign In", bg=self.ACCENT_GREEN, fg="white", width=14, bd=0, pady=5, command=self._handle_login
        ).pack(side="left", padx=5)
        tk.Button(
            btn_row, text="Forgot Password?", bg="#e2e8f0", width=16, bd=0, pady=5, command=self._handle_forgot_password
        ).pack(side="left", padx=5)

        reg_box = tk.LabelFrame(
            self.guest_auth_frame,
            text=" Register New Member Card (UC-05) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            padx=20,
            pady=20,
        )
        reg_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        fields = [
            ("Full Name (*):", "reg_name", False),
            ("Email (*):", "reg_email", False),
            ("National ID / Student ID (*):", "reg_cccd", False),
            ("Phone Number:", "reg_phone", False),
            ("Address:", "reg_addr", False),
            ("Password (>=6 chars) (*):", "reg_pwd", True),
        ]
        self.reg_entries = {}
        for idx, (label, key, is_pwd) in enumerate(fields):
            tk.Label(reg_box, text=label, bg="white").grid(row=idx, column=0, sticky="w", pady=4)
            ent = tk.Entry(reg_box, width=32, show="•" if is_pwd else "")
            ent.grid(row=idx, column=1, pady=4, padx=8)
            self.reg_entries[key] = ent

        tk.Button(
            reg_box, text="Register Card", bg=self.ACCENT_BLUE, fg="white", width=18, bd=0, pady=5, command=self._handle_register
        ).grid(row=len(fields), column=1, sticky="e", pady=10)

        self.profile_frame = tk.LabelFrame(
            self.tab_account,
            text=" Active Member Profile (UC-06) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            padx=25,
            pady=20,
        )

        prof_rows = [
            ("Library Card Number:", "ent_prof_card", True, False),
            ("Email (read-only):", "ent_prof_email", True, False),
            ("National ID (read-only):", "ent_prof_cccd", True, False),
            ("Full Name:", "ent_prof_name", False, False),
            ("Phone Number:", "ent_prof_phone", False, False),
            ("Address:", "ent_prof_addr", False, False),
            ("New Password (leave blank to keep):", "ent_prof_pwd", False, True),
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
            self.profile_frame, text="Save Changes", bg=self.ACCENT_GREEN, fg="white", width=18, bd=0, pady=6, command=self._handle_update_profile
        ).grid(row=len(prof_rows), column=1, sticky="e", pady=12)

    def _populate_profile_form(self, user: User):
        for ent, val in [
            (self.ent_prof_card, getattr(user, "card_number", "")),
            (self.ent_prof_email, getattr(user, "email", "")),
            (self.ent_prof_cccd, getattr(user, "identity_number", "")),
        ]:
            ent.config(state="normal")
            ent.delete(0, tk.END)
            ent.insert(0, val or "")
            ent.config(state="readonly")

        self.ent_prof_name.delete(0, tk.END)
        self.ent_prof_name.insert(0, getattr(user, "full_name", "") or "")
        self.ent_prof_phone.delete(0, tk.END)
        self.ent_prof_phone.insert(0, getattr(user, "phone", "") or "")
        self.ent_prof_addr.delete(0, tk.END)
        self.ent_prof_addr.insert(0, getattr(user, "address", "") or "")
        self.ent_prof_pwd.delete(0, tk.END)

    def _handle_login(self):
        try:
            user = self.auth_service.login(self.ent_login_id.get(), self.ent_login_pwd.get())
            self.ent_login_pwd.delete(0, tk.END)
            messagebox.showinfo("Sign In Success", f"Welcome {user.full_name} ({user.role})!")
            self._refresh_role_access()
        except Exception as e:
            messagebox.showerror("Sign In Error", str(e))

    def _handle_logout(self):
        if hasattr(self.auth_service, "logout"):
            self.auth_service.logout()
        else:
            self.auth_service.current_user = None
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
            messagebox.showinfo("Registration Success", f"Your card number: {member.card_number}")
        except Exception as e:
            messagebox.showerror("Registration Error", str(e))

    def _handle_forgot_password(self):
        email = simpledialog.askstring("Forgot Password (UC-07)", "Enter registered email:")
        if not email:
            return
        try:
            temp_pwd = self.auth_service.reset_password(email)
            messagebox.showinfo("Password Reset", f"Temporary password: {temp_pwd}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _handle_update_profile(self):
        user = getattr(self.auth_service, "current_user", None)
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
            messagebox.showinfo("Success", f"Profile updated for {updated.full_name}.")
        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    def _build_opac_tab(self):
        filter_bar = tk.Frame(self.tab_opac, bg="white", padx=10, pady=10, bd=1, relief="groove")
        filter_bar.pack(fill="x", padx=10, pady=8)

        tk.Label(filter_bar, text="Keyword:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=4)
        self.ent_opac_kw = tk.Entry(filter_bar, width=28)
        self.ent_opac_kw.grid(row=0, column=1, padx=4)

        tk.Label(filter_bar, text="Category:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=4)
        self.cmb_opac_cat = ttk.Combobox(filter_bar, state="readonly", width=20)
        self.cmb_opac_cat.grid(row=0, column=3, padx=4)

        tk.Label(filter_bar, text="Sort by:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=4)
        self.cmb_opac_sort = ttk.Combobox(
            filter_bar,
            state="readonly",
            width=18,
            values=["Title (A-Z)", "Publication Year (Newest)", "Most Borrowed"],
        )
        self.cmb_opac_sort.current(0)
        self.cmb_opac_sort.grid(row=0, column=5, padx=4)

        tk.Button(
            filter_bar, text="🔍 Search", bg=self.ACCENT_GREEN, fg="white", bd=0, padx=12, pady=4, command=self._search_opac
        ).grid(row=0, column=6, padx=6)
        tk.Button(
            filter_bar, text="📍 Shelf & Barcodes", bg=self.ACCENT_BLUE, fg="white", bd=0, padx=12, pady=4, command=self._show_book_copies_popup
        ).grid(row=0, column=7, padx=4)

        cols = ("id", "isbn", "title", "author", "category", "year", "avail")
        self.tree_opac = ttk.Treeview(self.tab_opac, columns=cols, show="headings", height=16)
        for col, text, w in [
            ("id", "ID", 45),
            ("isbn", "ISBN", 125),
            ("title", "Book Title", 280),
            ("author", "Author", 180),
            ("category", "Category", 135),
            ("year", "Year", 70),
            ("avail", "Available / Total", 110),
        ]:
            self.tree_opac.heading(col, text=text)
            self.tree_opac.column(col, width=w, anchor="center" if col in ("id", "year", "avail") else "w")
        self.tree_opac.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_catalog_manager_tab(self):
        tk.Label(
            self.tab_catalog_mgr,
            text="Catalog & Physical Copy Management (UC-03)",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
        ).pack(anchor="w", padx=16, pady=12)

    def _build_user_manager_tab(self):
        tk.Label(
            self.tab_user_mgr,
            text="Member & Role Administration (UC-12)",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
        ).pack(anchor="w", padx=16, pady=12)

    def _load_categories(self):
        try:
            if hasattr(self.catalog_service, "get_categories"):
                cats = self.catalog_service.get_categories() or []
                values = ["All"] + [str(c) for c in cats]
            else:
                values = ["All"]
        except Exception:
            values = ["All"]
        self.cmb_opac_cat["values"] = values
        self.cmb_opac_cat.current(0)

    def _search_opac(self):
        for item in self.tree_opac.get_children():
            self.tree_opac.delete(item)
        try:
            kw = self.ent_opac_kw.get().strip()
            cat = self.cmb_opac_cat.get().strip()
            if hasattr(self.catalog_service, "search_books"):
                books = self.catalog_service.search_books(keyword=kw, category=None if cat in ("", "All") else cat) or []
                for b in books:
                    if isinstance(b, dict):
                        self.tree_opac.insert(
                            "",
                            tk.END,
                            values=(
                                b.get("id", ""),
                                b.get("isbn", ""),
                                b.get("title", ""),
                                b.get("author", ""),
                                b.get("category", ""),
                                b.get("year", ""),
                                b.get("avail", ""),
                            ),
                        )
        except Exception:
            pass

    def _show_book_copies_popup(self):
        selected = self.tree_opac.selection()
        if not selected:
            messagebox.showinfo("Shelf & Barcodes", "Select a book row first to inspect copy locations.")
            return
        vals = self.tree_opac.item(selected[0], "values")
        messagebox.showinfo("Book Copy Details", f"Title: {vals[2]}\nISBN: {vals[1]}\nAvailability: {vals[6]}")
