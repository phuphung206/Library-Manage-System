from datetime import datetime, timedelta
from src.repositories.circulation_repo import CirculationRepository


class CirculationService:
    def __init__(self, repo: CirculationRepository = None):
        self.repo = repo or CirculationRepository()

    # UC-08: Check-out Books (Borrow)
    def checkout_books(self, reader_id: int, employee_id: int, barcodes: list[str]):
        if not barcodes:
            raise ValueError("Barcode list cannot be empty.")

        max_books = self.repo.get_config_value("MAX_BORROW_BOOKS", 5)
        borrow_days = self.repo.get_config_value("MAX_BORROW_DAYS", 14)

        reader = self.repo.get_reader_info(reader_id)
        if not reader:
            raise ValueError("Reader not found.")
        if reader[3] != "ACTIVE":
            raise ValueError(f"Reader card is not eligible (Current status: {reader[3]}).")

        unpaid_fines = self.repo.get_unpaid_fines_total(reader_id)
        if unpaid_fines > 0:
            raise ValueError(f"Reader has {unpaid_fines:,.0f} VND in unpaid fines. Please settle fines before borrowing.")

        current_borrowed = self.repo.count_active_borrowed_books(reader_id)
        if current_borrowed + len(barcodes) > max_books:
            raise ValueError(f"Borrowing quota exceeded (Max: {max_books} books). Currently borrowed: {current_borrowed}.")

        for bc in barcodes:
            copy_info = self.repo.get_copy_info(bc)
            if not copy_info:
                raise ValueError(f"Barcode {bc} does not exist in inventory.")
            status = copy_info[3]
            isbn = copy_info[1]

            if status == "AVAILABLE":
                continue
            elif status == "RESERVED":
                ready_res = self.repo.get_ready_reservation_for_reader(isbn, reader_id)
                if not ready_res:
                    raise ValueError(f"Copy {bc} is currently held for another reader.")
            else:
                raise ValueError(f"Copy {bc} is not available for check-out (Status: {status}).")

        slip_id, due_date = self.repo.execute_checkout(reader_id, employee_id, barcodes, borrow_days)
        return {"borrow_slip_id": slip_id, "due_date": due_date, "count": len(barcodes)}

    # UC-09: Check-in Book (Return)
    def checkin_book(self, barcode: str, return_condition: str = "GOOD"):
        if return_condition not in ("GOOD", "DAMAGED", "LOST"):
            raise ValueError("Return condition must be GOOD, DAMAGED, or LOST.")

        fine_per_day = self.repo.get_config_value("FINE_PER_DAY_VND", 5000)
        hold_hours = self.repo.get_config_value("RESERVATION_HOLD_HOURS", 48)
        return self.repo.execute_checkin(barcode, return_condition, fine_per_day, hold_hours)

    # UC-10: Renew Book Loan
    def renew_loan(self, borrow_slip_id: int, reader_id: int):
        borrow_days = self.repo.get_config_value("MAX_BORROW_DAYS", 14)
        max_renewals = self.repo.get_config_value("MAX_RENEWAL_TIMES", 2)

        if self.repo.get_unpaid_fines_total(reader_id) > 0:
            raise ValueError("Cannot renew loan while unpaid fines exist.")

        cursor = self.repo.conn.cursor()
        cursor.execute("""
            SELECT BorrowDate, DueDate, Status
            FROM BORROW_SLIP
            WHERE BorrowSlipID = ? AND ReaderID = ?
        """, (borrow_slip_id, reader_id))
        slip = cursor.fetchone()
        if not slip:
            raise ValueError("Borrow slip not found.")

        borrow_date, due_date, status = slip
        if status != "BORROWED" or datetime.now() > due_date:
            raise ValueError("Borrow slip is already overdue or closed and cannot be renewed.")

        current_days = (due_date.date() - borrow_date.date()).days
        renewal_count = max(0, (current_days // borrow_days) - 1)
        if renewal_count >= max_renewals:
            raise ValueError(f"Maximum renewal limit reached ({max_renewals} times).")

        cursor.execute("""
            SELECT COUNT(*)
            FROM BORROW_SLIP_DETAIL bsd
            JOIN BOOK_COPY bc ON bsd.Barcode = bc.Barcode
            JOIN RESERVATION r ON bc.ISBN = r.ISBN
            WHERE bsd.BorrowSlipID = ? AND r.Status = 'WAITING'
        """, (borrow_slip_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Book title has an active reservation queue and cannot be renewed.")

        new_due_date = due_date + timedelta(days=borrow_days)
        cursor.execute("UPDATE BORROW_SLIP SET DueDate = ? WHERE BorrowSlipID = ?", (new_due_date, borrow_slip_id))
        self.repo.conn.commit()
        return {"borrow_slip_id": borrow_slip_id, "new_due_date": new_due_date}

    # UC-11: Reserve Book (FIFO Hold Queue)
    def reserve_book(self, reader_id: int, isbn: str):
        reader = self.repo.get_reader_info(reader_id)
        if not reader or reader[3] != "ACTIVE":
            raise ValueError("Reader card is not active.")

        if self.repo.get_unpaid_fines_total(reader_id) > 0:
            raise ValueError("Please settle all unpaid fines before placing a reservation.")

        cursor = self.repo.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM BOOK_COPY WHERE ISBN = ? AND Status = 'AVAILABLE'
        """, (isbn,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Copies are currently available on the shelf; direct check-out is available.")

        cursor.execute("""
            SELECT COUNT(*) FROM RESERVATION
            WHERE ISBN = ? AND ReaderID = ? AND Status IN ('WAITING', 'READY')
        """, (isbn, reader_id))
        if cursor.fetchone()[0] > 0:
            raise ValueError("You already have an active reservation for this book title.")

        now = datetime.now()
        cursor.execute("""
            INSERT INTO RESERVATION (ISBN, ReaderID, ReservationDate, Status)
            OUTPUT INSERTED.ReservationID
            VALUES (?, ?, ?, 'WAITING')
        """, (isbn, reader_id, now))
        res_id = cursor.fetchone()[0]
        self.repo.conn.commit()
        return {"reservation_id": res_id, "status": "WAITING", "reservation_date": now}