from django.urls import path
from pos.views import create_sale_html, add_sales_form, process_backup_sales

app_name = "pos"

urlpatterns = [
    path("create_sale_form/", add_sales_form, name="create_sale_form"),
    path("process_backup/", process_backup_sales, name="process_backup"),
    path("api/create_sale/", create_sale_html, name="create_sale_json"),
]
