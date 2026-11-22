from datetime import datetime, timedelta
from src.config.db_connection import DatabaseConnection
class CirculationRepository:
    def __init__(self, conn=None):
        self.conn = conn or DatabaseConnection().get_connection()

    def get_config_value(self, key: str, default_val: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT config_value FROM system_configs WHERE config_key = ?", (key,))
        row = cursor.fetchone()
        return int(row[0]) if row else default_val

    def get_reader_info(self, reader_id: int):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ReaderID, FullName, Email, CardStatus
            FROM READER
            WHERE ReaderID = ?
        """, (reader_id,))
        return cursor.fetchone()

    def count_active_borrowed_books(self, reader_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM BORROW_SLIP bs
            JOIN BORROW_SLIP_DETAIL bsd ON bs.BorrowSlipID = bsd.BorrowSlipID
            WHERE bs.ReaderID = ? AND bs.Status IN ('BORROWED', 'OVERDUE')
              AND bs.ActualReturnDate IS NULL
        """, (reader_id,))
        return cursor.fetchone()[0]

    def get_unpaid_fines_total(self, reader_id: int) -> float:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ISNULL(SUM(FineAmount), 0)
            FROM FINE
            WHERE ReaderID = ? AND Status = 'UNPAID'
        """, (reader_id,))
        return float(cursor.fetchone()[0])

    def get_copy_info(self, barcode: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT Barcode, ISBN, Location, Status
            FROM BOOK_COPY
            WHERE Barcode = ?
        """, (barcode,))
        return cursor.fetchone()

    def get_earliest_waiting_reservation(self, isbn: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT TOP 1 ReservationID, ReaderID, ReservationDate
            FROM RESERVATION
            WHERE ISBN = ? AND Status = 'WAITING'
            ORDER BY ReservationDate ASC
        """, (isbn,))
        return cursor.fetchone()

    def get_ready_reservation_for_reader(self, isbn: str, reader_id: int):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT TOP 1 ReservationID
            FROM RESERVATION
            WHERE ISBN = ? AND ReaderID = ? AND Status = 'READY'
            ORDER BY ReservationDate ASC
        """, (isbn, reader_id))
        return cursor.fetchone()

    def execute_checkout(self, reader_id: int, employee_id: int, barcodes: list[str], borrow_days: int):
        cursor = self.conn.cursor()
        try:
            borrow_date = datetime.now()
            due_date = borrow_date + timedelta(days=borrow_days)

            cursor.execute("""
                INSERT INTO BORROW_SLIP (BorrowDate, DueDate, ActualReturnDate, ReaderID, EmployeeID, Status)
                OUTPUT INSERTED.BorrowSlipID
                VALUES (?, ?, NULL, ?, ?, 'BORROWED')
            """, (borrow_date, due_date, reader_id, employee_id))
            borrow_slip_id = cursor.fetchone()[0]

            for bc in barcodes:
                copy_info = self.get_copy_info(bc)
                isbn = copy_info[1]

                cursor.execute("""
                    INSERT INTO BORROW_SLIP_DETAIL (BorrowSlipID, Barcode, ConditionWhenBorrow, ConditionWhenReturn)
                    VALUES (?, ?, 'GOOD', NULL)
                """, (borrow_slip_id, bc))

                cursor.execute("""
                    UPDATE BOOK_COPY SET Status = 'BORROWED' WHERE Barcode = ?
                """, (bc,))

                cursor.execute("""
                    UPDATE RESERVATION
                    SET Status = 'FULFILLED'
                    WHERE ISBN = ? AND ReaderID = ? AND Status = 'READY'
                """, (isbn, reader_id))

            self.conn.commit()
            return borrow_slip_id, due_date
        except Exception as e:
            self.conn.rollback()
            raise e

    def execute_checkin(self, barcode: str, return_condition: str, fine_per_day: int, hold_hours: int):
        cursor = self.conn.cursor()
        try:
            return_date = datetime.now()

            cursor.execute("""
                SELECT TOP 1 bs.BorrowSlipID, bs.DueDate, bs.ReaderID, bc.ISBN, bt.Title
                FROM BORROW_SLIP bs
                JOIN BORROW_SLIP_DETAIL bsd ON bs.BorrowSlipID = bsd.BorrowSlipID
                JOIN BOOK_COPY bc ON bsd.Barcode = bc.Barcode
                JOIN BOOK_TITLE bt ON bc.ISBN = bt.ISBN
                WHERE bsd.Barcode = ? AND bs.ActualReturnDate IS NULL
                ORDER BY bs.BorrowDate DESC
            """, (barcode,))
            loan = cursor.fetchone()
            if not loan:
                raise ValueError(f"Không tìm thấy giao dịch mượn đang hoạt động cho mã vạch: {barcode}")

            slip_id, due_date, reader_id, isbn, book_title = loan

            cursor.execute("""
                UPDATE BORROW_SLIP_DETAIL
                SET ConditionWhenReturn = ?
                WHERE BorrowSlipID = ? AND Barcode = ?
            """, (return_condition, slip_id, barcode))

            cursor.execute("""
                SELECT COUNT(*) FROM BORROW_SLIP_DETAIL
                WHERE BorrowSlipID = ? AND ConditionWhenReturn IS NULL
            """, (slip_id,))
            remaining_unreturned = cursor.fetchone()[0]

            if remaining_unreturned == 0:
                cursor.execute("""
                    UPDATE BORROW_SLIP
                    SET ActualReturnDate = ?, Status = 'RETURNED'
                    WHERE BorrowSlipID = ?
                """, (return_date, slip_id))

            fine_created = 0.0
            overdue_days = max(0, (return_date.date() - due_date.date()).days)
            if overdue_days > 0:
                fine_created += overdue_days * fine_per_day
                cursor.execute("""
                    INSERT INTO FINE (ReaderID, BorrowSlipID, FineAmount, Reason, Status)
                    VALUES (?, ?, ?, ?, 'UNPAID')
                """, (reader_id, slip_id, overdue_days * fine_per_day, f"Quá hạn {overdue_days} ngày (Barcode: {barcode})"))

            if return_condition in ('DAMAGED', 'LOST'):
                cursor.execute("""
                    INSERT INTO FINE (ReaderID, BorrowSlipID, FineAmount, Reason, Status)
                    VALUES (?, ?, ?, ?, 'UNPAID')
                """, (reader_id, slip_id, 100000, f"Sách {return_condition} (Barcode: {barcode})"))
                fine_created += 100000

            next_copy_status = 'AVAILABLE'
            reserved_for_reader = None

            if return_condition == 'GOOD':
                waiting_res = self.get_earliest_waiting_reservation(isbn)
                if waiting_res:
                    res_id, waiting_reader_id, _ = waiting_res
                    next_copy_status = 'RESERVED'
                    reserved_for_reader = waiting_reader_id

                    cursor.execute("""
                        UPDATE RESERVATION SET Status = 'READY' WHERE ReservationID = ?
                    """, (res_id,))

                    cursor.execute("""
                        SELECT Username FROM ACCOUNT WHERE ReaderID = ?
                    """, (waiting_reader_id,))
                    acc_row = cursor.fetchone()
                    if acc_row:
                        hold_deadline = (return_date + timedelta(hours=hold_hours)).strftime("%d/%m/%Y %H:%M")
                        cursor.execute("""
                            INSERT INTO NOTIFICATION (Username, Title, Content, SendDate, NotificationType, Status)
                            VALUES (?, ?, ?, ?, 'RESERVATION_READY', 'UNREAD')
                        """, (
                            acc_row[0],
                            f"Sách đặt trước đã sẵn sàng: {book_title}",
                            f"Bản sao {barcode} đang được giữ cho bạn đến {hold_deadline} ({hold_hours}h).",
                            return_date
                        ))
            else:
                next_copy_status = return_condition

            cursor.execute("UPDATE BOOK_COPY SET Status = ? WHERE Barcode = ?", (next_copy_status, barcode))

            self.conn.commit()
            return {
                "borrow_slip_id": slip_id,
                "fine_amount": fine_created,
                "next_copy_status": next_copy_status,
                "reserved_for_reader": reserved_for_reader
            }
        except Exception as e:
            self.conn.rollback()
            raise e
