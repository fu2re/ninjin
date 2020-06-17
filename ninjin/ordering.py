# -*- coding: utf-8 -*-
"""Ordering classes."""
from typing import Iterable

from sqlalchemy import desc

from ninjin.decorator import lazy


class ModelResourceOrdering:
    """ModelResource ordering class."""

    def __init__(self, ordering: str, allowed_ordering: Iterable):
        """
        Object is created per each request.

        :param ordering: field to filter with
        :param allowed_ordering: allowed ordering fields
        """
        self.ordering_ = ordering
        self.allowed_ordering = allowed_ordering or ()

    @lazy
    def _ordering(self):
        if self.ordering_:
            return self.ordering_.lstrip('-')

    @lazy
    def applicable_ordering(self):
        """
        Get applicable ordering.

        :return:
        """
        if self._ordering and self._ordering in self.allowed_ordering:
            return desc(self._ordering) if self._desc_ordering \
                else self._ordering

    @lazy
    def _desc_ordering(self):
        return self.ordering_.startswith('-')

    def order_by(self, query):
        """
        Perform an ordering with applicable ordering.

        :param query: SQL Alchemy core query.
        :return: SQL Alchemy core query.
        """
        return query.order_by(
            self.applicable_ordering,
        )
