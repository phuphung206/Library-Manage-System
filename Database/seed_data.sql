USE master;
GO

-- 1. XÓA CSDL CŨ ĐỂ LÀM SẠCH HOÀN TOÀN
IF DB_ID('library_management_system') IS NOT NULL
BEGIN
    ALTER DATABASE library_management_system SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE library_management_system;
END
GO

-- 2. TẠO LẠI CSDL
CREATE DATABASE library_management_system;
GO

USE library_management_system;
GO

-- 3. TẠO CẤU TRÚC BẢNG (Đã bọc ngoặc vuông chuẩn xác)
CREATE TABLE [system_configs] (
    [config_key] VARCHAR(50) PRIMARY KEY, [config_value] VARCHAR(255), [description] NVARCHAR(255), [updated_at] DATETIME DEFAULT GETDATE()
);

CREATE TABLE [users] (
    [user_id] INT IDENTITY(1,1) PRIMARY KEY, [username] VARCHAR(50), [password_hash] VARCHAR(255), [full_name] NVARCHAR(100), [identity_number] VARCHAR(20), [phone] VARCHAR(15), [email] VARCHAR(100), [address] NVARCHAR(255), [role] VARCHAR(20), [status] VARCHAR(20), [card_number] VARCHAR(20), [membership_expiry_date] DATE, [created_at] DATETIME DEFAULT GETDATE()
);

CREATE TABLE [categories] (
    [category_id] INT IDENTITY(1,1) PRIMARY KEY, [name] NVARCHAR(100), [description] NVARCHAR(255)
);

CREATE TABLE [authors] (
    [author_id] INT IDENTITY(1,1) PRIMARY KEY, [author_name] NVARCHAR(100), [bio] NVARCHAR(500)
);

CREATE TABLE [book_titles] (
    [title_id] INT IDENTITY(1,1) PRIMARY KEY, [title] NVARCHAR(255), [category_id] INT, [publisher] NVARCHAR(100), [publish_year] INT, [description] NVARCHAR(500), [created_at] DATETIME DEFAULT GETDATE()
);

CREATE TABLE [book_authors] (
    [title_id] INT, [author_id] INT, PRIMARY KEY ([title_id], [author_id])
);

CREATE TABLE [book_copies] (
    [copy_id] INT IDENTITY(1,1) PRIMARY KEY, [title_id] INT, [barcode] VARCHAR(50), [status] VARCHAR(20), [condition] VARCHAR(20), [created_at] DATETIME DEFAULT GETDATE()
);

CREATE TABLE [loan_transactions] (
    [loan_id] INT IDENTITY(1,1) PRIMARY KEY, [user_id] INT, [copy_id] INT, [borrow_date] DATE, [due_date] DATE, [return_date] DATE NULL, [status] VARCHAR(50), [created_at] DATETIME DEFAULT GETDATE()
);

CREATE TABLE [fines] (
    [fine_id] INT IDENTITY(1,1) PRIMARY KEY, [loan_id] INT, [user_id] INT, [amount] DECIMAL(18,2), [fine_reason] VARCHAR(100), [status] VARCHAR(20), [created_at] DATETIME DEFAULT GETDATE()
);

CREATE TABLE [fine_payments] (
    [payment_id] INT IDENTITY(1,1) PRIMARY KEY, [fine_id] INT, [amount_paid] DECIMAL(18,2), [payment_method] VARCHAR(50), [payment_date] DATETIME, [receipt_number] VARCHAR(50)
);

CREATE TABLE [BORROW_SLIP] (
    [BorrowSlipID] INT IDENTITY(1,1) PRIMARY KEY, [ReaderID] INT, [EmployeeID] INT, [BorrowDate] DATE, [DueDate] DATE, [ActualReturnDate] DATE NULL, [Status] VARCHAR(50)
);

CREATE TABLE [RESERVATION] (
    [ReservationID] INT IDENTITY(1,1) PRIMARY KEY, [ISBN] VARCHAR(50), [ReaderID] INT, [ReservationDate] DATETIME, [Status] VARCHAR(50)
);
GO

-- 4. BƠM DỮ LIỆU ĐẠI TRÀ (BIG DATA SEEDING)
INSERT INTO [system_configs] ([config_key], [config_value], [description]) VALUES 
('MAX_BORROW_BOOKS', '5', N'Số lượng sách tối đa được mượn'), 
('MAX_BORROW_DAYS', '14', N'Số ngày mượn tối đa'), 
('FINE_PER_DAY_VND', '5000', N'Tiền phạt mỗi ngày trễ hạn');

-- Thêm Users (Admin, Librarian, và 8 Members)
SET IDENTITY_INSERT [users] ON;
INSERT INTO [users] ([user_id], [username], [password_hash], [full_name], [identity_number], [phone], [email], [address], [role], [status], [card_number]) VALUES
(1, 'admin', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Phùng Gia Phú', '079012345678', '0901234567', 'phu.admin@library.com', N'Bình Thạnh, TP.HCM', 'ADMIN', 'ACTIVE', 'LIB-2026-001'),
(2, 'librarian_minh', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Trần Tuấn Minh', '079012345679', '0912345678', 'minh.lib@library.com', N'Quận 1, TP.HCM', 'LIBRARIAN', 'ACTIVE', 'LIB-2026-002'),
(3, 'sofia', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Sofia Perez', '079012345680', '0923456789', 'sofia@gmail.com', N'Quận 2, TP.HCM', 'MEMBER', 'ACTIVE', 'MEM-2026-001'),
(4, 'alex', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Alex Morgan', '079012345681', '0934567890', 'alex@gmail.com', N'Quận 7, TP.HCM', 'MEMBER', 'ACTIVE', 'MEM-2026-002'),
(5, 'jamie', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Jamie Chen', '079012345682', '0945678901', 'jamie@gmail.com', N'Gò Vấp, TP.HCM', 'MEMBER', 'LOCKED', 'MEM-2026-003'),
(6, 'hoang.nguyen', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Nguyễn Việt Hoàng', '079012345683', '0956789012', 'hoang@gmail.com', N'Quận 3, TP.HCM', 'MEMBER', 'ACTIVE', 'MEM-2026-004'),
(7, 'mai.le', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Lê Thị Mai', '079012345684', '0967890123', 'mai.le@gmail.com', N'Quận 5, TP.HCM', 'MEMBER', 'ACTIVE', 'MEM-2026-005'),
(8, 'tuan.tran', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW', N'Trần Quốc Tuấn', '079012345685', '0978901234', 'tuan.tran@gmail.com', N'Quận 10, TP.HCM', 'MEMBER', 'ACTIVE', 'MEM-2026-006');
SET IDENTITY_INSERT [users] OFF;

-- Thêm 7 Thể loại
SET IDENTITY_INSERT [categories] ON;
INSERT INTO [categories] ([category_id], [name], [description]) VALUES 
(1, N'Khoa học Máy tính', N'Lập trình, thuật toán, AI, dữ liệu'), 
(2, N'Tâm lý học', N'Khoa học hành vi, tư duy, não bộ'), 
(3, N'Kinh tế & Quản trị', N'Kinh doanh, chứng khoán, quản trị nhân sự'), 
(4, N'Tiểu thuyết viễn tưởng', N'Sci-Fi, phiêu lưu kỳ ảo ngoài vũ trụ'),
(5, N'Văn học Việt Nam', N'Truyện ngắn, tiểu thuyết đương đại'),
(6, N'Lịch sử & Khoa học', N'Lịch sử nhân loại, vũ trụ học'),
(7, N'Kỹ năng sống', N'Phát triển bản thân, giao tiếp');
SET IDENTITY_INSERT [categories] OFF;

-- Thêm 8 Tác giả
SET IDENTITY_INSERT [authors] ON;
INSERT INTO [authors] ([author_id], [author_name], [bio]) VALUES 
(1, N'Thomas H. Cormen', N'Giáo sư khoa học máy tính tại MIT.'), 
(2, N'Daniel Kahneman', N'Nhà tâm lý học, đoạt giải Nobel Kinh tế.'), 
(3, N'David Thomas', N'Tác giả nổi tiếng trong giới lập trình phần mềm.'), 
(4, N'Frank Herbert', N'Tiểu thuyết gia người Mỹ, tác giả của Dune.'),
(5, N'Robert C. Martin', N'Tác giả cuốn Clean Code (Uncle Bob).'),
(6, N'Nguyễn Nhật Ánh', N'Nhà văn nổi tiếng với tuổi thơ Việt Nam.'),
(7, N'Dale Carnegie', N'Chuyên gia nhân tế học, tác giả Đắc Nhân Tâm.'),
(8, N'Yuval Noah Harari', N'Giáo sư lịch sử, tác giả Sapiens.');
SET IDENTITY_INSERT [authors] OFF;

-- Thêm 9 Đầu sách
SET IDENTITY_INSERT [book_titles] ON;
INSERT INTO [book_titles] ([title_id], [title], [category_id], [publisher], [publish_year], [description]) VALUES 
(1, N'Introduction to Algorithms', 1, N'MIT Press', 2009, N'Sách giáo khoa kinh điển về thuật toán.'), 
(2, N'Thinking, Fast and Slow', 2, N'FSG', 2011, N'Phân tích 2 hệ thống tư duy.'), 
(3, N'The Pragmatic Programmer', 1, N'Addison-Wesley', 1999, N'Cẩm nang code thực chiến.'), 
(4, N'Dune', 4, N'Chilton Books', 1965, N'Kiệt tác khoa học viễn tưởng.'),
(5, N'Clean Code: A Handbook of Agile Software', 1, N'Prentice Hall', 2008, N'Cách viết mã nguồn sạch và dễ bảo trì.'),
(6, N'Mắt Biếc', 5, N'NXB Trẻ', 1990, N'Truyện dài về tình yêu tuổi học trò.'),
(7, N'Cho Tôi Xin Một Vé Đi Tuổi Thơ', 5, N'NXB Trẻ', 2008, N'Hồi ức tuổi thơ tuyệt đẹp.'),
(8, N'Đắc Nhân Tâm', 7, N'Simon & Schuster', 1936, N'Nghệ thuật thu phục lòng người.'),
(9, N'Sapiens: Lược Sử Loài Người', 6, N'Harper', 2011, N'Hành trình tiến hóa của nhân loại.');
SET IDENTITY_INSERT [book_titles] OFF;

INSERT INTO [book_authors] ([title_id], [author_id]) VALUES 
(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 6), (8, 7), (9, 8);

-- Thêm 18 Bản sao vật lý (để hiển thị kho sách)
SET IDENTITY_INSERT [book_copies] ON;
INSERT INTO [book_copies] ([copy_id], [title_id], [barcode], [status], [condition]) VALUES 
(1, 1, 'M-0382', 'BORROWED', 'GOOD'), (2, 1, 'M-0383', 'AVAILABLE', 'NEW'), 
(3, 2, 'M-0431', 'BORROWED', 'GOOD'), (4, 2, 'M-0432', 'AVAILABLE', 'GOOD'),
(5, 3, 'M-0894', 'BORROWED', 'OLD'),  (6, 3, 'M-0895', 'AVAILABLE', 'NEW'),
(7, 4, 'M-0954', 'AVAILABLE', 'GOOD'),(8, 4, 'M-0955', 'LOST', 'DAMAGED'),
(9, 5, 'M-1101', 'BORROWED', 'NEW'),  (10, 5, 'M-1102', 'AVAILABLE', 'GOOD'),
(11, 6, 'M-1201', 'AVAILABLE', 'NEW'), (12, 6, 'M-1202', 'BORROWED', 'GOOD'),
(13, 7, 'M-1301', 'AVAILABLE', 'OLD'), (14, 7, 'M-1302', 'AVAILABLE', 'GOOD'),
(15, 8, 'M-1401', 'BORROWED', 'GOOD'), (16, 8, 'M-1402', 'BORROWED', 'OLD'),
(17, 9, 'M-1501', 'AVAILABLE', 'NEW'), (18, 9, 'M-1502', 'AVAILABLE', 'NEW');
SET IDENTITY_INSERT [book_copies] OFF;

-- Thêm 10 Phiếu mượn (để bảng Dashboard và Circulation đầy ắp)
INSERT INTO [BORROW_SLIP] ([ReaderID], [EmployeeID], [BorrowDate], [DueDate], [ActualReturnDate], [Status]) VALUES 
(3, 1, GETDATE()-3, GETDATE()+11, NULL, 'BORROWED'), 
(4, 1, GETDATE()-1, GETDATE()+13, NULL, 'BORROWED'), 
(5, 2, GETDATE()-20, GETDATE()-6, NULL, 'OVERDUE'),
(6, 2, GETDATE()-14, GETDATE(), NULL, 'OVERDUE'), -- Vừa tới hạn hôm nay
(7, 1, GETDATE()-5, GETDATE()+9, NULL, 'BORROWED'),
(8, 1, GETDATE()-2, GETDATE()+12, NULL, 'BORROWED'),
(3, 2, GETDATE()-18, GETDATE()-4, NULL, 'OVERDUE'),
(4, 1, GETDATE()-10, GETDATE()+4, NULL, 'BORROWED'),
(6, 2, GETDATE()-30, GETDATE()-16, GETDATE()-15, 'RETURNED'), -- Đã trả
(7, 1, GETDATE()-25, GETDATE()-11, GETDATE()-10, 'RETURNED'); -- Đã trả

-- Thêm 5 Đặt trước (FIFO Queue)
INSERT INTO [RESERVATION] ([ISBN], [ReaderID], [ReservationDate], [Status]) VALUES 
('978-013235', 4, GETDATE()-2, 'WAITING'), 
('978-020183', 1, GETDATE(), 'READY'),
('978-000111', 8, GETDATE()-3, 'WAITING'),
('978-000222', 5, GETDATE()-1, 'READY'),
('978-000333', 6, GETDATE(), 'WAITING');
GO