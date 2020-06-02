import operator

from ninjin.lazy import lazy, listify

SEPARATOR = '__'
LESSER_THAN = 'lt'
LESSER_THAN_OR_EQUAL = 'lte'
GREATER_THAN = 'gt'
GREATER_THAN_OR_EQUAL = 'gte'
EXACT = 'exact'
CONTAINS = 'in'
ALL = (
    LESSER_THAN,
    LESSER_THAN_OR_EQUAL,
    GREATER_THAN,
    GREATER_THAN_OR_EQUAL,
    EXACT,
    CONTAINS
)


class BasicFiltering:
    """

    """
    OPERATOR = {
        LESSER_THAN: operator.lt,
        LESSER_THAN_OR_EQUAL: operator.le,
        GREATER_THAN: operator.gt,
        GREATER_THAN_OR_EQUAL: operator.ge,
        EXACT: operator.eq,
        CONTAINS: operator.contains
    }

    def __init__(self, model, filtering, allowed_filters):
        self.model = model
        self.filtering = filtering
        self.allowed_filters = allowed_filters

    @lazy
    @listify
    def applicable_filters(self):
        for filter_, val in self.filtering.items():
            try:
                field, op = filter_.split(SEPARATOR)
            except ValueError:
                field, op = filter_, EXACT
            if field in self.allowed_filters and \
                    op in ALL and \
                    op in self.allowed_filters[field]:
                yield field, op, val

    @lazy
    @listify
    def _operators(self):
        for field, op, val in self.applicable_filters:
            yield self.OPERATOR[op](
                getattr(self.model, field),
                val
            )

    @lazy
    def where_clause(self):
        if self._operators:
            res = self._operators[0]
            for op in self._operators[1:]:
                res = operator.and_(res, op)
            return res
        return True

    @lazy
    def empty(self):
        return not bool(self.applicable_filters)

    def filter(self, query):
        return query.where(self.where_clause)
