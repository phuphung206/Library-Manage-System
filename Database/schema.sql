USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'library_management_system')
BEGIN
    CREATE DATABASE library_management_system;
END
GO

USE library_management_system;
GO

-- 1. Bảng Người dùng (Độc giả, Thủ thư, Admin)
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    card_number VARCHAR(20) UNIQUE NOT NULL,
    full_name NVARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    identity_number VARCHAR(30) UNIQUE NOT NULL,
    address NVARCHAR(MAX),
    role VARCHAR(20) NOT NULL DEFAULT 'MEMBER' 
        CONSTRAINT chk_user_role CHECK (role IN ('MEMBER', 'LIBRARIAN', 'ADMIN')),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' 
        CONSTRAINT chk_user_status CHECK (status IN ('ACTIVE', 'LOCKED', 'EXPIRED')),
    membership_expiry_date DATE,
    created_at DATETIME2 DEFAULT SYSDATETIME()
);

-- 2. Bảng Thể loại sách
CREATE TABLE categories (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name NVARCHAR(100) UNIQUE NOT NULL,
    description NVARCHAR(MAX)
);

-- 3. Bảng Nhà xuất bản
CREATE TABLE publishers (
    publisher_id INT IDENTITY(1,1) PRIMARY KEY,
    publisher_name NVARCHAR(150) NOT NULL,
    address NVARCHAR(MAX),
    contact_email VARCHAR(100)
);

-- 4. Bảng Tác giả
CREATE TABLE authors (
    author_id INT IDENTITY(1,1) PRIMARY KEY,
    author_name NVARCHAR(150) NOT NULL,
    biography NVARCHAR(MAX)
);

-- 5. Bảng Đầu sách (Chứa thông tin mô tả sách chung)
CREATE TABLE book_titles (
    book_id INT IDENTITY(1,1) PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title NVARCHAR(255) NOT NULL,
    category_id INT NULL REFERENCES categories(category_id) ON DELETE SET NULL,
    publisher_id INT NULL REFERENCES publishers(publisher_id) ON DELETE SET NULL,
    publication_year INT,
    summary NVARCHAR(MAX),
    cover_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_deleted BIT NOT NULL DEFAULT 0
);

-- 6. Bảng Trung gian Đầu sách & Tác giả (N-N)
CREATE TABLE book_authors (
    book_id INT NOT NULL REFERENCES book_titles(book_id) ON DELETE CASCADE,
    author_id INT NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- 7. Bảng Bản sao vật lý (Mỗi cuốn sách thực tế trên kệ)
CREATE TABLE book_copies (
    copy_id INT IDENTITY(1,1) PRIMARY KEY,
    book_id INT NOT NULL REFERENCES book_titles(book_id) ON DELETE CASCADE,
    barcode VARCHAR(50) UNIQUE NOT NULL,
    zone NVARCHAR(50), 
    shelf NVARCHAR(50), 
    floor NVARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CONSTRAINT chk_copy_status CHECK (status IN ('AVAILABLE', 'BORROWED', 'RESERVED', 'DAMAGED', 'LOST'))
);

-- 8. Bảng Phiếu mượn/trả
CREATE TABLE loan_transactions (
    loan_id INT IDENTITY(1,1) PRIMARY KEY,
    copy_id INT NOT NULL REFERENCES book_copies(copy_id) ON DELETE NO ACTION,
    member_id INT NOT NULL REFERENCES users(user_id) ON DELETE NO ACTION,
    checkout_librarian_id INT NULL REFERENCES users(user_id) ON DELETE NO ACTION,
    checkin_librarian_id INT NULL REFERENCES users(user_id) ON DELETE NO ACTION,
    borrow_date DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    due_date DATETIME2 NOT NULL,
    return_date DATETIME2 NULL,
    renewal_count INT NOT NULL DEFAULT 0,
    return_condition VARCHAR(20) NULL CONSTRAINT chk_return_condition CHECK (return_condition IN ('GOOD', 'DAMAGED', 'LOST')),
    status VARCHAR(20) NOT NULL DEFAULT 'BORROWED' CONSTRAINT chk_loan_status CHECK (status IN ('BORROWED', 'RETURNED', 'OVERDUE'))
);

-- 9. Bảng Hàng đợi đặt trước (FIFO)
CREATE TABLE reservations (
    reservation_id INT IDENTITY(1,1) PRIMARY KEY,
    book_id INT NOT NULL REFERENCES book_titles(book_id) ON DELETE CASCADE,
    member_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_copy_id INT NULL REFERENCES book_copies(copy_id) ON DELETE NO ACTION,
    reservation_date DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    hold_until DATETIME2 NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'WAITING'
        CONSTRAINT chk_res_status CHECK (status IN ('WAITING', 'READY_FOR_PICKUP', 'FULFILLED', 'CANCELLED', 'EXPIRED'))
);

-- 10. Bảng Tiền phạt
CREATE TABLE fines (
    fine_id INT IDENTITY(1,1) PRIMARY KEY,
    loan_id INT NOT NULL REFERENCES loan_transactions(loan_id) ON DELETE CASCADE,
    member_id INT NOT NULL REFERENCES users(user_id) ON DELETE NO ACTION,
    fine_type VARCHAR(20) NOT NULL CONSTRAINT chk_fine_type CHECK (fine_type IN ('OVERDUE', 'DAMAGED', 'LOST')),
    overdue_days INT DEFAULT 0,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPAID' CONSTRAINT chk_fine_status CHECK (status IN ('UNPAID', 'PAID')),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

-- 11. Bảng Thanh toán biên lai
CREATE TABLE fine_payments (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    fine_id INT NOT NULL REFERENCES fines(fine_id) ON DELETE NO ACTION,
    librarian_id INT NULL REFERENCES users(user_id) ON DELETE NO ACTION,
    payment_method VARCHAR(20) NOT NULL CONSTRAINT chk_payment_method CHECK (payment_method IN ('CASH', 'ONLINE')),
    amount_paid DECIMAL(10, 2) NOT NULL,
    receipt_code VARCHAR(50) UNIQUE NOT NULL,
    payment_date DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

-- 12. Bảng Thông báo (Email/Push notification)
CREATE TABLE notifications (
    notification_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(30) NOT NULL CONSTRAINT chk_notif_type CHECK (notification_type IN ('DUE_REMINDER', 'OVERDUE_ALERT', 'RESERVATION_READY')),
    title NVARCHAR(255) NOT NULL,
    message NVARCHAR(MAX) NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    sent_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

-- 13. Bảng Cấu hình tham số hệ thống
CREATE TABLE system_configs (
    config_key VARCHAR(50) PRIMARY KEY,
    config_value NVARCHAR(100) NOT NULL,
    description NVARCHAR(255),
    updated_by INT NULL REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at DATETIME2 DEFAULT SYSDATETIME()
);
GO

-- 14. CHỈ MỤC (INDEXES) Tối ưu hóa tốc độ truy vấn
CREATE INDEX idx_book_title ON book_titles(title);
CREATE INDEX idx_author_name ON authors(author_name);
CREATE INDEX idx_copy_status ON book_copies(book_id, status);
CREATE INDEX idx_loan_member_status ON loan_transactions(member_id, status);
CREATE INDEX idx_reservation_fifo ON reservations(book_id, status, reservation_date);
GO

-- 15. Khởi tạo dữ liệu cấu hình nghiệp vụ mặc định
INSERT INTO system_configs (config_key, config_value, description) VALUES
('MAX_BORROW_BOOKS', N'5', N'Số cuốn sách tối đa độc giả được mượn cùng lúc'),
('MAX_BORROW_DAYS', N'14', N'Số ngày mượn sách tối đa cho mỗi lượt'),
('MAX_RENEWAL_TIMES', N'2', N'Số lần gia hạn sách tối đa'),
('RESERVATION_HOLD_HOURS', N'48', N'Thời gian tối đa giữ sách đặt trước tại quầy (giờ)'),
('FINE_PER_DAY_VND', N'5000', N'Đơn giá phạt quá hạn mỗi ngày tính bằng VNĐ');
GO