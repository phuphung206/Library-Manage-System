USE library_management_system;
GO

-- ==========================================
-- 1. XÓA DỮ LIỆU CŨ ĐỂ KHÔNG BỊ TRÙNG LẶP (Chạy từ dưới lên trên để tránh lỗi khóa ngoại)
-- ==========================================
DELETE FROM fine_payments;
DELETE FROM fines;
DELETE FROM loan_transactions;
DELETE FROM book_copies;
DELETE FROM book_authors;
DELETE FROM book_titles;
DELETE FROM authors;
DELETE FROM categories;
DELETE FROM notifications;
DELETE FROM system_configs;
DELETE FROM users;
GO

-- ==========================================
-- 2. THÊM DỮ LIỆU BẢNG SYSTEM CONFIGS
-- ==========================================
INSERT INTO system_configs (config_key, config_value, description, updated_at) VALUES
('MAX_BORROW_BOOKS', '5', N'Số lượng sách tối đa được mượn cùng lúc', GETDATE()),
('MAX_BORROW_DAYS', '14', N'Số ngày mượn tối đa', GETDATE()),
('FINE_PER_DAY_VND', '5000', N'Số tiền phạt mỗi ngày trễ hạn (VNĐ)', GETDATE());
GO

-- ==========================================
-- 3. THÊM DỮ LIỆU TÀI KHOẢN NGƯỜI DÙNG (USERS)
-- ==========================================
SET IDENTITY_INSERT users ON;
INSERT INTO users (user_id, username, password_hash, full_name, identity_number, phone, email, address, role, status, created_at) VALUES
(1, 'admin', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Phùng Gia Phú', '079012345678', '0901234567', 'phu.admin@library.com', N'Quận Bình Thạnh, TP.HCM', 'ADMIN', 'ACTIVE', GETDATE()),
(2, 'librarian_minh', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Trần Tuấn Minh', '079012345679', '0912345678', 'minh.lib@library.com', N'Quận 1, TP.HCM', 'LIBRARIAN', 'ACTIVE', GETDATE()),
(3, 'member_sofia', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Sofia Perez', '079012345680', '0923456789', 'sofia@gmail.com', N'Quận 2, TP.HCM', 'MEMBER', 'ACTIVE', GETDATE()),
(4, 'member_alex', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Alex Morgan', '079012345681', '0934567890', 'alex@gmail.com', N'Quận 7, TP.HCM', 'MEMBER', 'ACTIVE', GETDATE()),
(5, 'member_jamie', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Jamie Chen', '079012345682', '0945678901', 'jamie@gmail.com', N'Gò Vấp, TP.HCM', 'MEMBER', 'LOCKED', GETDATE());
SET IDENTITY_INSERT users OFF;
GO

-- ==========================================
-- 4. THÊM THỂ LOẠI (CATEGORIES) VÀ TÁC GIẢ (AUTHORS)
-- ==========================================
SET IDENTITY_INSERT categories ON;
INSERT INTO categories (category_id, name, description) VALUES
(1, N'Khoa học Máy tính', N'Sách lập trình, thuật toán, AI, dữ liệu'),
(2, N'Tâm lý học', N'Khoa học hành vi, tư duy, phát triển bản thân'),
(3, N'Kinh tế & Quản trị', N'Tài chính, kinh doanh, chứng khoán'),
(4, N'Tiểu thuyết viễn tưởng', N'Sci-Fi, phiêu lưu kỳ ảo');
SET IDENTITY_INSERT categories OFF;

SET IDENTITY_INSERT authors ON;
INSERT INTO authors (author_id, author_name, bio) VALUES
(1, N'Thomas H. Cormen', N'Giáo sư khoa học máy tính tại MIT.'),
(2, N'Daniel Kahneman', N'Nhà tâm lý học, đoạt giải Nobel Kinh tế.'),
(3, N'David Thomas', N'Tác giả nổi tiếng trong giới lập trình phần mềm.'),
(4, N'Frank Herbert', N'Tiểu thuyết gia người Mỹ, tác giả của Dune.');
SET IDENTITY_INSERT authors OFF;
GO

-- ==========================================
-- 5. THÊM ĐẦU SÁCH (BOOK TITLES) VÀ BẢNG TRUNG GIAN SÁCH-TÁC GIẢ
-- ==========================================
SET IDENTITY_INSERT book_titles ON;
INSERT INTO book_titles (title_id, title, category_id, publisher, publish_year, description, created_at) VALUES
(1, N'Introduction to Algorithms', 1, N'MIT Press', 2009, N'Sách giáo khoa kinh điển về thuật toán dành cho sinh viên IT.', GETDATE()),
(2, N'Thinking, Fast and Slow', 2, N'Farrar, Straus and Giroux', 2011, N'Cuốn sách phân tích sâu sắc về 2 hệ thống tư duy của con người.', GETDATE()),
(3, N'The Pragmatic Programmer', 1, N'Addison-Wesley', 1999, N'Cẩm nang nâng cao kỹ năng code và tư duy làm nghề thực chiến.', GETDATE()),
(4, N'Dune', 4, N'Chilton Books', 1965, N'Kiệt tác khoa học viễn tưởng kinh điển mọi thời đại.', GETDATE());
SET IDENTITY_INSERT book_titles OFF;

INSERT INTO book_authors (title_id, author_id) VALUES
(1, 1), (2, 2), (3, 3), (4, 4);
GO

-- ==========================================
-- 6. THÊM CÁC CUỐN SÁCH VẬT LÝ (BOOK COPIES)
-- ==========================================
SET IDENTITY_INSERT book_copies ON;
INSERT INTO book_copies (copy_id, title_id, barcode, status, condition, created_at) VALUES
(1, 1, 'M-0382', 'BORROWED', 'GOOD', GETDATE()),
(2, 1, 'M-0383', 'AVAILABLE', 'NEW', GETDATE()),
(3, 2, 'M-0431', 'BORROWED', 'GOOD', GETDATE()),
(4, 3, 'M-0894', 'BORROWED', 'OLD', GETDATE()),
(5, 4, 'M-0954', 'AVAILABLE', 'GOOD', GETDATE()),
(6, 4, 'M-0955', 'LOST', 'DAMAGED', GETDATE());
SET IDENTITY_INSERT book_copies OFF;
GO

-- ==========================================
-- 7. THÊM GIAO DỊCH MƯỢN TRẢ (LOAN TRANSACTIONS)
-- ==========================================
SET IDENTITY_INSERT loan_transactions ON;
INSERT INTO loan_transactions (loan_id, user_id, copy_id, borrow_date, due_date, return_date, status, created_at) VALUES
(1, 3, 1, DATEADD(day, -5, GETDATE()), DATEADD(day, 0, GETDATE()), NULL, 'BORROWED', GETDATE()), -- Tới hạn hôm nay (Today)
(2, 4, 3, DATEADD(day, -10, GETDATE()), DATEADD(day, 1, GETDATE()), NULL, 'BORROWED', GETDATE()), -- Tới hạn ngày mai (Tomorrow)
(3, 5, 4, DATEADD(day, -20, GETDATE()), DATEADD(day, -6, GETDATE()), NULL, 'OVERDUE', GETDATE()),  -- Đã trễ hạn (Overdue)
(4, 3, 5, DATEADD(day, -30, GETDATE()), DATEADD(day, -16, GETDATE()), DATEADD(day, -15, GETDATE()), 'RETURNED', GETDATE()); -- Đã trả sách
SET IDENTITY_INSERT loan_transactions OFF;
GO

-- ==========================================
-- 8. THÊM TIỀN PHẠT (FINES) VÀ BIÊN LAI THANH TOÁN (FINE PAYMENTS)
-- ==========================================
SET IDENTITY_INSERT fines ON;
INSERT INTO fines (fine_id, loan_id, user_id, amount, fine_reason, status, created_at) VALUES
(1, 3, 5, 30000, 'LATE_RETURN', 'UNPAID', GETDATE()), 
(2, 4, 3, 5000, 'LATE_RETURN', 'PAID', GETDATE());    
SET IDENTITY_INSERT fines OFF;

SET IDENTITY_INSERT fine_payments ON;
INSERT INTO fine_payments (payment_id, fine_id, amount_paid, payment_method, payment_date, receipt_number) VALUES
(1, 2, 5000, 'CASH', DATEADD(day, -15, GETDATE()), 'REC-2026-001');
SET IDENTITY_INSERT fine_payments OFF;
GO