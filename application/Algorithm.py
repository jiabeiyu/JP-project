import urllib2
import json
import random
import time
import threading
import psycopg2

QUERY = "http://localhost:8080/query?id={}"
ORDER = "http://localhost:8080/order?id={}&side=sell&qty={}&price={}"

ORDER_DISCOUNT = 10
ORDER_SIZE = 100
INVENTORY = 0

N = 5

qty = INVENTORY
pnl = 0


class UseThread(threading.Thread):
    def __init__(self, quantity):
        threading.Thread.__init__(self)
        self.quantity = quantity

    def run(self):
        try:
            conn = psycopg2.connect("dbname='stock' user='Linnan' host='localhost' password='' ")
            print 'get connect'
        except:
            print "I am unable to connect to the database"
            return 1

        cur = conn.cursor()
        global qty
        global pnl
        qty = self.quantity

        delet1 = "DELETE FROM info;"
        delet2 = "DELETE FROM transact;"
        try:
            cur.execute(delet1)
            conn.commit()
            cur.execute(delet2)
            conn.commit()
        except:
            print "I can't write data"
            conn.rollback()

        def insert_info(data_id, time_stamp, message, cur):
            # insert server feedback to database
            query = "INSERT INTO info (id, time_quote, info) VALUES ('{}', '{}', '{}');".format(data_id, time_stamp, message)
            print query
            try:
                cur.execute(query)
                conn.commit()
            except:
                print "I can't write data"
                conn.rollback()

        def insert_trans(data_id, time_stamp, result, price, size, cur):
            # insert server feedback to database
            query = "INSERT INTO transact (id, time_quote, result, price, size) VALUES ('{}', '{}', '{}', '{}', '{}');".\
                format(data_id, time_stamp, result, price, size)
            print query
            try:
                cur.execute(query)
                conn.commit()
            except:
                print "I can't write data"
                conn.rollback()

        # Repeat the strategy until we run out of shares.
        db_id = 0
        while qty > 0:
            # Query the price once every N seconds.
            for _ in xrange(N):
                time.sleep(1)
                quote = json.loads(urllib2.urlopen(QUERY.format(random.random())).read())
                price = float(quote['top_bid']['price'])
                time_mark = str(quote['timestamp'])
                print "Quoted at %s" % price
                insert_info(db_id, time_mark, "Quoted at %s" % price, cur)
                db_id += 1

            # Attempt to execute a sell order.
            order_args = (ORDER_SIZE, price - ORDER_DISCOUNT)
            print "Executing 'sell' of {:,} @ {:,}".format(*order_args)
            exec_time = str(json.loads(urllib2.urlopen(QUERY.format(random.random())).read())['timestamp'])
            insert_info(db_id, exec_time, "Executing Sell of {:,} at price {:,}".format(*order_args), cur)
            db_id += 1

            url = ORDER.format(random.random(), *order_args)
            order = json.loads(urllib2.urlopen(url).read())
            fin_time = order['timestamp']

            # Update the PnL if the order was filled.
            if order['avg_price'] > 0:
                price = order['avg_price']
                notional = float(price * ORDER_SIZE)
                pnl += notional
                qty -= ORDER_SIZE
                print "Sold {:,} for ${:,}/share, ${:,} notional".format(ORDER_SIZE, price, notional)
                insert_trans(db_id, fin_time, "success", price, ORDER_SIZE, cur)
                db_id += 1
                print "PnL ${:,}, Qty {:,}".format(pnl, qty)
                insert_trans(db_id, fin_time, "PnL ${:,}, Qty {:,}".format(pnl, qty), " ", " ", cur)
                db_id += 1
            else:
                print "Unfilled order; $%s total, %s qty" % (pnl, qty)
                insert_trans(db_id, fin_time, "fail", "none", ORDER_SIZE, cur)
                db_id += 1

            time.sleep(1)
        # Position is liquididated!
        print "Liquidated position for ${:,}".format(pnl)
        insert_trans(db_id, fin_time, "Liquidated position for ${:,}".format(pnl), " ", " ", cur)
        db_id += 1
