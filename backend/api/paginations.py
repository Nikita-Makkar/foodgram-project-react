from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    Кастомный пагинатор - ожидается параметр limit."""
    page_size_query_param = 'limit'
    page_size = 6
