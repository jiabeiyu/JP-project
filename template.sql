Database name: stock

CREATE TABLE transact(
time_quote VARCHAR(100),
result VARCHAR(50),
price VARCHAR(30),
size VARCHAR(30));

CREATE TABLE info(
time_quote VARCHAR(100),
info VARCHAR(500));

CREATE TABLE strat(
id VARCHAR(30),
info VARCHAR(500));