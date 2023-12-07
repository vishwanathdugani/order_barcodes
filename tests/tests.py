import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import redirect_stdout
import io

from sqlalchemy_orm.session import Session

from database import crud

from database.database_manager import Base
from main import load_data, append_data, list_barcodes, count_unused_barcodes
from models.orders import Order
from models.barcodes import Barcode


@pytest.fixture(scope="module")
def test_db():
    test_database_url = os.getenv("TEST_DATABASE_URL", "sqlite:///./tests/test_tiqets.db")

    engine = create_engine(test_database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_load_data(test_db: Session):
    mock_orders_path = 'tests/mock_orders.csv'
    mock_barcodes_path = 'tests/mock_barcodes.csv'

    assert os.path.exists(mock_orders_path), f"File not found: {mock_orders_path}"
    assert os.path.exists(mock_barcodes_path), f"File not found: {mock_barcodes_path}"

    load_data([mock_orders_path, mock_barcodes_path], test_db)

    orders = test_db.query(Order).all()
    barcodes = test_db.query(Barcode).all()

    assert len(orders) == 5
    assert len(barcodes) == 9


def test_append_data(test_db):
    load_data(['tests/mock_orders.csv', 'tests/mock_barcodes.csv'], test_db)
    append_data(['tests/mock_orders.csv', 'tests/mock_barcodes.csv'], test_db)

    orders = test_db.query(Order).all()
    barcodes = test_db.query(Barcode).all()

    assert len(orders) == 5
    assert len(barcodes) == 9


def test_list_barcodes(test_db):
    f = io.StringIO()
    with redirect_stdout(f):
        list_barcodes(test_db)
    output = f.getvalue()

    assert "Customer: 100, Order: 1, Barcodes:" in output


def test_count_unused_barcodes(test_db):
    f = io.StringIO()
    with redirect_stdout(f):
        count_unused_barcodes(test_db)
    output = f.getvalue()
    unused_count = int(output.split(': ')[1])

    assert unused_count == 1


def test_load_data_with_invalid_file(test_db):
    with pytest.raises(FileNotFoundError):
        load_data(['nonexistent_orders.csv', 'nonexistent_barcodes.csv'], db=test_db)


def test_append_data_with_duplicates(test_db):
    load_data(['tests/mock_orders.csv', 'tests/mock_barcodes.csv'], test_db)

    append_data(['tests/mock_orders_duplicates.csv', 'tests/mock_barcodes_duplicates.csv'], test_db)

    orders = test_db.query(Order).all()
    barcodes = test_db.query(Barcode).all()

    assert len(orders) == len(set(order.id for order in orders))
    assert len(barcodes) == len(set(barcode.code for barcode in barcodes))


def test_create_order(test_db: Session):
    new_order = crud.create_order(test_db, '1000', "500")
    assert new_order is not None
    assert new_order.id == 1000

    duplicate_order = crud.create_order(test_db, '1000', "500")
    assert duplicate_order is None  # Assuming it returns None if order exists

    test_db.query(Order).filter(Order.id == 1000).delete()
    test_db.commit()


def test_create_barcode(test_db: Session):
    new_barcode = crud.create_barcode(test_db, "abc123", '1000')
    assert new_barcode is not None
    assert new_barcode.code == "abc123"
    assert new_barcode.order_id == 1000

    duplicate_barcode = crud.create_barcode(test_db, "abc123", '1000')
    assert duplicate_barcode is None  # Assuming it returns None if barcode exists

    test_db.query(Barcode).filter(Barcode.code == "abc123").delete()
    test_db.commit()


def test_list_barcodes_crud(test_db: Session):
    barcodes_list = crud.list_barcodes(test_db)
    assert isinstance(barcodes_list, dict)
    assert all(isinstance(key, tuple) for key in barcodes_list.keys())
    assert all(isinstance(value, list) for value in barcodes_list.values())


def test_get_top_customers(test_db: Session):
    top_customers = crud.get_top_customers(test_db, 5)
    assert len(top_customers) <= 5
    for customer_id, ticket_count in top_customers:
        assert isinstance(customer_id, str)
        assert isinstance(ticket_count, int)


def test_count_unused_barcodes_crud(test_db: Session):
    count = crud.count_unused_barcodes(test_db)
    assert isinstance(count, int)


def test_get_order_by_id(test_db: Session):
    order = crud.get_order_by_id(test_db, '1')
    assert order is not None
    assert order.id == 1

    no_order = crud.get_order_by_id(test_db, '9999')
    assert no_order is None


def test_get_barcode(test_db: Session):
    barcode = crud.get_barcode(test_db, "11111")
    assert barcode is not None
    assert barcode.code == "11111"

    no_barcode = crud.get_barcode(test_db, "non_existing_code")
    assert no_barcode is None


def test_delete_all_data(test_db: Session):
    crud.create_order(test_db, '9999', "temp_customer")
    crud.create_barcode(test_db, "temp_barcode", '9999')

    crud.delete_all_data(test_db)

    orders = test_db.query(Order).all()
    barcodes = test_db.query(Barcode).all()
    assert len(orders) == 0
    assert len(barcodes) == 0
