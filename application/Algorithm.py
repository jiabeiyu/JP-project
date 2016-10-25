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
        db_id = 0

        def insert(db_id, message, cur):
            # insert server feedback to database
            query = "INSERT INTO info (id, info) VALUES ({}, '{}');".format(db_id, message)
            print query
            try:
                cur.execute(query)
                conn.commit()
            except:
                print "I can't write data"
                conn.rollback()

        # Repeat the strategy until we run out of shares.
        while qty > 0:
            # Query the price once every N seconds.
            for _ in xrange(N):
                time.sleep(1)
                quote = json.loads(urllib2.urlopen(QUERY.format(random.random())).read())
                price = float(quote['top_bid']['price'])
                print "Quoted at %s" % price
                print db_id
                insert(db_id, "Quoted at %s" % price, cur)
                db_id += 1

            # Attempt to execute a sell order.
            order_args = (ORDER_SIZE, price - ORDER_DISCOUNT)
            print "Executing 'sell' of {:,} @ {:,}".format(*order_args)
            insert(db_id, "Executing Sell of {:,} at price {:,}".format(*order_args), cur)
            db_id += 1
            url = ORDER.format(random.random(), *order_args)
            order = json.loads(urllib2.urlopen(url).read())

            # Update the PnL if the order was filled.
            if order['avg_price'] > 0:
                price = order['avg_price']
                notional = float(price * ORDER_SIZE)
                pnl += notional
                qty -= ORDER_SIZE
                print "Sold {:,} for ${:,}/share, ${:,} notional".format(ORDER_SIZE, price, notional)
                insert(db_id, "Sold {:,} for ${:,}/share, ${:,} notional".format(ORDER_SIZE, price, notional), cur)
                db_id += 1
                print "PnL ${:,}, Qty {:,}".format(pnl, qty)
                insert(db_id, "PnL ${:,}, Qty {:,}".format(pnl, qty), cur)
                db_id += 1
            else:
                print "Unfilled order; $%s total, %s qty" % (pnl, qty)
                insert(db_id, "Unfilled order; $%s total, %s qty" % (pnl, qty), cur)
                db_id += 1

            time.sleep(1)
        # Position is liquididated!
        print "Liquidated position for ${:,}".format(pnl)
        insert(db_id, "Liquidated position for ${:,}".format(pnl), cur)
