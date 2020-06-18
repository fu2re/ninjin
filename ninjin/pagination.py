# -*- coding: utf-8 -*-
"""Pagination classes."""


class ModelResourcePagination:
    """ModelResource pagination class."""

    items_per_page = 1
    max_items_per_page = 100

    def __init__(self,
                 pagination: dict = None,
                 items_per_page: int = None,
                 max_items_per_page: int = None):
        """
        Object is created per each request.

        :param pagination: pagination dictionary
        :param items_per_page: items per page
        :param max_items_per_page: maximum items per page
        """
        pagination = pagination or {}
        self.page = pagination.get('page', 0)
        self.max_items_per_page = max_items_per_page

        self.items_per_page = min(
            pagination.get('items_per_page', items_per_page),
            self.max_items_per_page,
        )
        self.limit = (self.page + 1) * self.items_per_page
        self.offset = self.page * self.items_per_page
        self.next = False

    def paginate(self, query):
        """
        Get query subset.

        :param query: SQL Alchemy core query.
        :return: SQL Alchemy core query.
        """
        return query.limit(self.limit).offset(self.offset)

    @property
    def result(self):
        """
        Get navigation data.

        :return: Pagination dictionary
        """
        # TODO next page
        return {
            'page': self.page,
        }
