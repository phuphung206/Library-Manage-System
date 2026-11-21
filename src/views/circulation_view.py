from src.services.circulation_service import CirculationService


class CirculationView:
    def __init__(self, service: CirculationService = None):
        self.service = service or CirculationService()

    def run(self):
        while True:
            print("\n=== CIRCULATION & FIFO RESERVATION MODULE (PERSON 2) ===")
            print("1. Check-out Books (UC-08)")
            print("2. Check-in Book (UC-09)")
            print("3. Renew Book Loan (UC-10)")
            print("4. Reserve Book - FIFO Queue (UC-11)")
            print("0. Exit")

            choice = input("Select an option (0-4): ").strip()
            try:
                if choice == "1":
                    reader_id = int(input("Enter ReaderID: ").strip())
                    employee_id = int(input("Enter EmployeeID (Librarian): ").strip())
                    raw_bc = input("Enter book barcodes (comma-separated, e.g. BC-001,BC-002): ").strip()
                    barcodes = [b.strip() for b in raw_bc.split(",") if b.strip()]
                    res = self.service.checkout_books(reader_id, employee_id, barcodes)
                    print(f"[SUCCESS] BorrowSlipID: {res['borrow_slip_id']} | Due Date: {res['due_date']} | Books: {res['count']}")

                elif choice == "2":
                    barcode = input("Enter returned book barcode: ").strip()
                    condition = input("Return condition (GOOD / DAMAGED / LOST) [default GOOD]: ").strip().upper() or "GOOD"
                    res = self.service.checkin_book(barcode, condition)
                    print(f"[SUCCESS] Slip #{res['borrow_slip_id']} | Next Copy Status: {res['next_copy_status']} | Fine: {res['fine_amount']:,.0f} VND")
                    if res["reserved_for_reader"]:
                        print(f"-> Automatically held (FIFO) for ReaderID: {res['reserved_for_reader']}")

                elif choice == "3":
                    slip_id = int(input("Enter BorrowSlipID to renew: ").strip())
                    reader_id = int(input("Enter ReaderID: ").strip())
                    res = self.service.renew_loan(slip_id, reader_id)
                    print(f"[SUCCESS] Slip #{res['borrow_slip_id']} | New Due Date: {res['new_due_date']}")

                elif choice == "4":
                    reader_id = int(input("Enter ReaderID: ").strip())
                    isbn = input("Enter Book ISBN to reserve: ").strip()
                    res = self.service.reserve_book(reader_id, isbn)
                    print(f"[SUCCESS] ReservationID: #{res['reservation_id']} | Status: {res['status']} | Timestamp: {res['reservation_date']}")

                elif choice == "0":
                    print("Exiting Circulation Module.")
                    break
                else:
                    print("Invalid choice. Please select between 0 and 4.")
            except Exception as e:
                print(f"[ERROR] {e}")


if __name__ == "__main__":
    CirculationView().run()