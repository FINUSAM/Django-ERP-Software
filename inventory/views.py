# views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Stock, StockType, StockSet
from billapp.globalmixins import ModelNameContextMixin


class Inventory(ListView):
    model = StockSet
    template_name = 'inventory/inventory.html'
    ordering = ['name']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_types'] = StockType.objects.all()  # Add your second model here
        return context

class Inventory(ListView):
    model = StockSet
    template_name = 'inventory/inventory.html'
    ordering = ['name']

    def get_queryset(self):
        return (
            StockSet.objects
            .prefetch_related(
                'stock',                 # preload M2M stocks
                'stock__stocksets',      # avoid nested queries
                'stock__stock_type',     # preload stock types
                'sales', 'purchases'     # preload sales/purchases if used
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_types'] = StockType.objects.all()
        return context


# ------- Create Views -------

class StockCreateView(ModelNameContextMixin, CreateView):
    model = Stock
    fields = ['name', 'initial_quantity', 'cost_price', 'selling_price_retail', 'selling_price_wholesale', 'supplier', 'stock_type']
    template_name = 'model_create_edit_form.html'
    success_url = reverse_lazy('inventory')

class StockSetCreateView(ModelNameContextMixin, CreateView):
    model = StockSet
    fields = ['name', 'stock', 'custom_selling_price_retail', 'custom_selling_price_wholesale', 'consumption_quantity']
    template_name = 'model_create_edit_form.html'
    success_url = reverse_lazy('inventory')


class StockTypeCreateView(ModelNameContextMixin, CreateView):
    model = StockType
    fields = ['name', 'unit']
    template_name = 'model_create_edit_form.html'
    success_url = reverse_lazy('create_stock_view')

# ------- Edit Views -------

class StockUpdateView(ModelNameContextMixin, UpdateView):
    model = Stock
    fields = ['name', 'initial_quantity', 'cost_price', 'selling_price_retail', 'selling_price_wholesale', 'supplier', 'stock_type']
    template_name = 'model_create_edit_form.html'
    success_url = reverse_lazy('inventory')

class StockTypeUpdateView(ModelNameContextMixin, UpdateView):
    model = StockType
    fields = ['name', 'unit']
    template_name = 'model_create_edit_form.html'
    success_url = reverse_lazy('inventory')

class StockSetUpdateView(ModelNameContextMixin, UpdateView):
    model = StockSet
    fields = ['name', 'stock', 'custom_selling_price_retail', 'custom_selling_price_wholesale', 'consumption_quantity']
    template_name = 'model_create_edit_form.html'
    success_url = reverse_lazy('inventory')

# ------- Detail Views -------

class StockTypeDetailView(ModelNameContextMixin, DetailView):
    model = StockType
    template_name = 'inventory/stocktype_detail.html'

class StockDetailView(ModelNameContextMixin, DetailView):
    model = Stock
    template_name = 'inventory/stock_detail.html'

class StockSetDetailView(ModelNameContextMixin, DetailView):
    model = StockSet
    template_name = 'inventory/stockset_detail.html'




from django.http import JsonResponse

def get_stock_details(request):
    stockset_id = request.GET.get('stockset_id')
    stockset = StockSet.objects.filter(id=stockset_id).first()
    if stockset:
        remaining_quantity = stockset.remaining_quantity
        selling_price_wholesale = stockset.selling_price_wholesale
        selling_price_retail = stockset.selling_price_retail
        return JsonResponse({
            'remaining_quantity': remaining_quantity,
            'selling_price_retail': selling_price_retail,
            'selling_price_wholesale': selling_price_wholesale
        })
    return JsonResponse({
        'remaining_quantity': 0,
        'price': 0
    })

def stock(request):
    data = []
    for stock in Stock.objects.all():
        data.append({
            "name": stock.name,
            "sold_quantity": stock.sold_quantity,
            "sales_return_quantity": stock.sales_return_quantity,
            "remaining_quantity": stock.remaining_quantity
        })
    return JsonResponse({"data": data})

def stockset(request):
    data = []
    for stockset in StockSet.objects.all():
        data.append({
            "name": stockset.name,
            "initial_quantity": stockset.initial_quantity,
            "sold_quantity": stockset.sold_quantity,
            "sales_return_quantity": stockset.sales_return_quantity,
            "remaining_quantity": stockset.remaining_quantity
        })
    return JsonResponse({"data": data})
