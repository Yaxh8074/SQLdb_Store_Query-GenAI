-- Create the database
-- DROP DATABASE atliq_tshirts;
CREATE DATABASE atliq_tshirts;
USE atliq_tshirts;

-- Create the t_shirts table
CREATE TABLE t_shirts (
    t_shirt_id INT AUTO_INCREMENT PRIMARY KEY,
    brand ENUM('Van Huesen', 'Levi', 'Nike', 'Adidas') NOT NULL,
    color ENUM('Red', 'Blue', 'Black', 'White') NOT NULL,
    size ENUM('XS', 'S', 'M', 'L', 'XL') NOT NULL,
    price INT CHECK (price BETWEEN 10 AND 50),
    stock_quantity INT NOT NULL,
    UNIQUE KEY brand_color_size (brand, color, size)
);

-- Create the discounts table
CREATE TABLE discounts (
    discount_id INT AUTO_INCREMENT PRIMARY KEY,
    t_shirt_id INT NOT NULL,
    pct_discount DECIMAL(5,2) CHECK (pct_discount BETWEEN 0 AND 100),
    FOREIGN KEY (t_shirt_id) REFERENCES t_shirts(t_shirt_id)
);

-- Create a stored procedure to populate the t_shirts table
DELIMITER $$
CREATE PROCEDURE PopulateTShirts()
BEGIN
    DECLARE counter INT DEFAULT 0;
    DECLARE max_records INT DEFAULT 100;
    DECLARE brand ENUM('Van Huesen', 'Levi', 'Nike', 'Adidas');
    DECLARE color ENUM('Red', 'Blue', 'Black', 'White');
    DECLARE size ENUM('XS', 'S', 'M', 'L', 'XL');
    DECLARE price INT;
    DECLARE stock INT;

    -- Seed the random number generator
    SET SESSION rand_seed1 = UNIX_TIMESTAMP();

    WHILE counter < max_records DO
        -- Generate random values
        SET brand = ELT(FLOOR(1 + RAND() * 4), 'Van Huesen', 'Levi', 'Nike', 'Adidas');
        SET color = ELT(FLOOR(1 + RAND() * 4), 'Red', 'Blue', 'Black', 'White');
        SET size = ELT(FLOOR(1 + RAND() * 5), 'XS', 'S', 'M', 'L', 'XL');
        SET price = FLOOR(10 + RAND() * 41);
        SET stock = FLOOR(10 + RAND() * 91);

        -- Attempt to insert a new record
        -- Duplicate brand, color, size combinations will be ignored due to the unique constraint
        BEGIN
            DECLARE CONTINUE HANDLER FOR 1062 BEGIN END;  -- Handle duplicate key error
            INSERT INTO t_shirts (brand, color, size, price, stock_quantity)
            VALUES (brand, color, size, price, stock);
            SET counter = counter + 1;
        END;
    END WHILE;
END$$
DELIMITER ;

-- Call the stored procedure to populate the t_shirts table
CALL PopulateTShirts();

-- Clear any partial data if necessary (optional)
-- DELETE FROM discounts; 

-- Insert discounts for the first 10 valid t-shirt IDs found in the table
INSERT INTO discounts (t_shirt_id, pct_discount)
SELECT t_shirt_id, 10.00 FROM t_shirts LIMIT 1;

-- To insert multiple specific discounts for existing shirts:
INSERT INTO discounts (t_shirt_id, pct_discount)
SELECT t_shirt_id, 15.00 FROM t_shirts WHERE t_shirt_id > (SELECT MIN(t_shirt_id) FROM t_shirts) LIMIT 9;