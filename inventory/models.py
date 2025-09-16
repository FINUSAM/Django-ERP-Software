from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.

class StockType(models.Model):
    UNIT_CHOICES = [
        ('', 'None'),
        ('mtr', 'Meter'),
        ('ml', 'Milliliter'),
    ]

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, default='')

    @property
    def no_of_stocks(self):
        return self.stocks.all().count()

    def __str__(self):
        return self.name

class Stock(models.Model):
    name = models.CharField(unique=True, max_length=100)
    initial_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price_retail = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price_wholesale = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    supplier = models.CharField(max_length=100, blank=True, null=True)  # optional
    stock_type = models.ForeignKey(StockType, on_delete=models.CASCADE, related_name='stocks', null=True, blank=True)  # optional

    def __str__(self):
        return self.name
    
    @property
    def sold_quantity(self):
        total = 0
        for stockset in self.stocksets.all():
            for sale in stockset.sales.all():
                if stockset.consumption_quantity:
                    total += sale.quantity * stockset.consumption_quantity
                else:
                    total += sale.quantity
        return total


    @property
    def purchased_quantity(self):
        total = 0
        for stockset in self.stocksets.all():
            for purchase in stockset.purchases.all():
                if stockset.consumption_quantity:
                    total += purchase.quantity * stockset.consumption_quantity
                else:
                    total += purchase.quantity
        return total

    
    @property
    def sales_return_quantity(self):
        total = 0
        for stockset in self.stocksets.all():
            for sale in stockset.sales.all():
                if stockset.consumption_quantity:
                    total += sale.return_quantity * stockset.consumption_quantity
                else:
                    total += sale.return_quantity
        return total


    @property
    def purchases_return_quantity(self):
        total = 0
        for stockset in self.stocksets.all():
            for purchase in stockset.purchases.all():
                if stockset.consumption_quantity:
                    total += purchase.return_quantity * stockset.consumption_quantity
                else:
                    total += purchase.return_quantity
        return total

    
    @property
    def remaining_quantity(self):
        return (self.initial_quantity 
                + (self.purchased_quantity - self.purchases_return_quantity) 
                - (self.sold_quantity - self.sales_return_quantity))

class StockSet(models.Model):
    name = models.CharField(unique=True, max_length=100)
    stock = models.ManyToManyField(Stock, related_name='stocksets')

    # New optional fields for bundle prices
    custom_cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_selling_price_retail = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_selling_price_wholesale = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # 👇 NEW FIELD
    consumption_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="How much base stock this set consumes (e.g., 5ml, 10ml)."
    )
    
    def __str__(self):
        return self.name
    
    @property
    def stock_type(self):
        if self.stock.all().count() > 1:
            return "Set"
        else:
            if self.stock.first().name != self.name:
                return "Set"
            return self.stock.first().stock_type.name if self.stock.first().stock_type else "unknown"
    
    @property
    def unit(self):
        if self.stock.all().count() > 1:
            return ""
        else:
            return self.stock.first().stock_type.unit if self.stock.first().stock_type else ""
    
    @property
    def stock_pk(self):
        if self.stock_type == 'Set':
            return self.pk
        else:
            return self.stock.first().pk
    
    @property
    def cost_price(self):
        if self.custom_cost_price is not None:
            return self.custom_cost_price
        stocks = self.stock.all()
        if not stocks:
            return 0
        return sum(stock.cost_price for stock in stocks)

    @property
    def selling_price_retail(self):
        if self.custom_selling_price_retail is not None:
            return self.custom_selling_price_retail
        stocks = self.stock.all()
        if not stocks:
            return 0
        return sum(stock.selling_price_retail for stock in stocks)

    @property
    def selling_price_wholesale(self):
        if self.custom_selling_price_wholesale is not None:
            return self.custom_selling_price_wholesale
        stocks = self.stock.all()
        if not stocks:
            return 0
        return sum(stock.selling_price_wholesale for stock in stocks)


    @property
    def initial_quantity(self):
        stocks = self.stock.all()
        if not stocks:
            return 0
        return min(stock.initial_quantity for stock in stocks)
    
    @property
    def sold_quantity(self):
        return sum(sale.quantity for sale in self.sales.all())
    
    @property
    def purchased_quantity(self):
        return sum(purchase.quantity for purchase in self.purchases.all())
    
    @property
    def sales_return_quantity(self):
        return sum(sale.return_quantity for sale in self.sales.all())
    
    @property
    def purchases_return_quantity(self):
        return sum(purchase.return_quantity for purchase in self.purchases.all())
    
    @property
    def remaining_quantity(self):
        stocks = self.stock.all()
        if not stocks:
            return 0

        if self.consumption_quantity:
            # Divide available stock by consumption_quantity to get number of sets
            return min(stock.remaining_quantity // self.consumption_quantity for stock in stocks)
        else:
            # Fallback to old behaviour
            return min(stock.remaining_quantity for stock in stocks)
    

