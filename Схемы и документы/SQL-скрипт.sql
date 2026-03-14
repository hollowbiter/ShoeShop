-- 1. Справочные таблицы (Словари)
CREATE TABLE Roles (
    RoleId INTEGER PRIMARY KEY AUTOINCREMENT,
    RoleName TEXT NOT NULL UNIQUE
);

CREATE TABLE Categories (
    CategoryId INTEGER PRIMARY KEY AUTOINCREMENT,
    CategoryName TEXT NOT NULL UNIQUE
);

CREATE TABLE Manufacturers (
    ManufacturerId INTEGER PRIMARY KEY AUTOINCREMENT,
    ManufacturerName TEXT NOT NULL UNIQUE
);

CREATE TABLE Suppliers (
    SupplierId INTEGER PRIMARY KEY AUTOINCREMENT,
    SupplierName TEXT NOT NULL UNIQUE
);

CREATE TABLE Units (
    UnitId INTEGER PRIMARY KEY AUTOINCREMENT,
    UnitName TEXT NOT NULL UNIQUE
);

CREATE TABLE OrderStatuses (
    StatusId INTEGER PRIMARY KEY AUTOINCREMENT,
    StatusName TEXT NOT NULL UNIQUE
);

CREATE TABLE PickupPoints (
    PointId INTEGER PRIMARY KEY AUTOINCREMENT,
    Address TEXT NOT NULL
);

-- 2. Основные таблицы
CREATE TABLE Users (
    UserId INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT NOT NULL,
    Login TEXT NOT NULL UNIQUE,
    Password TEXT NOT NULL,
    RoleId INTEGER NOT NULL,
    FOREIGN KEY (RoleId) REFERENCES Roles(RoleId)
);

CREATE TABLE Products (
    ProductId INTEGER PRIMARY KEY AUTOINCREMENT,
    ArticleNumber TEXT NOT NULL UNIQUE,
    ProductName TEXT NOT NULL,
    Description TEXT,
    CategoryId INTEGER NOT NULL,
    ManufacturerId INTEGER NOT NULL,
    SupplierId INTEGER NOT NULL,
    UnitId INTEGER NOT NULL,
    Price REAL NOT NULL CHECK (Price >= 0), -- Стоимость не может быть отрицательной 
    MaxDiscount INTEGER DEFAULT 0,
    QuantityInStock INTEGER NOT NULL CHECK (QuantityInStock >= 0), -- Кол-во не может быть отрицательным 
    ImagePath TEXT,
    FOREIGN KEY (CategoryId) REFERENCES Categories(CategoryId),
    FOREIGN KEY (ManufacturerId) REFERENCES Manufacturers(ManufacturerId),
    FOREIGN KEY (SupplierId) REFERENCES Suppliers(SupplierId),
    FOREIGN KEY (UnitId) REFERENCES Units(UnitId)
);

CREATE TABLE Orders (
    OrderId INTEGER PRIMARY KEY, -- Номер заказа из импорта [cite: 23, 88]
    OrderDate TEXT NOT NULL,
    DeliveryDate TEXT NOT NULL,
    PointId INTEGER NOT NULL,
    ClientFullName TEXT,
    PickupCode INTEGER NOT NULL,
    StatusId INTEGER NOT NULL,
    FOREIGN KEY (PointId) REFERENCES PickupPoints(PointId),
    FOREIGN KEY (StatusId) REFERENCES OrderStatuses(StatusId)
);

-- 3. Состав заказа (Многие-ко-многим для 3НФ)
CREATE TABLE OrderItems (
    OrderId INTEGER NOT NULL,
    ProductArticle TEXT NOT NULL,
    Quantity INTEGER NOT NULL,
    PRIMARY KEY (OrderId, ProductArticle),
    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId),
    FOREIGN KEY (ProductArticle) REFERENCES Products(ArticleNumber)
);