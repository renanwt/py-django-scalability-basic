from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import time

from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]
    filterset_fields = ['price', 'stock', 'created_at']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'stock', 'created_at']

    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):        
        # For demonstration purposes, let's simulate a "heavy" operation
        # that would benefit from caching.
        time.sleep(0.1) # Uncomment to see the effect of caching on latency
        return super().list(request, *args, **kwargs)


    @action(detail=True, methods=['get'])
    def cached_detail(self, request, pk=None):
        product = self.get_object()
        cache_key = f'product_detail_{pk}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # If not cached, serialize the product and cache the result
        serializer = self.get_serializer(product)
        data = serializer.data
        cache.set(cache_key, data, timeout=300) # Cache for 5 min
        return Response(data)

    # Example of how you would integrate an asynchronous task (Celery)
    # Suppose you have a function in tasks.py: `send_product_update_notification(product_id)`
    @action(detail=True, methods=['post'])
    def notify_update(self, request, pk=None):
        product = self.get_object()
        # Here you would typically call an asynchronous task
        # from .tasks import send_product_update_notification
        # send_product_update_notification.delay(product.id) # .delay() para execução assíncrona

        return Response({"status": "Notificação de atualização enviada para processamento em segundo plano."})
    # Query optimization for the retrieve method (GET /products/{id}/)    
    def retrieve(self, request, *args, **kwargs):
        # In scenarios with relationships, using select_related/prefetch_related
        # would save DB queries. Ex: Product.objects.select_related('category').get(pk=pk)
        return super().retrieve(request, *args, **kwargs)