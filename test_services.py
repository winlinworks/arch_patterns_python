import pytest
import model
import repository
import services


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMINOUS-MIRROR", 10)
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    # TODO: you'll need to implement the services.add_batch method
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)

    # allocate the line
    services.allocate(line, repo, session)
    batch = repo.get(reference="b1")
    # check that the available quantity is decremented
    assert batch.available_quantity == 90

    # deallocate the line
    services.deallocate(line, repo, session)
    batch = repo.get(reference="b1")
    # check that the available quantity is back to 100
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    # TODO - check that we decrement the right sku
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    services.add_batch("b2", "RED-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    line2 = model.OrderLine("o2", "RED-PLINTH", 20)

    # allocate the lines
    services.allocate(line, repo, session)
    services.allocate(line2, repo, session)
    batch1 = repo.get(reference="b1")
    batch2 = repo.get(reference="b2")

    # check that the available quantity is decremented
    assert batch1.available_quantity == 90
    assert batch2.available_quantity == 80

    # deallocate the lines
    services.deallocate(line, repo, session)
    services.deallocate(line2, repo, session)
    batch1 = repo.get(reference="b1")
    batch2 = repo.get(reference="b2")

    # check that the available quantity is back to 100
    assert batch1.available_quantity == 100
    assert batch2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    # TODO - check that we raise an error when trying to deallocate an unallocated batch
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)

    with pytest.raises(model.NotAllocated):
        services.deallocate(line, repo, session)
