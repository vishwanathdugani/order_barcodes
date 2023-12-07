import argparse
import csv
import logging
import os
import sys
from sqlite3 import OperationalError

from pydantic import ValidationError
from sqlalchemy.orm import Session

from database.crud import create_order, create_barcode, get_barcode
from database.database_manager import SessionLocal, init_db
from utils.validation import OrderModel, BarcodeModel
from models.orders import Order
from database import crud


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_and_validate_data(file_path, model, db: Session):
    """
    Read and validate data from a CSV file.

    Args:
        file_path (str): Path to the CSV file.
        model (pydantic.BaseModel): The Pydantic model for data validation.
        db (Session): SQLAlchemy database session.

    Yields:
        dict: Valid rows from the CSV file.
    """
    with open(file_path, 'r') as file:
        data = list(csv.DictReader(file))
        for row in data:
            try:
                model(**row)
                if model == BarcodeModel and get_barcode(db, row['barcode']):
                    logging.error(f"Barcode {row['barcode']} already exists, skipping!")
                    continue
                yield row
            except ValidationError as e:
                print(f"Invalid data: {row}", file=sys.stderr)


def determine_file_order(file_paths):
    """
    Determine the order of files based on the presence of a 'customer_id' column.

    Args:
        file_paths (list): List of file paths.

    Returns:
        list: Ordered list of file paths.
    """
    with open(file_paths[0], 'r') as file:
        if 'customer_id' in file.readline():
            return file_paths
        else:
            return file_paths[::-1]


def load_data(file_paths, db: Session):
    """
    Load data from CSV files into the database. Overwrites all previous data.

    Args:
        file_paths (list): List of file paths.
        db (Session): SQLAlchemy database session.
    """
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

    init_db()

    try:
        crud.delete_all_data(db)
        orders_file, barcodes_file = determine_file_order(file_paths)

        for row in read_and_validate_data(orders_file, OrderModel, db):
            create_order(db, row['order_id'], row['customer_id'])

        for row in read_and_validate_data(barcodes_file, BarcodeModel, db):
            create_barcode(db, row['barcode'], row['order_id'])

        db.commit()
        logging.info("Data loaded successfully.")
    except Exception as e:
        db.rollback()
        logging.error(f"Error loading data: {e}", exc_info=True)
    finally:
        db.close()


def append_data(file_paths, db: Session):
    """
    Append data from CSV files into the database.

    Args:
        file_paths (list): List of file paths.
        db (Session): SQLAlchemy database session.
    """
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

    try:
        orders_file, barcodes_file = determine_file_order(file_paths)

        for row in read_and_validate_data(orders_file, OrderModel, db):
            if not db.query(Order).filter(Order.id == row['order_id']).first():
                create_order(db, row['order_id'], row['customer_id'])

        for row in read_and_validate_data(barcodes_file, BarcodeModel, db):
            if not get_barcode(db, row['barcode']):
                create_barcode(db, row['barcode'], row['order_id'])

        db.commit()
        logging.info("Data appended successfully.")
    except Exception as e:
        db.rollback()
        logging.error(f"Error appending data: {e}", exc_info=True)
    finally:
        db.close()


def list_barcodes(db: Session):
    """
    List all barcodes and related data.

    Args:
        db (Session): SQLAlchemy database session.
    """
    try:
        grouped_barcodes = crud.list_barcodes(db)
        for (customer_id, order_id), barcodes in grouped_barcodes.items():
            print(f"Customer: {customer_id}, Order: {order_id}, Barcodes: {barcodes}")

        logging.info("Barcodes grouped and listed successfully.")
    except Exception as e:
        logging.error(f"Error listing barcodes: {e}, check if the database is loaded with data", exc_info=True)
    finally:
        db.close()


def get_top_customers(db: Session, top_n=5):
    """
    List the top N customers by the number of tickets purchased.

    Args:
        db (Session): SQLAlchemy database session.
        top_n (int, optional): Number of top customers to list. Default is 5.
    """
    try:
        results = crud.get_top_customers(db, top_n)

        for customer_id, ticket_count in results:
            print(f"Customer: {customer_id}, Count: {ticket_count}")
    except Exception as e:
        logging.error(f"Error listing top customers: {e}, check if the database is loaded with data")


def count_unused_barcodes(db: Session):
    """
    Count unused barcodes in the database.

    Args:
        db (Session): SQLAlchemy database session.
    """
    try:
        unused_count = crud.count_unused_barcodes(db)
        print(f"Number of Unused barcodes: {unused_count}")
    except Exception as e:
        logging.error(f"Error listing no. of unused barcodes: {e}, check if the database is loaded with data")


def main():
    parser = argparse.ArgumentParser(description="Data Management for Tiqets.")
    parser.add_argument("--load-data", nargs=2, help="Load data from CSV files. Over writes all previous data")
    parser.add_argument("--append-data", nargs=2, help="Append data from CSV files. "
                                                       "Appends new rows, and skips existing ones")
    parser.add_argument("--barcodes", action="store_true", help="List all barcodes and related data.")
    parser.add_argument("--top-customers", nargs='?', const=5, type=int,
                        help="List top N customers by number of tickets purchased. Default is 5.")
    parser.add_argument("--unused-barcodes", action="store_true", help="Count unused barcodes.")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.load_data:
            load_data(args.load_data, db)
        elif args.append_data:
            append_data(args.append_data, db)
        elif args.barcodes:
            list_barcodes(db)
        elif args.top_customers:
            get_top_customers(db, args.top_customers)
        elif args.unused_barcodes:
            count_unused_barcodes(db)
        else:
            parser.print_help()
    except OperationalError as e:
        if "no such table" in str(e):
            print("Error: No data found in the database. Please load data first using --load-data.")
            logging.error("Attempted to access database tables before data was loaded.")
        else:
            raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
