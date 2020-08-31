from rest_framework import serializers

from invoice.models import Item_details, Transaction

from .models import (Address, Invoice, Item, Item_details, Order, Transaction,
                     User)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'user_type', 'gstin', 'pan')

class InvoiceUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name','gstin', 'pan')

class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'user_type')

class InvoiceBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name')

class AddressSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    class Meta:
        model = Address
        fields = ('line1', 'line2', 'address_type', 'is_primary', 'user', 'city', 'state', 'zipcode', 'country')

class ItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item_details
        fields = ('id', 'igst_tax_percentage', 'sgst_tax_percentage', 'cgst_tax_percentage', 'igst_amt', 'cgst_amt', 'sgst_amt')

class ItemSerializer(serializers.ModelSerializer):
    seller = UserSerializer(many=False, read_only=True)
    class Meta:
        model = Item
        fields = ('id', 'name', 'price', 'tax_percentage', 'tax_type', 'seller')

class InvoiceItemSerializer(serializers.ModelSerializer):
    seller = InvoiceUserSerializer(many=False, read_only=True)
    item_details = ItemDetailsSerializer(many=False, read_only=True)
    class Meta:
        model = Item
        fields = ('id', 'name', 'price', 'tax_percentage', 'tax_type', 'seller', 'item_details')

class OrderItemSerializer(serializers.ModelSerializer):
    seller = UserSerializer(many=False, read_only=True)
    class Meta:
        model = Item
        fields = ('id', 'name', 'price', 'seller')

class OrderSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer(many=False, read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ('id', 'order_date', 'items', 'total_price', 'grand_total', 'buyer', 'is_deleted')

class InvoiceOrderSerializer(serializers.ModelSerializer):
    buyer = InvoiceBuyerSerializer(many=False, read_only=True)
    class Meta:
        model = Order
        fields = ('id', 'buyer')

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    order = InvoiceOrderSerializer(many=False, read_only=True)
    class Meta:
        model = Invoice
        fields = ('id', 'items', 'order', 'total_tax', 'grand_total', 'is_deleted')

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'order', 'user', 'external_transaction_id', 'transaction_status')