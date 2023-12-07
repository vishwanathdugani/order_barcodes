import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.orders import Order
from models.barcodes import Barcode
from sqlalchemy import func, desc
# from sqlite3 import OperationalError
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_order(db: Session, order_id: str, customer_id: str):
    """
    Creates an order in the database.

    :param db: Database session.
    :param order_id: ID of the order.
    :param customer_id: ID of the customer.
    :return: Created Order object.
    """
    try:
        existing_order = db.query(Order).filter(Order.id == order_id).first()
        if existing_order is None:
            db_order = Order(id=order_id, customer_id=customer_id)
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
            return db_order
        else:
            logging.info(f"Order {order_id} already exists. Skipping.")
    except IntegrityError as e:
        db.rollback()
        logging.error(f"Error adding order {order_id}: {e}")
    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error: {e}")


def create_barcode(db: Session, barcode: str, order_id: str = None):
    """
    Creates a barcode in the database.

    :param db: Database session.
    :param barcode: Barcode code.
    :param order_id: ID of the associated order.
    :return: Created Barcode object.
    """
    try:
        if order_id == '':
            order_id = None  # Treat empty strings as None

        existing_barcode = db.query(Barcode).filter(Barcode.code == barcode).first()
        if existing_barcode is None:
            db_barcode = Barcode(code=barcode, order_id=order_id)
            db.add(db_barcode)
            db.commit()
            db.refresh(db_barcode)
            return db_barcode
        else:
            logging.info(f"Barcode {barcode} already exists. Skipping.")
    except IntegrityError as e:
        db.rollback()
        logging.error(f"Error adding barcode {barcode}: {e}")
    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error: {e}")


def list_barcodes(db: Session):
    """
    Lists all barcodes grouped by customer and order.

    :param db: Database session.
    :return: Dictionary of barcodes grouped by customer and order.
    """
    try:
        barcodes = db.query(Barcode).join(Order, Barcode.order_id == Order.id).all()

        grouped_barcodes = {}
        for barcode in barcodes:
            key = (barcode.order.customer_id, barcode.order.id)
            if key not in grouped_barcodes:
                grouped_barcodes[key] = []
            grouped_barcodes[key].append(barcode.code)

        return grouped_barcodes
    except OperationalError as e:
        if "no such table: barcodes" in str(e):
            logging.error("The table 'barcodes' does not exist in the database. use --load-data <csv-files>")
        else:
            logging.error(f"Operational error in database operation: {e}")
    except Exception as e:
        logging.error(f"Error listing barcodes: {e}")
        return {}


def get_top_customers(db: Session, top_n=5):
    """
    Gets the top customers based on the number of tickets purchased.

    :param db: Database session.
    :param top_n: Number of top customers to retrieve.
    :return: List of top customers with their ticket counts.
    """
    try:
        results = db.query(
            Order.customer_id,
            func.count(Barcode.id).label('ticket_count')
        ).join(Barcode, Order.id == Barcode.order_id).group_by(
            Order.customer_id
        ).order_by(
            desc('ticket_count')
        ).limit(top_n).all()

        return results
    except OperationalError as e:
        logging.error(f"Operational error in database operation: {e}, Load the data first in the database. "
                      f"Use --load-data <csv-files>")
    except Exception as e:
        logging.error(f"Error getting top customers: {e}")
        return []


def count_unused_barcodes(db: Session):
    """
    Counts the number of unused barcodes.

    :param db: Database session.
    :return: Count of unused barcodes.
    """
    try:
        return db.query(Barcode).filter(Barcode.order_id == None).count()
    except OperationalError as e:
        logging.error(f"Operational error in database operation: {e}, Load the data first in the database."
                      f"Use --load-data <csv-files>")
    except Exception as e:
        logging.error(f"Error counting unused barcodes: {e}")
        return 0



def get_order_by_id(db: Session, order_id: str):
    """
    Retrieve an order by its ID.

    Args:
        db (Session): SQLAlchemy database session.
        order_id (str): The ID of the order to retrieve.

    Returns:
        Order: The retrieved order or None if not found.
    """
    return db.query(Order).filter(Order.id == order_id).first()


def get_barcode(db: Session, barcode_code: str):
    """
    Retrieve a barcode by its code.

    Args:
        db (Session): SQLAlchemy database session.
        barcode_code (str): The code of the barcode to retrieve.

    Returns:
        Barcode: The retrieved barcode or None if not found.
    """
    return db.query(Barcode).filter(Barcode.code == barcode_code).first()


def delete_all_data(db: Session):
    """
    Delete all data from the Orders and Barcodes tables.

    Args:
        db (Session): SQLAlchemy database session.
    """
    db.query(Order).delete()
    db.query(Barcode).delete()
