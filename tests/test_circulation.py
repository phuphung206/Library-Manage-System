import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from src.services.circulation_service import CirculationService


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_config_value.side_effect = lambda key, default: {
        "MAX_BORROW_BOOKS": 5,
        "MAX_BORROW_DAYS": 14,
        "MAX_RENEWAL_TIMES": 2,
        "RESERVATION_HOLD_HOURS": 48,
        "FINE_PER_DAY_VND": 5000,
    }.get(key, default)
    return repo


# --- 1. CHECK-OUT TESTS (UC-08) ---
def test_checkout_success(mock_repo):
    mock_repo.get_reader_info.return_value = (1, "Nguyen Van A", "a@gmail.com", "ACTIVE")
    mock_repo.get_unpaid_fines_total.return_value = 0.0
    mock_repo.count_active_borrowed_books.return_value = 2
    mock_repo.get_copy_info.return_value = ("BC-001", "978-0132350884", "A1", "AVAILABLE")
    expected_due = datetime.now() + timedelta(days=14)
    mock_repo.execute_checkout.return_value = (101, expected_due)

    service = CirculationService(repo=mock_repo)
    result = service.checkout_books(reader_id=1, employee_id=10, barcodes=["BC-001"])

    assert result["borrow_slip_id"] == 101
    assert result["count"] == 1


def test_checkout_fail_exceed_max_books(mock_repo):
    mock_repo.get_reader_info.return_value = (1, "Nguyen Van A", "a@gmail.com", "ACTIVE")
    mock_repo.get_unpaid_fines_total.return_value = 0.0
    mock_repo.count_active_borrowed_books.return_value = 5

    service = CirculationService(repo=mock_repo)
    with pytest.raises(ValueError, match="Borrowing quota exceeded"):
        service.checkout_books(reader_id=1, employee_id=10, barcodes=["BC-002"])


def test_checkout_fail_unpaid_fines(mock_repo):
    mock_repo.get_reader_info.return_value = (1, "Nguyen Van A", "a@gmail.com", "ACTIVE")
    mock_repo.get_unpaid_fines_total.return_value = 15000.0

    service = CirculationService(repo=mock_repo)
    with pytest.raises(ValueError, match="15,000 VND in unpaid fines"):
        service.checkout_books(reader_id=1, employee_id=10, barcodes=["BC-001"])


# --- 2. CHECK-IN & FIFO QUEUE TESTS (UC-09) ---
def test_checkin_assigns_fifo_reservation(mock_repo):
    mock_repo.execute_checkin.return_value = {
        "borrow_slip_id": 101,
        "fine_amount": 0.0,
        "next_copy_status": "RESERVED",
        "reserved_for_reader": 2,
    }
    service = CirculationService(repo=mock_repo)
    res = service.checkin_book(barcode="BC-001", return_condition="GOOD")

    assert res["next_copy_status"] == "RESERVED"
    assert res["reserved_for_reader"] == 2


# --- 3. LOAN RENEWAL TESTS (UC-10) ---
def test_renew_loan_success(mock_repo):
    mock_repo.get_unpaid_fines_total.return_value = 0.0
    borrow_date = datetime.now() - timedelta(days=5)
    due_date = borrow_date + timedelta(days=14)

    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [
        (borrow_date, due_date, "BORROWED"),
        (0,),
    ]
    mock_repo.conn.cursor.return_value = mock_cursor

    service = CirculationService(repo=mock_repo)
    res = service.renew_loan(borrow_slip_id=101, reader_id=1)

    assert res["borrow_slip_id"] == 101
    assert res["new_due_date"] == due_date + timedelta(days=14)


def test_renew_loan_fail_has_reservation(mock_repo):
    mock_repo.get_unpaid_fines_total.return_value = 0.0
    borrow_date = datetime.now() - timedelta(days=5)
    due_date = borrow_date + timedelta(days=14)

    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [
        (borrow_date, due_date, "BORROWED"),
        (1,),
    ]
    mock_repo.conn.cursor.return_value = mock_cursor

    service = CirculationService(repo=mock_repo)
    with pytest.raises(ValueError, match="active reservation queue"):
        service.renew_loan(borrow_slip_id=101, reader_id=1)


# --- 4. FIFO RESERVATION TESTS (UC-11) ---
def test_reserve_book_success(mock_repo):
    mock_repo.get_reader_info.return_value = (1, "Nguyen Van A", "a@gmail.com", "ACTIVE")
    mock_repo.get_unpaid_fines_total.return_value = 0.0

    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [
        (0,),
        (0,),
        (55,),
    ]
    mock_repo.conn.cursor.return_value = mock_cursor

    service = CirculationService(repo=mock_repo)
    res = service.reserve_book(reader_id=1, isbn="978-0132350884")

    assert res["reservation_id"] == 55
    assert res["status"] == "WAITING"


def test_reserve_book_fail_copy_available(mock_repo):
    mock_repo.get_reader_info.return_value = (1, "Nguyen Van A", "a@gmail.com", "ACTIVE")
    mock_repo.get_unpaid_fines_total.return_value = 0.0

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (2,)
    mock_repo.conn.cursor.return_value = mock_cursor

    service = CirculationService(repo=mock_repo)
    with pytest.raises(ValueError, match="currently available on the shelf"):
        service.reserve_book(reader_id=1, isbn="978-0132350884")