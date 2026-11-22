import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime

# ---------------------------------------------------------
# 1. DATABASE CONNECTION, REPOSITORIES & SERVICES
# ---------------------------------------------------------
from src.config.db_connection import DatabaseConnection

# Module 1: Catalog & Users
from src.repositories.book_repository import BookRepository
from src.services.catalog_service import CatalogService

# Module 2: Circulation & FIFO Reservation
from src.repositories.circulation_repo import CirculationRepository
from src.services.circulation_service import CirculationService

# Module 3: Reports & Fines
from src.repositories.fine_repository import FineRepository
from src.services.report_fine_service import ReportFineService

# ---------------------------------------------------------
# 2. APPLICATION VIEWS
# ---------------------------------------------------------
from src.views.dashboard_view import DashboardView
from src.views.report_config_view import ReportConfigView
from src.views.auth_catalog_view import AuthCatalogView
from src.views.circulation_view import CirculationView


class MainWindow(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("LMS - Arcadia Library System (Group 12)")
        self.geometry("1400x850")
        self.minsize(1200, 700)

        # Arcadia color palette
        self.COLOR_SIDEBAR_BG = "#1a362f"
        self.COLOR_SIDEBAR_HOVER = "#234940"
        self.COLOR_SIDEBAR_TEXT_ACTIVE = "#ffffff"
        self.COLOR_SIDEBAR_TEXT_INACTIVE = "#8baba1"
        self.COLOR_MAIN_BG = "#f4f7f6"

        self.configure(bg=self.COLOR_MAIN_BG)

        # ==========================================
        # INITIALIZE DATABASE & SERVICES
        # ==========================================
        db = DatabaseConnection()
        self.conn = db.get_connection()
        if not self.conn:
            tb.dialogs.Messagebox.show_error(
                "Unable to connect to SQL Server database.",
                "System Error",
            )
            self.destroy()
            return

        # Repositories
        self.book_repo = BookRepository()
        self.circ_repo = CirculationRepository(self.conn)
        self.fine_repo = FineRepository(self.conn)

        # Services
        self.catalog_service = CatalogService(self.book_repo)
        self.circ_service = CirculationService(self.circ_repo)
        self.report_service = ReportFineService(self.fine_repo)

        # Active logged-in user ID (simulated Head Librarian / Admin #1)
        self.current_user_id = 1

        self.frames = {}
        self.current_btn = None
        self.nav_buttons = {}

        self.setup_sidebar()
        self.setup_main_content()

        # Default view
        self.show_view("dashboard")

    def setup_sidebar(self):
        self.sidebar = tk.Frame(self, bg=self.COLOR_SIDEBAR_BG, width=260)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        lbl_logo = tk.Label(
            self.sidebar,
            text="📚 LMS System",
            font=("Segoe UI", 18, "bold"),
            bg=self.COLOR_SIDEBAR_BG,
            fg=self.COLOR_SIDEBAR_TEXT_ACTIVE,
            anchor="w",
        )
        lbl_logo.pack(fill=X, padx=25, pady=(30, 40))

        menu_items = [
            ("dashboard", "🏠  Overview"),
            ("catalog", "📖  Catalog"),
            ("circulation", "🔄  Circulation"),
            ("members", "👥  Members"),
            ("reports", "📊  Reports & Fines"),
        ]

        lbl_workspace = tk.Label(
            self.sidebar,
            text="WORKSPACE",
            font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_SIDEBAR_BG,
            fg=self.COLOR_SIDEBAR_TEXT_INACTIVE,
            anchor="w",
        )
        lbl_workspace.pack(fill=X, padx=25, pady=(0, 10))

        for key, text in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=("Segoe UI", 11),
                bg=self.COLOR_SIDEBAR_BG,
                fg=self.COLOR_SIDEBAR_TEXT_INACTIVE,
                bd=0,
                anchor="w",
                padx=25,
                pady=8,
                activebackground=self.COLOR_SIDEBAR_HOVER,
                activeforeground=self.COLOR_SIDEBAR_TEXT_ACTIVE,
                cursor="hand2",
            )
            btn.pack(fill=X, padx=10, pady=2)
            btn.bind("<Button-1>", lambda e, k=key, b=btn: self.on_nav_click(k, b))
            self.nav_buttons[key] = btn

        # === BOTTOM SECTION ===
        bottom_frame = tk.Frame(self.sidebar, bg=self.COLOR_SIDEBAR_BG)
        bottom_frame.pack(side=BOTTOM, fill=X, pady=20)

        tk.Frame(bottom_frame, bg=self.COLOR_SIDEBAR_HOVER, height=1).pack(fill=X, padx=20, pady=15)

        user_frame = tk.Frame(bottom_frame, bg=self.COLOR_SIDEBAR_BG)
        user_frame.pack(fill=X, padx=25)

        tk.Label(
            user_frame,
            text="👤",
            font=("Segoe UI", 20),
            bg=self.COLOR_SIDEBAR_BG,
            fg="#e5a059",
        ).pack(side=LEFT)

        info_frame = tk.Frame(user_frame, bg=self.COLOR_SIDEBAR_BG)
        info_frame.pack(side=LEFT, padx=10)
        tk.Label(
            info_frame,
            text="Phùng Gia Phú",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_SIDEBAR_BG,
            fg=self.COLOR_SIDEBAR_TEXT_ACTIVE,
        ).pack(anchor="w")
        tk.Label(
            info_frame,
            text="Head Librarian",
            font=("Segoe UI", 9),
            bg=self.COLOR_SIDEBAR_BG,
            fg=self.COLOR_SIDEBAR_TEXT_INACTIVE,
        ).pack(anchor="w")

        tk.Button(
            user_frame,
            text="🚪",
            font=("Segoe UI", 12),
            bg=self.COLOR_SIDEBAR_BG,
            fg=self.COLOR_SIDEBAR_TEXT_INACTIVE,
            bd=0,
            cursor="hand2",
            command=self.destroy,
        ).pack(side=RIGHT)

    def setup_main_content(self):
        self.main_content = tk.Frame(self, bg=self.COLOR_MAIN_BG)
        self.main_content.pack(side=RIGHT, fill=BOTH, expand=True)

    def on_nav_click(self, view_key, btn_widget):
        if self.current_btn:
            self.current_btn.configure(bg=self.COLOR_SIDEBAR_BG, fg=self.COLOR_SIDEBAR_TEXT_INACTIVE)

        btn_widget.configure(bg=self.COLOR_SIDEBAR_HOVER, fg=self.COLOR_SIDEBAR_TEXT_ACTIVE)
        self.current_btn = btn_widget
        self.show_view(view_key)

    def show_view(self, view_key):
        for widget in self.main_content.winfo_children():
            widget.pack_forget()

        if view_key == "dashboard":
            if "dashboard" not in self.frames:
                self.frames["dashboard"] = DashboardView(self.main_content, self.COLOR_MAIN_BG)
            self.frames["dashboard"].pack(fill=BOTH, expand=True)

        elif view_key in ("catalog", "members"):
            if "catalog" not in self.frames:
                self.frames["catalog"] = AuthCatalogView(self.main_content, self.catalog_service)
            if hasattr(self.frames["catalog"], "select_mode"):
                self.frames["catalog"].select_mode(view_key)
            self.frames["catalog"].pack(fill=BOTH, expand=True)

        elif view_key == "circulation":
            if "circulation" not in self.frames:
                self.frames["circulation"] = CirculationView(self.main_content, self.circ_service, self.COLOR_MAIN_BG)
            if hasattr(self.frames["circulation"], "refresh_tables"):
                self.frames["circulation"].refresh_tables()
            self.frames["circulation"].pack(fill=BOTH, expand=True)

        elif view_key == "reports":
            if "reports" not in self.frames:
                self.frames["reports"] = ReportConfigView(self.main_content, self.report_service, self.current_user_id)
            self.frames["reports"].pack(fill=BOTH, expand=True)

        else:
            lbl = tk.Label(
                self.main_content,
                text=f"{view_key.capitalize()} view is under maintenance.",
                font=("Segoe UI", 18),
                bg=self.COLOR_MAIN_BG,
            )
            lbl.pack(expand=True)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
