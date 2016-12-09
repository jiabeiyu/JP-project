"""
This is algorithm for trading
"""
import urllib2
# import time
import re
import datetime
import sys
import json
import threading
import psycopg2


class UseThread(threading.Thread):
    """
    This is algorithm class which is thread class' extension
    """

    def __init__(self, quantity):
        """
        class initiator
        """
        threading.Thread.__init__(self)
        self.quantity = quantity

    @staticmethod
    def cal_current_time(cur_time):
        """
        convert input string time to second

        Args:
            cur_time: current time in string form.

        Returns:
            current time in second
        """
        time_string = cur_time.split()[1]
        # b = a.split('.')[0]
        hour, minute, second = re.split(':', time_string)
        cur_time = float(
            datetime.timedelta(
                hours=int(hour), minutes=int(minute), seconds=float(second)).total_seconds())
        # Total time 8:30 = 30600 sec
        if cur_time > 30600:
            print "End of the trading day"
            sys.exit()
        # print "This is current time: ",
        # print current_time
        return cur_time

    @staticmethod
    def cal_interval_time(cur_time, quantity, order_size):
        """
        calculate time interval for next child order

        Args:
            cur_time: current time in string form.
            quantity: current inventory size
            order_size: next child order's size

        Returns:
            time interval in second
        """
        # work time 8:30 - 10 min = 30000 sec
        time_left = 30000 - cur_time
        # print time_left
        if time_left < 0:
            return 0
        else:
            return time_left / (quantity / order_size)

    @staticmethod
    def connect_database():
        """
        initialize connection with database

        Args:

        Returns:
            database connection object
        """
        try:
            conn = psycopg2.connect("dbname='stock' user='Linnan' host='localhost' password='' ")
            print 'get connect'
        except Exception:
            print "I am unable to connect to the database"
            return 1
        return conn

    @staticmethod
    def database_cleanup(connection, cursor):
        """
        delete previous stored value in database

        Args:
            connection: database connection object
            cursor: database cursor

        Returns:

        """
        delet1 = "DELETE FROM info;"
        delet2 = "DELETE FROM transact;"
        try:
            cursor.execute(delet1)
            connection.commit()
            cursor.execute(delet2)
            connection.commit()
        except Exception:
            print "Can't delete data from database"
            connection.rollback()

    @staticmethod
    def insert_info(data_id, time_stamp, message, cur, connection):
        """
        calculate time interval for next child order

        Args:
            data_id: database id
            time_stamp: current time
            message: market price
            cur: database cursor
            connection: database connection

        Returns:
            time interval in second
        """
        # insert server feedback to database
        query = "INSERT INTO info (id, time_quote, info) VALUES ('{}', '{}', '{}');" \
            .format(data_id, time_stamp, message)
        # print query
        try:
            cur.execute(query)
            connection.commit()
        except Exception:
            print "Can't insert data into market information form"
            connection.rollback()

    @staticmethod
    def insert_trans(sell_info, result, order_info, cur, connection):
        """
        calculate time interval for next child order

        Args:
            sell_info: database id and selling value
            result: string of order status
            order_info: selling order information
            cur: database cursor
            connection: database connection

        Returns:
            time interval in second
        """
        if order_info is None:
            time_stamp = ""
            price = ""
            size = ""
        else:
            time_stamp = order_info['timestamp']
            price = order_info['avg_price']
            size = order_info['qty']
        query = "INSERT INTO transact (id, time_quote, result, price, size, amount, value) " \
                "VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}');". \
            format(sell_info['trans_id'], time_stamp, result, price, size,
                   sell_info['total_sell'], sell_info['sum_value'])
        # print query
        try:
            cur.execute(query)
            connection.commit()
        except Exception as info:
            print "Can't insert data into transition history form"
            print info
            connection.rollback()

    @staticmethod
    def quote_info():
        """
        send request string to the JP server and get market information

        Args:

        Returns:
            JSON object of market information
        """
        query = "http://localhost:8080/query?id={}"
        try:
            quote = json.loads(urllib2.urlopen(query.format(1)).read())
        except Exception:
            print "Server error"
            # sys.exit()
        return quote

    @staticmethod
    def make_order(order_size, market_info, order_discount):
        """
        calculate time interval for next child order

        Args:
            order_size: order size of this order
            market_info: market information JSON object
            order_discount: order discount percentage

        Returns:
            JSON object of order information
        """
        order_query = "http://localhost:8080/order?id={}&side=sell&qty={}&price={}"
        try:
            order_price = float(market_info['top_bid']['price']) * (100 - order_discount) * 0.01
            order_args = (order_size, order_price)
            url = order_query.format(2, *order_args)
            order = json.loads(urllib2.urlopen(url).read())
            print order
        except Exception:
            print "price or order size too high"
            order = None
        return order

    def run(self):
        """
        main function which executing parent order

        Args:

        Returns:
            none
        """

        inventory = int(self.quantity)
        if inventory < 30:
            order_size = inventory
        else:
            order_size = 30
        order_discount = 10

        conn = self.connect_database()
        cur = conn.cursor()
        self.database_cleanup(conn, cur)

        # info_id = 0
        sell_info = {'trans_id': 1, 'total_sell': 0, 'sum_value': 0}
        time_wait = 0

        while inventory > 0:
            market_info = self.quote_info()
            while True:  # 0.5 is estimation time of execution of one order
                if self.cal_current_time(market_info['timestamp']) + 0.5 > time_wait:
                    break
                else:
                    market_info = self.quote_info()

            while 1:
                # time.sleep(0.2)
                # make order
                order = self.make_order(order_size, market_info, order_discount)

                if order is None:
                    self.insert_trans(
                        sell_info, "failure occurred, recalculate strategy", None, cur, conn)

                    sell_info['trans_id'] += 1
                    market_info = self.quote_info()
                    current_time = self.cal_current_time(market_info['timestamp'])
                    # self.insert_info(info_id, time_mark, "Quoted at %s" % price, cur, conn)
                    # info_id += 1
                    if order_size > 10:
                        order_size -= 10
                else:
                    # record sell price and add total sell amount and revenue
                    sell_info['total_sell'] += order_size
                    sell_info['sum_value'] += float(order['avg_price']) * order_size

                    self.insert_trans(sell_info, "success", order, cur, conn)
                    sell_info['trans_id'] += 1

                    # change inventory amount and recalculate time
                    inventory -= order_size
                    current_time = self.cal_current_time(order['timestamp'])
                    break

            if inventory == 0:
                break
            time_interval = self.cal_interval_time(current_time, float(inventory), float(order_size))
            if time_interval < 2:
                order_discount += 1
                order_size += 50
            print "This is interval time: ",
            print time_interval
            time_wait = current_time + time_interval
            # print "This is wait time: ",
            # print time_wait

            if inventory < order_size:
                order_size = inventory

        print "this is total sell",
        print sell_info['total_sell']
        print "this is total value",
        print sell_info['sum_value']
        print "this is ave price",
        if sell_info['total_sell'] > 0:
            avg_price = sell_info['sum_value'] / sell_info['total_sell']
        else:
            avg_price = 0
        print avg_price
        result_order = "Finished with average price " + str(avg_price)
        self.insert_trans(sell_info, result_order, None, cur, conn)
        # Repeat the strategy until we run out of shares.
