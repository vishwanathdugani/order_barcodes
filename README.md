# Orders and Barcode Management

## Overview
Tiqets Script is a Python-based application designed for managing ticket orders and barcodes. It includes features to load and append data from CSV files, list barcodes, identify top customers, and count unused barcodes.

## Getting Started

### Prerequisites
- Docker (Recommended for ease of setup)
- Python 3.11 (If not using Docker)
- Git (To clone the repository)

### Installation

1. **Clone the Repository:**
   ```bash
   git clone git@github.com:vishwanathdugani/order_barcodes.git
   cd order_barcodes
   ```

2. **Using Docker (Recommended):**
   - Build the Docker Image:
     ```bash
     docker build -t tiqets_script .
     ```
   - Run the Docker Container:
     ```bash
     docker run -it tiqets_script bash
     ```

3. **Without Docker:**
   - Set Up a Local Environment:
     - Install Python 3.11.
     - Create a virtual environment (recommended):
       ```bash
       python3 -m venv venv
       source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
       ```
     - Install dependencies:
       ```bash
       pip install -r requirements.txt
       ```
   - Set the PYTHONPATH:
     - Ensure the PYTHONPATH includes the current working directory:
       ```bash
       export PYTHONPATH=$(pwd):$PYTHONPATH
       ```

### Usage

It's critical to load data into the database before performing other operations:

- **Load Data into the Database:**
  ```bash
  python main.py --load-data orders.csv barcodes.csv
  ```

- **Run the Main Script:**
  ```bash
  python main.py [arguments]
  ```

  The script accepts various arguments for different operations:
  - `--load-data [ORDERS_FILE_PATH] [BARCODES_FILE_PATH]`: Load data from CSV files.
  - `--append-data [ORDERS_FILE_PATH] [BARCODES_FILE_PATH]`: Append data from CSV files.
  - `--barcodes`: List all barcodes and related data.
  - `--top-customers [N]`: List top N customers by number of tickets purchased.
  - `--unused-barcodes`: Count unused barcodes.

  Note: If an operation fails due to missing data, an exception will inform you to load the data first.

### Running Tests

- **Pytest:**
  - Ensure you are in the project's root directory and PYTHONPATH is set.
  - Execute the test command:
    ```bash
    pytest tests/tests.py --html=report.html
    ```

### Test Reports
- A report will be generated in HTML format (`report.html`) after running the tests. Open it in a web browser for a detailed view of the test results.

### Project Approach

The project adopts a modular approach:

- **Data Model Layer (`./models`)**: Defines the database schema with SQLAlchemy ORM models for `Order` and `Barcode`.

- **Database Operations Layer (`./database`)**: Manages database interactions, including CRUD operations in `crud.py` and database connection setup in `database_manager.py`.

- **Validation Layer (`./utils`)**: Ensures data integrity, crucial for processing external data sources like CSV files.

- **Application Logic (`main.py`)**: Implements the command-line interface using argparse, orchestrating data flow through the system.

- **Testing Suite (`./tests`)**: Contains tests and mock data, ensuring the application's functionality and reliability.

---

Remember to load data into the database first to avoid operational errors. The application's exception handling will guide you through any missing data scenarios.