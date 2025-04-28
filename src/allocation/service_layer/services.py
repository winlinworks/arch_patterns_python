from __future__ import annotations
from typing import Optional, List
from datetime import date

from allocation.domain import model
from allocation.domain.model import OrderLine
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_product(
    sku: str,
    batches: List[model.Batch],
    uow: unit_of_work.AbstractUnitOfWork
):
    with uow:
        # Check if product already exists
        existing_product = uow.products.get(sku)
        if existing_product:
            raise ValueError(f"Product with SKU {sku} already exists.")

        # If product does not exist, create a new one
        product = model.Product(sku, batches)
        uow.products.add(product)
        uow.commit()


def add_batch(
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        # Get product
        product = uow.products.get(sku)

        # If product does not exist, create a new one
        if not product:
            product = model.Product(sku, set())
            uow.products.add(product)
        
        # Add batch to product
        product.batches.add(model.Batch(ref, sku, qty, eta))        
        uow.commit()


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        # Check if product exists
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")
        
        # Allocate the order line
        batchref = product.allocate(line)
        uow.commit()
    return batchref
