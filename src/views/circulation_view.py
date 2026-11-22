import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.services.circulation_service import CirculationService

class CirculationView(tk.Frame):
    """Circulation & FIFO Reservation View (UC-08 to UC-11) for LMS."""

    def __init__(self, parent=None, service: CirculationService = None, bg_color: str = "#f4f7f6"):
        self._standalone = parent is None
        if self._standalone:
            root = tk.Tk()
            root.title("Circulation & FIFO Reservation - LMS")
            root.geometry("1280x780")
            parent = root
            self._root = root

        super().__init__(parent, bg=bg_color)
        self.bg_color = bg_color
        self.service = service or CirculationService()

        self._build_ui()
        self.refresh_tables()

    def _build_ui(self):
        # Top Header Bar
        header_frame = tk.Frame(self, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=24, pady=(18, 10))

        title_box = tk.Frame(header_frame, bg=self.bg_color)
        title_box.pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="Circulation & FIFO Reservation Desk",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg="#1a362f",
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Check-out (UC-08), Check-in & FIFO Queue (UC-09), Loan Renewal (UC-10), Book Reservation (UC-11)",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#5a6b65",
        ).pack(anchor="w")

        btn_refresh = tk.Button(
            header_frame,
            text="↻ Refresh Tables",
            font=("Segoe UI", 10, "bold"),
            bg="#1a362f",
            fg="#ffffff",
            activebackground="#234940",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.refresh_tables,
        )
        btn_refresh.pack(side=tk.RIGHT)

        # Summary KPI Cards Row
        kpi_frame = tk.Frame(self, bg=self.bg_color)
        kpi_frame.pack(fill=tk.X, padx=24, pady=(4, 14))

        self.lbl_active_loans = self._create_kpi_card(kpi_frame, "Active Borrow Slips", "0", "#1a362f", "#ffffff", 0)
        self.lbl_waiting_queue = self._create_kpi_card(kpi_frame, "FIFO Waiting Queue", "0", "#ffffff", "#1a362f", 1)
        self.lbl_ready_holds = self._create_kpi_card(kpi_frame, "Ready Holds (48h)", "0", "#ffffff", "#1a362f", 2)
        self.lbl_last_action = self._create_kpi_card(kpi_frame, "Last Operation", "Ready", "#ffffff", "#1a362f", 3)

        # Action Notebook (Tabs for all 4 Use Cases)
        notebook_frame = tk.Frame(self, bg="#ffffff", highlightbackground="#dce3e0", highlightthickness=1)
        notebook_frame.pack(fill=tk.X, padx=24, pady=(0, 14))

        style = ttk.Style()
        style.configure("Circ.TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 8])

        self.notebook = ttk.Notebook(notebook_frame, style="Circ.TNotebook")
        self.notebook.pack(fill=tk.X, padx=10, pady=8)

        self._build_checkout_tab()
        self._build_checkin_tab()
        self._build_renew_tab()
        self._build_reserve_tab()

        # Status / Feedback Banner
        self.status_var = tk.StringVar(value="Ready. Enter parameters above and click an action button.")
        status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"),
            bg="#e6efec",
            fg="#1a362f",
            anchor="w",
            padx=14,
            pady=8,
        )
        status_bar.pack(fill=tk.X, padx=24, pady=(0, 10))

        # Bottom Data Tables (Active Loans & FIFO Reservations)
        tables_frame = tk.Frame(self, bg=self.bg_color)
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 18))
        tables_frame.columnconfigure(0, weight=1)
        tables_frame.columnconfigure(1, weight=1)
        tables_frame.rowconfigure(0, weight=1)

        # Left Table: Active Borrow Slips
        left_card = tk.Frame(tables_frame, bg="#ffffff", highlightbackground="#dce3e0", highlightthickness=1)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            left_card,
            text="Active Borrow Slips",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#1a362f",
        ).pack(anchor="w", padx=12, pady=(10, 6))

        loan_cols = ("slip_id", "reader_id", "borrow_date", "due_date", "status")
        self.loans_tree = ttk.Treeview(left_card, columns=loan_cols, show="headings", height=8)
        for col, text, w in [
            ("slip_id", "Slip ID", 70),
            ("reader_id", "Reader ID", 80),
            ("borrow_date", "Borrow Date", 125),
            ("due_date", "Due Date", 125),
            ("status", "Status", 95),
        ]:
            self.loans_tree.heading(col, text=text)
            self.loans_tree.column(col, width=w, anchor="center")
        self.loans_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # Right Table: FIFO Reservation Queue
        right_card = tk.Frame(tables_frame, bg="#ffffff", highlightbackground="#dce3e0", highlightthickness=1)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            right_card,
            text="FIFO Reservation Queue",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#1a362f",
        ).pack(anchor="w", padx=12, pady=(10, 6))

        res_cols = ("res_id", "isbn", "reader_id", "reserved_at", "status")
        self.res_tree = ttk.Treeview(right_card, columns=res_cols, show="headings", height=8)
        for col, text, w in [
            ("res_id", "Res ID", 70),
            ("isbn", "ISBN", 130),
            ("reader_id", "Reader ID", 80),
            ("reserved_at", "Reserved Date", 130),
            ("status", "Status", 90),
        ]:
            self.res_tree.heading(col, text=text)
            self.res_tree.column(col, width=w, anchor="center")
        self.res_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

    def _create_kpi_card(self, parent, label: str, initial_val: str, bg: str, fg: str, col: int):
        card = tk.Frame(
            parent,
            bg=bg,
            highlightbackground="#dce3e0",
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0 if col == 3 else 8))
        parent.columnconfigure(col, weight=1)

        sub_fg = "#c7ddd6" if bg == "#1a362f" else "#5a6b65"
        tk.Label(card, text=label, font=("Segoe UI", 9, "bold"), bg=bg, fg=sub_fg).pack(anchor="w")
        val_lbl = tk.Label(card, text=initial_val, font=("Segoe UI", 16, "bold"), bg=bg, fg=fg)
        val_lbl.pack(anchor="w", pady=(4, 0))
        return val_lbl

    def _build_checkout_tab(self):
        tab = tk.Frame(self.notebook, bg="#ffffff", padx=12, pady=10)
        self.notebook.add(tab, text="1. Check-out (UC-08)")

        tk.Label(tab, text="Reader ID:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=0, padx=(0, 6))
        self.ent_co_reader = tk.Entry(tab, width=12, font=("Segoe UI", 10))
        self.ent_co_reader.grid(row=0, column=1, padx=(0, 14))

        tk.Label(tab, text="Employee ID:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=2, padx=(0, 6))
        self.ent_co_emp = tk.Entry(tab, width=12, font=("Segoe UI", 10))
        self.ent_co_emp.insert(0, "1")
        self.ent_co_emp.grid(row=0, column=3, padx=(0, 14))

        tk.Label(tab, text="Barcodes (comma-separated):", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=4, padx=(0, 6))
        self.ent_co_barcodes = tk.Entry(tab, width=28, font=("Segoe UI", 10))
        self.ent_co_barcodes.grid(row=0, column=5, padx=(0, 14))

        tk.Button(
            tab,
            text="Check-out Books",
            font=("Segoe UI", 10, "bold"),
            bg="#1a362f",
            fg="#ffffff",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.handle_checkout,
        ).grid(row=0, column=6)

    def _build_checkin_tab(self):
        tab = tk.Frame(self.notebook, bg="#ffffff", padx=12, pady=10)
        self.notebook.add(tab, text="2. Check-in & FIFO (UC-09)")

        tk.Label(tab, text="Book Barcode:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=0, padx=(0, 6))
        self.ent_ci_barcode = tk.Entry(tab, width=20, font=("Segoe UI", 10))
        self.ent_ci_barcode.grid(row=0, column=1, padx=(0, 14))

        tk.Label(tab, text="Return Condition:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=2, padx=(0, 6))
        self.cmb_ci_condition = ttk.Combobox(tab, values=["GOOD", "DAMAGED", "LOST"], state="readonly", width=14, font=("Segoe UI", 10))
        self.cmb_ci_condition.set("GOOD")
        self.cmb_ci_condition.grid(row=0, column=3, padx=(0, 14))

        tk.Button(
            tab,
            text="Check-in Book",
            font=("Segoe UI", 10, "bold"),
            bg="#1a362f",
            fg="#ffffff",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.handle_checkin,
        ).grid(row=0, column=4)

    def _build_renew_tab(self):
        tab = tk.Frame(self.notebook, bg="#ffffff", padx=12, pady=10)
        self.notebook.add(tab, text="3. Renew Loan (UC-10)")

        tk.Label(tab, text="Borrow Slip ID:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=0, padx=(0, 6))
        self.ent_rn_slip = tk.Entry(tab, width=14, font=("Segoe UI", 10))
        self.ent_rn_slip.grid(row=0, column=1, padx=(0, 14))

        tk.Label(tab, text="Reader ID:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=2, padx=(0, 6))
        self.ent_rn_reader = tk.Entry(tab, width=14, font=("Segoe UI", 10))
        self.ent_rn_reader.grid(row=0, column=3, padx=(0, 14))

        tk.Button(
            tab,
            text="Renew Loan",
            font=("Segoe UI", 10, "bold"),
            bg="#1a362f",
            fg="#ffffff",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.handle_renew,
        ).grid(row=0, column=4)

    def _build_reserve_tab(self):
        tab = tk.Frame(self.notebook, bg="#ffffff", padx=12, pady=10)
        self.notebook.add(tab, text="4. Reserve Book FIFO (UC-11)")

        tk.Label(tab, text="Reader ID:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=0, padx=(0, 6))
        self.ent_rs_reader = tk.Entry(tab, width=14, font=("Segoe UI", 10))
        self.ent_rs_reader.grid(row=0, column=1, padx=(0, 14))

        tk.Label(tab, text="Book ISBN:", font=("Segoe UI", 10), bg="#ffffff").grid(row=0, column=2, padx=(0, 6))
        self.ent_rs_isbn = tk.Entry(tab, width=24, font=("Segoe UI", 10))
        self.ent_rs_isbn.grid(row=0, column=3, padx=(0, 14))

        tk.Button(
            tab,
            text="Join FIFO Queue",
            font=("Segoe UI", 10, "bold"),
            bg="#1a362f",
            fg="#ffffff",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.handle_reserve,
        ).grid(row=0, column=4)

    def _set_status(self, message: str, is_error: bool = False):
        self.status_var.set(message)
        self.lbl_last_action.config(text="Error" if is_error else "Success")

    def handle_checkout(self):
        try:
            reader_id = int(self.ent_co_reader.get().strip())
            employee_id = int(self.ent_co_emp.get().strip())
            barcodes = [b.strip() for b in self.ent_co_barcodes.get().split(",") if b.strip()]
            res = self.service.checkout_books(reader_id, employee_id, barcodes)
            msg = f"Check-out succeeded | Slip #{res['borrow_slip_id']} | Due: {res['due_date']} | Books: {res['count']}"
            self._set_status(msg, is_error=False)
            messagebox.showinfo("Check-out Success", msg)
            self.refresh_tables()
        except Exception as exc:
            self._set_status(f"Check-out failed: {exc}", is_error=True)
            messagebox.showerror("Check-out Error", str(exc))

    def handle_checkin(self):
        try:
            barcode = self.ent_ci_barcode.get().strip()
            condition = self.cmb_ci_condition.get().strip() or "GOOD"
            res = self.service.checkin_book(barcode, condition)
            fifo_info = f" | FIFO Hold for Reader #{res['reserved_for_reader']}" if res.get("reserved_for_reader") else ""
            msg = (
                f"Check-in succeeded | Slip #{res['borrow_slip_id']} | "
                f"Copy Status: {res['next_copy_status']} | Fine: {res['fine_amount']:,.0f} VND{fifo_info}"
            )
            self._set_status(msg, is_error=False)
            messagebox.showinfo("Check-in Success", msg)
            self.refresh_tables()
        except Exception as exc:
            self._set_status(f"Check-in failed: {exc}", is_error=True)
            messagebox.showerror("Check-in Error", str(exc))

    def handle_renew(self):
        try:
            slip_id = int(self.ent_rn_slip.get().strip())
            reader_id = int(self.ent_rn_reader.get().strip())
            res = self.service.renew_loan(slip_id, reader_id)
            msg = f"Renewal succeeded | Slip #{res['borrow_slip_id']} | New Due Date: {res['new_due_date']}"
            self._set_status(msg, is_error=False)
            messagebox.showinfo("Renewal Success", msg)
            self.refresh_tables()
        except Exception as exc:
            self._set_status(f"Renewal failed: {exc}", is_error=True)
            messagebox.showerror("Renewal Error", str(exc))

    def handle_reserve(self):
        try:
            reader_id = int(self.ent_rs_reader.get().strip())
            isbn = self.ent_rs_isbn.get().strip()
            res = self.service.reserve_book(reader_id, isbn)
            msg = f"Reservation placed | ID #{res['reservation_id']} | Status: {res['status']} | Date: {res['reservation_date']}"
            self._set_status(msg, is_error=False)
            messagebox.showinfo("Reservation Success", msg)
            self.refresh_tables()
        except Exception as exc:
            self._set_status(f"Reservation failed: {exc}", is_error=True)
            messagebox.showerror("Reservation Error", str(exc))

    def refresh_tables(self):
        """Load active borrow slips and FIFO reservations from DB if available."""
        for tree in (self.loans_tree, self.res_tree):
            for row in tree.get_children():
                tree.delete(row)

        conn = getattr(getattr(self.service, "repo", None), "conn", None)
        if not conn:
            return

        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT TOP 20 BorrowSlipID, ReaderID, BorrowDate, DueDate, Status
                FROM BORROW_SLIP
                WHERE ActualReturnDate IS NULL
                ORDER BY BorrowDate DESC
            """)
            loan_rows = cursor.fetchall()
            self.lbl_active_loans.config(text=str(len(loan_rows)))
            for r in loan_rows:
                b_date = r[2].strftime("%Y-%m-%d") if hasattr(r[2], "strftime") else str(r[2])
                d_date = r[3].strftime("%Y-%m-%d") if hasattr(r[3], "strftime") else str(r[3])
                self.loans_tree.insert("", tk.END, values=(r[0], r[1], b_date, d_date, r[4]))

            cursor.execute("""
                SELECT TOP 20 ReservationID, ISBN, ReaderID, ReservationDate, Status
                FROM RESERVATION
                WHERE Status IN ('WAITING', 'READY')
                ORDER BY ReservationDate ASC
            """)
            res_rows = cursor.fetchall()
            waiting_cnt = sum(1 for r in res_rows if r[4] == "WAITING")
            ready_cnt = sum(1 for r in res_rows if r[4] == "READY")
            self.lbl_waiting_queue.config(text=str(waiting_cnt))
            self.lbl_ready_holds.config(text=str(ready_cnt))

            for r in res_rows:
                r_date = r[3].strftime("%Y-%m-%d %H:%M") if hasattr(r[3], "strftime") else str(r[3])
                self.res_tree.insert("", tk.END, values=(r[0], r[1], r[2], r_date, r[4]))
        except Exception:
            # Keep UI functional even when DB schema is not yet initialized
            self.lbl_active_loans.config(text="0")
            self.lbl_waiting_queue.config(text="0")
            self.lbl_ready_holds.config(text="0")

    def run(self):
        if self._standalone:
            self.pack(fill=tk.BOTH, expand=True)
            self._root.mainloop()


if __name__ == "__main__":
    CirculationView().run()
