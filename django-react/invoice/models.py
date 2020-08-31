from django.db import models
from django.db.models.fields.related import ForeignKey
from model_utils import Choices
from gst_field.modelfields import GSTField, PANField
from datetime import date

class User(models.Model):
    UserType = Choices('BUYER', 'SELLER', 'BROKER', 'GUEST')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    user_type = models.CharField(choices=UserType, max_length=64, default=UserType.BUYER)
    gstin = GSTField(null=True, blank=True)
    pan = PANField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Address(models.Model):
    AddressType = Choices('HOME', 'WORK')
    line1 = models.CharField(max_length=50)
    line2 = models.CharField(max_length=50)
    address_type = models.CharField(choices=AddressType, max_length=64, default=AddressType.WORK)
    is_primary = models.BooleanField(default=True)
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    city = models.CharField(max_length=60, default="Jammu")
    state = models.CharField(max_length=30, default="J&K")
    zipcode = models.CharField(max_length=6, default="180001")
    country = models.CharField(max_length=50, default="India")

class Item_details(models.Model):
    igst_tax_percentage = models.FloatField(null=True, blank=True)
    sgst_tax_percentage = models.FloatField(null=True, blank=True)
    cgst_tax_percentage = models.FloatField(null=True, blank=True)
    igst_amt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    sgst_amt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    cgst_amt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Item(models.Model):
    TaxType = Choices('GST')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    tax_percentage = models.FloatField()
    tax_type = models.CharField(choices=TaxType, max_length=64, default=TaxType.GST)
    item_details = models.OneToOneField(Item_details,on_delete=models.CASCADE,null=True, blank=True)
    seller = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Order(models.Model):
    PaymentStatus = Choices('PENDING', 'IN_PROCESS', 'PAID', 'COD')
    order_date = models.DateField()
    items = models.ManyToManyField(Item, through='Order_Item_Relationship')
    buyer = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    order_payment_status = models.CharField(choices=PaymentStatus, max_length=64, default=PaymentStatus.PENDING)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Order_Item_Relationship(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)

class Invoice(models.Model):
    TaxType = Choices('GST')
    items = models.ManyToManyField(Item, through='Invoice_Item_Relationship')
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.CASCADE)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    tax_type = models.CharField(choices=TaxType, max_length=64, default=TaxType.GST)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Invoice_Item_Relationship(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    item_details = models.OneToOneField(Item_details,on_delete=models.CASCADE,null=True, blank=True)

class Transaction(models.Model):
    TransactionStatus = Choices('INITIATED', 'SUCCESS', 'FAILURE')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    external_transaction_id = models.CharField(max_length=128, unique=True, blank=True, null=True)
    transaction_hash = models.CharField(max_length=254, blank=True, null=True)
    transaction_status = models.CharField(choices=TransactionStatus, max_length=64, default=TransactionStatus.INITIATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)