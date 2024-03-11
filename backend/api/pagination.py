from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    """Не забываем про паджинатор
    Причем кастомный, т.к. там ожидается параметра limit."""
    page_size_query_param = 'limit'
    page_size = 6