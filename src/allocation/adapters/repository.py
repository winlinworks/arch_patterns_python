import abc
from allocation.domain import model


class AbstractProductRepository(abc.ABC):
    def add(self, product: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class ProductRepository(AbstractProductRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product: model.Product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).one_or_none()

    def list(self):
        return self.session.query(model.Product).all()
