from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database_manager import Base

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    customer_id = Column(String, nullable=False)
    barcodes = relationship("Barcode", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, customer_id={self.customer_id})>"
