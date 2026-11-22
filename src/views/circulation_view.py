from src.services.circulation_service import CirculationService
class CirculationView:
    def __init__(self, service: CirculationService = None):
        self.service = service or CirculationService()

    def run(self):
        while True:
            print("\n=== PHÂN HỆ LƯU THÔNG SÁCH & ĐẶT TRƯỚC (NGƯỜI 2) ===")
            print("1. Mượn sách (Check-out - UC-08)")
            print("2. Trả sách (Check-in - UC-09)")
            print("3. Gia hạn phiếu mượn (Renew - UC-10)")
            print("4. Đặt trước sách FIFO (Reserve - UC-11)")
            print("0. Thoát")

            choice = input("Chọn chức năng (0-4): ").strip()
            try:
                if choice == "1":
                    reader_id = int(input("Nhập ReaderID: ").strip())
                    employee_id = int(input("Nhập EmployeeID (thủ thư): ").strip())
                    raw_bc = input("Nhập các mã vạch sách (cách nhau bởi dấu phẩy, vd: BC-001,BC-002): ").strip()
                    barcodes = [b.strip() for b in raw_bc.split(",") if b.strip()]
                    res = self.service.checkout_books(reader_id, employee_id, barcodes)
                    print(f"[THÀNH CÔNG] Mã phiếu mượn: {res['borrow_slip_id']} | Hạn trả: {res['due_date']} | Số lượng: {res['count']}")

                elif choice == "2":
                    barcode = input("Nhập mã vạch sách trả: ").strip()
                    condition = input("Tình trạng sách (GOOD / DAMAGED / LOST) [mặc định GOOD]: ").strip().upper() or "GOOD"
                    res = self.service.checkin_book(barcode, condition)
                    print(f"[THÀNH CÔNG] Phiếu #{res['borrow_slip_id']} | Trạng thái bản sao mới: {res['next_copy_status']} | Tiền phạt phát sinh: {res['fine_amount']:,.0f} VND")
                    if res["reserved_for_reader"]:
                        print(f"-> Đã tự động giữ chỗ FIFO cho ReaderID: {res['reserved_for_reader']}")

                elif choice == "3":
                    slip_id = int(input("Nhập BorrowSlipID cần gia hạn: ").strip())
                    reader_id = int(input("Nhập ReaderID: ").strip())
                    res = self.service.renew_loan(slip_id, reader_id)
                    print(f"[THÀNH CÔNG] Phiếu #{res['borrow_slip_id']} | Hạn trả mới: {res['new_due_date']}")

                elif choice == "4":
                    reader_id = int(input("Nhập ReaderID: ").strip())
                    isbn = input("Nhập ISBN đầu sách cần đặt trước: ").strip()
                    res = self.service.reserve_book(reader_id, isbn)
                    print(f"[THÀNH CÔNG] Mã đặt trước: #{res['reservation_id']} | Trạng thái: {res['status']} | Thời gian: {res['reservation_date']}")

                elif choice == "0":
                    print("Tạm biệt!")
                    break
                else:
                    print("Lựa chọn không hợp lệ, vui lòng chọn từ 0 đến 4.")
            except Exception as e:
                print(f"[LỖI] {e}")

if __name__ == "__main__":
    CirculationView().run()
