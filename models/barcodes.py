from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database_manager import Base


class Barcode(Base):
    __tablename__ = 'barcodes'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    order = relationship("Order", back_populates="barcodes")

    def __repr__(self):
        return f"<Barcode(id={self.id}, code={self.code}, order_id={self.order_id})>"
