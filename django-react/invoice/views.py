import json
import logging

from datetime import date
from decimal import Decimal

from click.core import Argument
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Address, Invoice, Item, Item_details, Order, User, Order_Item_Relationship, Transaction
from .serializers import (AddressSerializer, InvoiceSerializer, ItemSerializer,
                          OrderSerializer, UserSerializer, TransactionSerializer)

from hashlib import sha512
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

class UserListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('name')
    serializer_class = UserSerializer

class ItemListCreate(generics.ListCreateAPIView):
    queryset = Item.objects.all().order_by('name')
    serializer_class = ItemSerializer

class OrderListCreate(generics.ListCreateAPIView):
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer

class InvoiceListCreate(generics.ListCreateAPIView):
    queryset = Invoice.objects.all().order_by('id')
    serializer_class = InvoiceSerializer

class AddressListCreate(generics.ListCreateAPIView):
    queryset = Address.objects.all().order_by('id')
    serializer_class = AddressSerializer

@api_view(["GET"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_orders(request):
    
    orders = Order.objects.all().order_by('id')
    
    serializer = OrderSerializer(orders, many=True)
    return JsonResponse({'orders': serializer.data}, safe=False, status=status.HTTP_200_OK)

@api_view(["GET"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_order_by_id(request, order_id):
    try:
        order = Order.objects.get(id=order_id)

        serializer = OrderSerializer(order)
        return JsonResponse({'order': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while fetching order : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def create_order(request):
    payload = json.loads(request.body)
    try:
        if not 'items' in payload or len(payload['items']) == 0:
            return JsonResponse({'error': 'No items found in the order'}, safe=False, status=status.HTTP_417_EXPECTATION_FAILED)
        
        buyer = User.objects.get(id=payload['buyer_id'], user_type="BUYER")
        
        items = []
        total_tax_amt = 0
        total_amt = 0
        grand_total = 0

        for i in payload['items']:
            item = Item.objects.get(id=i['id'])
            logger.debug("Found item with id %s %s" % (i['id'], item))

            qty = getQty(i)

            if item:
                total_amt += Decimal(item.price * qty)
                item_tax_amount = Decimal.from_float(item.tax_percentage / 100) * (item.price) * (qty)
                total_tax_amt += item_tax_amount
                item.qty = qty
                items.append(item)

        grand_total += (total_tax_amt + total_amt)

        order = createOrder(buyer, total_amt, grand_total)

        populateItems(items, order)
            
        serializer = OrderSerializer(order)
        return JsonResponse({'order': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while creating order : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def populateItems(items, order):
    for item in items:
        order.items.add(item, through_defaults={'qty' : item.qty})

def createOrder(buyer, total_amt, grand_total):
    order = Order.objects.create(
        buyer=buyer,
        order_date=date.today(),
        total_price=total_amt,
        grand_total=grand_total
    )
    return order

def getQty(i):
    qty = 1

    if i['qty']:
        qty = i['qty']
    return qty

@api_view(["PUT"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def update_order(request, order_id):
    payload = json.loads(request.body)
    try:
        order_item = Order.objects.get(id=order_id)
        logger.debug("Found order_item with id %s %s" % (order_id, order_item))

        if 'items' in payload or len(payload['items']) != 0:
            items = []
            total_tax_amt = 0
            total_amt = 0
            grand_total = 0
            
            for i in payload['items']:
                item = Item.objects.get(id=i['id'])
                logger.debug("Found item with id %s %s" % (i['id'], item))

                qty = getQty(i)

                if item:
                    total_amt += Decimal(item.price * qty)
                    item_tax_amount = Decimal.from_float(item.tax_percentage / 100) * (item.price) * (qty)
                    total_tax_amt += item_tax_amount
                    item.qty = qty
                    items.append(item)

            grand_total += (total_tax_amt + total_amt)

            order_item.total_price = total_amt
            order_item.grand_total = grand_total

            order_item.items.clear()

            populateItems(items, order_item)

            order_item.save()
    
        serializer = OrderSerializer(order_item)
        return JsonResponse({'order': serializer.data}, safe=False, status=status.HTTP_200_OK)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while updating order : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["DELETE"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_order(request, order_id):
    try:
        order_item = Order.objects.get(id=order_id)
        logger.debug("Found order_item with id %s %s" % (order_id, order_item))

        order_item.is_deleted = True
        order_item.save()
    
        serializer = OrderSerializer(order_item)
        return JsonResponse({'order': serializer.data}, safe=False, status=status.HTTP_200_OK)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while updating order : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_invoices(request):
    
    invoices = Invoice.objects.all().order_by('id')
    
    serializer = InvoiceSerializer(invoices, many=True) 
    return JsonResponse({'invoices': serializer.data}, safe=False, status=status.HTTP_200_OK)

@api_view(["GET"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_invoice_by_id(request, invoice_id):  
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        
        serializer = InvoiceSerializer(invoice)
        return JsonResponse({'invoice': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while fetching invoice : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def create_invoice(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        invoices = Invoice.objects.filter(order_id=order_id, is_deleted=False)
        
        buyer = order.buyer
        buyer_state = getBuyerState(buyer)
        
        clearPreviousInvoices(invoices)
        
        invoice = populateInvoice(order, buyer_state)

        serializer = InvoiceSerializer(invoice)
        return JsonResponse({'invoice': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while creating invoice : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def populateInvoice(order, buyer_state):
    items = []
    total_tax_amt = 0
    total_amt = 0
    grand_total = 0

    for item in order.items.all():
        
        if item:

            order_item_relationship = Order_Item_Relationship.objects.get(order_id=order.id,item_id=item.id)
            qty = order_item_relationship.qty
            
            total_amt += Decimal(item.price * qty)
            item_tax_amount = Decimal.from_float(item.tax_percentage / 100) * (item.price) * (qty)
            total_tax_amt += item_tax_amount

            seller_state = getSellerState(item)

            item.qty = qty
            item.item_details=getItemdetails(buyer_state, seller_state, item, item_tax_amount)
            items.append(item)

    grand_total += (total_tax_amt + total_amt)

    invoice = buildInvoice(order, total_tax_amt, total_amt, grand_total)
    
    for item in items:
        invoice.items.add(item, through_defaults={'qty' : item.qty, 'item_details' : item.item_details})
    
    return invoice

def buildInvoice(order, total_tax_amt, total_amt, grand_total):
    #for now sticking to single seller model 
    invoice = Invoice.objects.create(
        order=order,
        total_tax=total_tax_amt,
        total_price=total_amt,
        grand_total=grand_total
    )

    return invoice

def getItemdetails(buyer_state, seller_state, item, item_tax_amount):
    if(buyer_state != seller_state):
        item_details = Item_details.objects.create(
            igst_tax_percentage=item.tax_percentage,
            igst_amt=item_tax_amount
        )
    else:
        item_details = Item_details.objects.create(
            sgst_tax_percentage=Decimal.from_float(item.tax_percentage / 2),
            cgst_tax_percentage=Decimal.from_float(item.tax_percentage / 2),
            sgst_amt=Decimal(item_tax_amount / 2),
            cgst_amt=Decimal(item_tax_amount / 2) 
        )
    return item_details

def getSellerState(item):
    seller_state = None
    seller = item.seller
    
    if seller:
        seller_address = Address.objects.get(user_id=seller.id)
        if seller_address:
            seller_state = seller_address.state
            logger.debug("Found seller state for item %s " % seller_state)
    
    return seller_state

def clearPreviousInvoices(invoices):
    if invoices or len(invoices) != 0:  
        for i in invoices:
            i.is_deleted = True
            i.items.clear()
            i.save()

def getBuyerState(buyer):
    buyer_state = None
    buyer_address = Address.objects.get(user_id=buyer.id)
    
    if buyer_address:
        buyer_state = buyer_address.state
    
    return buyer_state

@api_view(["DELETE"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_invoice(request, invoice_id):
    try:
        invoice_item = Invoice.objects.get(id=invoice_id)
        logger.debug("Found invoice_item with id %s %s" % (invoice_id, invoice_item))

        invoice_item.is_deleted = True
        invoice_item.save()
    
        serializer = InvoiceSerializer(invoice_item)
        return JsonResponse({'invoice': serializer.data}, safe=False, status=status.HTTP_200_OK)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while deleting invoice : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def make_payment(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        
        txn_id = data['txn_id']
        order_id = data['order_id']
        merchantKey = '##########'
        merchantSalt = '##########'

        order = Order.objects.get(id=order_id)
        if order.order_payment_status == 'PAID':
            return JsonResponse({'error': 'Cannot process reequest as Order payment status is already %s' % order.order_payment_status}, safe=False, status=status.HTTP_417_EXPECTATION_FAILED)
        
        existing_transaction = Transaction.objects.filter(order_id=order_id, external_transaction_id=txn_id).first()
        if existing_transaction:
            if existing_transaction.transaction_status in ['INITIATED', 'SUCCESS']:
                return JsonResponse({'error': 'Transaction cannot be processed as an already existing transaction exists for this order in the system'}, safe=False, status=status.HTTP_403_FORBIDDEN)

        buyer = order.buyer
        
        hashString = merchantKey + '|' + txn_id + '|' + str(order.grand_total) + '|' + buyer.name + '|' + buyer.email + '|' + '||||||||||' + merchantSalt
        hashFinal = sha512(hashString.encode('utf-8')).hexdigest()

        order.order_payment_status = 'IN_PROCESS'
        order.save()

        transaction = createTransaction(order, buyer, txn_id, hashFinal)

        serializer = TransactionSerializer(transaction)
        return JsonResponse({'invoice': serializer.data}, safe=False, status=status.HTTP_200_OK)
    
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while making payment : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def createTransaction(order, buyer, txn_id, hashFinal):
    transaction = Transaction.objects.create(
        order=order,
        user=buyer,
        external_transaction_id=txn_id,
        transaction_hash=hashFinal,
        transaction_status='INITIATED'
    )
    return transaction

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def save_transaction_status(request):
    try:
        data = json.loads(request.body.decode("utf-8"))

        txn_id = data['txn_id']
        txnStatus = data['txnStatus']
        
        transaction = Transaction.objects.get(external_transaction_id=txn_id)  

        if transaction.transaction_status in ['SUCCESS', 'FAILURE']:
            return JsonResponse({'error': 'Cannot process reequest as Transaction already marked as %s' % transaction.transaction_status}, safe=False, status=status.HTTP_417_EXPECTATION_FAILED)

        transaction.transaction_status = txnStatus
        transaction.save()

        if txnStatus == 'SUCCESS':
            order = transaction.order
            order.order_payment_status = 'PAID'
            order.save()
            return redirect("custom success page url")
        elif txnStatus == 'FAILED':
            return redirect("custom failure page url")

    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as Argument:
        logger.error("Exception caught while saving transaction status : %s" % Argument)
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
