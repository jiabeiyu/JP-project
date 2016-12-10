Database name: stock

CREATE TABLE info(
id INT,
time_quote VARCHAR(100),
info VARCHAR(500));


CREATE TABLE transact(
id INT NOT NULL PRIMARY KEY,
time_quote VARCHAR(100),
result VARCHAR(50),
price VARCHAR(30),
size VARCHAR(30),
amount INT,
value double precision,
avgr double precision);


CREATE TABLE strat(
id VARCHAR(30),
info VARCHAR(500));


CREATE TABLE user_info(
name VARCHAR(50),
pass VARCHAR(300)
PRIMARY KEY (name));