from typing import Iterable

from sqlalchemy import desc

from ninjin.lazy import lazy


class BasicOrdering:
    def __init__(self, ordering: str, allowed_ordering: Iterable):
        self.ordering_ = ordering
        self.allowed_ordering = allowed_ordering or ()

    @lazy
    def ordering(self):
        if self.ordering_:
            return self.ordering_.lstrip('-')

    @lazy
    def applicable_ordering(self):
        if self.ordering and self.ordering in self.allowed_ordering:
            return desc(self.ordering) if self.desc_ordering \
                else self.ordering

    @lazy
    def desc_ordering(self):
        return self.ordering_.startswith('-')

    def order_by(self, query):
        return query.order_by(
            self.applicable_ordering
        )
