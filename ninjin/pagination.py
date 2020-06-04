class BasicPagination:
    items_per_page = 1
    max_items_per_page = 100

    def __init__(self,
                 pagination: dict = None,
                 items_per_page: int = None,
                 max_items_per_page: int = None):
        pagination = pagination or {}
        self.page = pagination.get('page', 0)
        self.max_items_per_page = max_items_per_page

        self.items_per_page = min(
            pagination.get('items_per_page', items_per_page),
            self.max_items_per_page
        )
        self.limit = (self.page + 1) * self.items_per_page
        self.offset = self.page * self.items_per_page
        self.next = False

    def paginate(self, query):
        return query.limit(self.limit).offset(self.offset)

    @property
    def result(self):
        # TODO next page
        return {
            'page': self.page
        }
