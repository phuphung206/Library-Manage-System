from datetime import datetime, timedelta
from src.repositories.circulation_repo import CirculationRepository


class CirculationService:
    def __init__(self, repo: CirculationRepository = None):
        self.repo = repo or CirculationRepository()

    # UC-08: Mượn sách (Check-out)
    def checkout_books(self, reader_id: int, employee_id: int, barcodes: list[str]):
        if not barcodes:
            raise ValueError("Danh sách mã vạch sách mượn không được trống.")

        max_books = self.repo.get_config_value("MAX_BORROW_BOOKS", 5)
        borrow_days = self.repo.get_config_value("MAX_BORROW_DAYS", 14)

        reader = self.repo.get_reader_info(reader_id)
        if not reader:
            raise ValueError("Không tìm thấy độc giả.")
        if reader[3] != "ACTIVE":
            raise ValueError(f"Thẻ độc giả không hợp lệ (Trạng thái hiện tại: {reader[3]}).")

        unpaid_fines = self.repo.get_unpaid_fines_total(reader_id)
        if unpaid_fines > 0:
            raise ValueError(f"Độc giả đang nợ {unpaid_fines:,.0f} VND tiền phạt. Vui lòng thanh toán trước khi mượn.")

        current_borrowed = self.repo.count_active_borrowed_books(reader_id)
        if current_borrowed + len(barcodes) > max_books:
            raise ValueError(f"Vượt quá hạn mức mượn tối đa ({max_books} cuốn). Đang mượn: {current_borrowed} cuốn.")

        for bc in barcodes:
            copy_info = self.repo.get_copy_info(bc)
            if not copy_info:
                raise ValueError(f"Mã vạch {bc} không tồn tại trong kho.")
            status = copy_info[3]
            isbn = copy_info[1]

            if status == "AVAILABLE":
                continue
            elif status == "RESERVED":
                ready_res = self.repo.get_ready_reservation_for_reader(isbn, reader_id)
                if not ready_res:
                    raise ValueError(f"Bản sao {bc} đang được giữ chỗ cho độc giả khác.")
            else:
                raise ValueError(f"Bản sao {bc} không sẵn sàng để mượn (Trạng thái: {status}).")

        slip_id, due_date = self.repo.execute_checkout(reader_id, employee_id, barcodes, borrow_days)
        return {"borrow_slip_id": slip_id, "due_date": due_date, "count": len(barcodes)}

    # UC-09: Trả sách (Check-in)
    def checkin_book(self, barcode: str, return_condition: str = "GOOD"):
        if return_condition not in ("GOOD", "DAMAGED", "LOST"):
            raise ValueError("Tình trạng sách trả phải là GOOD, DAMAGED hoặc LOST.")

        fine_per_day = self.repo.get_config_value("FINE_PER_DAY_VND", 5000)
        hold_hours = self.repo.get_config_value("RESERVATION_HOLD_HOURS", 48)
        return self.repo.execute_checkin(barcode, return_condition, fine_per_day, hold_hours)

    # UC-10: Gia hạn mượn sách (Renew Book Loan)
    def renew_loan(self, borrow_slip_id: int, reader_id: int):
        borrow_days = self.repo.get_config_value("MAX_BORROW_DAYS", 14)
        max_renewals = self.repo.get_config_value("MAX_RENEWAL_TIMES", 2)

        if self.repo.get_unpaid_fines_total(reader_id) > 0:
            raise ValueError("Không thể gia hạn khi đang có tiền phạt chưa thanh toán.")

        cursor = self.repo.conn.cursor()
        cursor.execute("""
            SELECT BorrowDate, DueDate, Status
            FROM BORROW_SLIP
            WHERE BorrowSlipID = ? AND ReaderID = ?
        """, (borrow_slip_id, reader_id))
        slip = cursor.fetchone()
        if not slip:
            raise ValueError("Không tìm thấy phiếu mượn.")

        borrow_date, due_date, status = slip
        if status != "BORROWED" or datetime.now() > due_date:
            raise ValueError("Phiếu mượn đã quá hạn hoặc đã đóng, không thể gia hạn.")

        current_days = (due_date.date() - borrow_date.date()).days
        renewal_count = max(0, (current_days // borrow_days) - 1)
        if renewal_count >= max_renewals:
            raise ValueError(f"Đã đạt giới hạn gia hạn tối đa ({max_renewals} lần).")

        cursor.execute("""
            SELECT COUNT(*)
            FROM BORROW_SLIP_DETAIL bsd
            JOIN BOOK_COPY bc ON bsd.Barcode = bc.Barcode
            JOIN RESERVATION r ON bc.ISBN = r.ISBN
            WHERE bsd.BorrowSlipID = ? AND r.Status = 'WAITING'
        """, (borrow_slip_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Sách trong phiếu mượn đang có độc giả khác đặt trước, không thể gia hạn.")

        new_due_date = due_date + timedelta(days=borrow_days)
        cursor.execute("UPDATE BORROW_SLIP SET DueDate = ? WHERE BorrowSlipID = ?", (new_due_date, borrow_slip_id))
        self.repo.conn.commit()
        return {"borrow_slip_id": borrow_slip_id, "new_due_date": new_due_date}

    # UC-11: Đặt trước sách theo hàng đợi FIFO (Reserve Book)
    def reserve_book(self, reader_id: int, isbn: str):
        reader = self.repo.get_reader_info(reader_id)
        if not reader or reader[3] != "ACTIVE":
            raise ValueError("Thẻ độc giả không hoạt động.")

        if self.repo.get_unpaid_fines_total(reader_id) > 0:
            raise ValueError("Vui lòng thanh toán hết tiền phạt trước khi đặt trước sách.")

        cursor = self.repo.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM BOOK_COPY WHERE ISBN = ? AND Status = 'AVAILABLE'
        """, (isbn,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Sách hiện vẫn còn bản sao sẵn sàng trên kệ, bạn có thể mượn trực tiếp.")

        cursor.execute("""
            SELECT COUNT(*) FROM RESERVATION
            WHERE ISBN = ? AND ReaderID = ? AND Status IN ('WAITING', 'READY')
        """, (isbn, reader_id))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Bạn đã có yêu cầu đặt trước đang chờ cho đầu sách này.")

        now = datetime.now()
        cursor.execute("""
            INSERT INTO RESERVATION (ISBN, ReaderID, ReservationDate, Status)
            OUTPUT INSERTED.ReservationID
            VALUES (?, ?, ?, 'WAITING')
        """, (isbn, reader_id, now))
        res_id = cursor.fetchone()[0]
        self.repo.conn.commit()
        return {"reservation_id": res_id, "status": "WAITING", "reservation_date": now}
