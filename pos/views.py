import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from connect import connect_to_postgres
import os
from datetime import datetime, timedelta, timezone

BACKUP_FILE = "backup_penjualan.json"

@csrf_exempt
def create_sale_html(request):
    try:
        connection = connect_to_postgres()
        if connection is None:
            raise Exception("Error Koneksi ke Database Cloud")
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                sales_products = data.get("sales_products", [])
                if not sales_products:
                    return JsonResponse(
                        {"error": "Tidak ditemukan data sales_products pada request"}, status=400
                    )
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO Sales (sale_date, total_price) VALUES (NOW(), 0.0) RETURNING sale_date, id"
                    )
                    sale_date, sale_id = cursor.fetchone()
                total_price = 0
                sales_product_details = []
                with connection.cursor() as cursor:
                    for product in sales_products:
                        product_name = product.get("product_name")
                        quantity = product.get("quantity")
                        price = product.get("price")

                        if not product_name or not quantity or not price:
                            return JsonResponse(
                                {"error": "Ada data produk yang tidak lengkap"}, status=400
                            )

                        cursor.execute(
                            """
                            INSERT INTO SalesProduct (sales_id, product_name, quantity, price)
                            VALUES (%s, %s, %s, %s)
                            RETURNING product_name, quantity, price, (quantity * price) AS total_price
                            """,
                            [sale_id, product_name, quantity, price],
                        )
                        product_detail = cursor.fetchone()
                        sales_product_details.append(
                            {
                                "product_name": product_detail[0],
                                "quantity": product_detail[1],
                                "price": product_detail[2],
                                "total_price": product_detail[3],
                            }
                        )
                        total_price += product_detail[3]
                    cursor.execute(
                        "UPDATE Sales SET total_price = %s WHERE id = %s",
                        [total_price, sale_id],
                    )
                    connection.commit()
                return render(
                    request,
                    "sale_success.html",
                    {
                        "message_tersimpan": "Data penjualan sukses tersimpan ke database cloud",
                        "sale_id": sale_id,
                        "sale_date": sale_date,
                        "total_price": total_price,
                        "sales_products": sales_product_details,
                    },
                )
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
        else:
            return JsonResponse({"error": "Invalid request method"}, status=405)

    except Exception as e:
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                gmt_plus_7 = timezone(timedelta(hours=7))
                current_datetime = datetime.now(gmt_plus_7).strftime("%Y-%m-%d %H:%M:%S")
                data["sale_date"] = current_datetime
                sales_products = data.get("sales_products", [])
                total_price = 0
                sales_product_details = []
                for product in sales_products:
                    product_name = product.get("product_name")
                    quantity = product.get("quantity")
                    price = product.get("price")
                    total_price += quantity * price
                    sales_product_details.append(
                        {
                            "product_name": product_name,
                            "quantity": quantity,
                            "price": price,
                            "total_price": total_price,
                        }
                    )
                if os.path.exists(BACKUP_FILE):
                    with open(BACKUP_FILE, "r") as f:
                        backup_data = json.load(f)
                else:
                    backup_data = []

                backup_data.append(data)

                with open(BACKUP_FILE, "w") as f:
                    json.dump(backup_data, f, indent=4)

                return render(
                    request,
                    "sale_success.html",
                    {
                        "message_tersimpan": "Database cloud down. Data penjualan sukses tersimpan ke database lokal",
                        "sale_date": current_datetime,
                        "total_price": total_price,
                        "sales_products": sales_product_details,
                    },
                )
            except Exception as backup_error:
                return JsonResponse(
                    {"error": f"Backup failed: {str(backup_error)}"}, status=500
                )
        else:
            return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def process_backup_sales(request):
    if request.method == "POST":
        try:
            connection = connect_to_postgres()
            if connection is None:
                raise Exception("Error Koneksi ke Database Cloud")

            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, "r") as f:
                    backup_data = json.load(f)

                for data in backup_data:
                    sale_date = data.get("sale_date")
                    sales_products = data.get("sales_products", [])
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO Sales (sale_date, total_price) VALUES (%s, 0.0) RETURNING id",
                            (sale_date,)
                        )
                        sale_id = cursor.fetchone()[0]
                    print(sale_date)
                    total_price = 0
                    with connection.cursor() as cursor:
                        for product in sales_products:
                            product_name = product.get("product_name")
                            quantity = product.get("quantity")
                            price = product.get("price")

                            cursor.execute(
                                """
                                INSERT INTO SalesProduct (sales_id, product_name, quantity, price)
                                VALUES (%s, %s, %s, %s)
                                """,
                                [sale_id, product_name, quantity, price],
                            )
                            total_price += quantity * price

                        cursor.execute(
                            "UPDATE Sales SET total_price = %s WHERE id = %s",
                            [total_price, sale_id],
                        )
                    connection.commit()
                os.remove(BACKUP_FILE)
                return JsonResponse(
                    {"message": "Backup data sukses tersimpan ke database cloud."}, status=200
                )

            return JsonResponse({"message": "Tidak ada backup data yang ditemukan"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def add_sales_form(request):
    return render(request, "add_sales_form.html")
