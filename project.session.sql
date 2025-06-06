CREATE TABLE predictions_crop (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Year INT,
    Area VARCHAR(100),
    Item VARCHAR(100),
    pesticides_tonnes FLOAT,
    avg_temp FLOAT,
     average_rain_fall_mm_per_year FLOAT,
    prediction FLOAT
);
SELECT* from predictions_crop;
ALTER TABLE predictions_crop ADD COLUMN profit FLOAT;

DESCRIBE predictions_crop;

ALTER TABLE predictions_crop DROP COLUMN profit;
ALTER TABLE predictions_crop DROP COLUMN recommended_crops;
DESCRIBE signup1;
select* from signup1;
select* from stock_admin;
INSERT INTO stocks (stock_name, quantity, price, image_path)
VALUES ('Wheat', 100, 120.50, 'uploads/fert2.jpg');
SELECT* from stocks;

drop TABLE stock_admin;
CREATE TABLE crops_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL
);

CREATE TABLE stock_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,

    price DECIMAL(10, 2),
    stock INT,
    image VARCHAR(255)
);
DELETE FROM stock_admin WHERE id IN (1, 2, 3, 4);
INSERT INTO stock_admin (name, description, price, stock, image) VALUES
('HerbGrow Organic Fertilizer', 'Enhances herb and vegetable growth.', 350.00, 10, './Farmify_buy/uploads/fert1.jpg'),
('SuperBloom Flower Fertilizer', 'Boosts flower production.', 450.00, 60,'./Farmify_buy/uploads/fert2.jpg'),
('RootMax Phosphorus Fertilizer', 'Strengthens roots.', 550.00, 50, './Farmify_buy/uploads/fert3.jpg'),
('GreenWave All-Purpose Fertilizer', 'Balanced nutrients for crops.', 300.00, 45, './Farmify_buy/uploads/fert4.jpg');