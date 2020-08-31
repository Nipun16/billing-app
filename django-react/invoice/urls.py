from django.urls import path

from invoice.views import InvoiceListCreate

from . import views

urlpatterns = [
    path('api/user/createview', views.UserListCreate.as_view()),
    path('api/item/createview', views.ItemListCreate.as_view()),
    path('api/order/createview', views.OrderListCreate.as_view()),
    path('api/invoice/createview', views.InvoiceListCreate.as_view()),
    path('api/address/createview', views.AddressListCreate.as_view()),

    path('api/get_orders', views.get_orders),
    path('api/get_order_by_id/<int:order_id>', views.get_order_by_id),
    path('api/create_order', views.create_order),
    path('api/update_order/<int:order_id>', views.update_order),
    path('api/delete_order/<int:order_id>', views.delete_order),

    path('api/get_invoices', views.get_invoices),
    path('api/get_invoice_by_id/<int:invoice_id>', views.get_invoice_by_id),
    path('api/create_invoice/<int:order_id>', views.create_invoice),
    path('api/delete_invoice/<int:invoice_id>', views.delete_invoice),

    path('api/make_payment', views.make_payment),
    path('api/save_transaction_status', views.save_transaction_status)
]
