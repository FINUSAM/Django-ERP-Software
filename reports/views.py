from django.shortcuts import render, redirect
from bills.models import SalesBill
from transactions.models import Purchase
from funds.models import Expense
from collections import defaultdict
from datetime import date as imported_date
from operator import itemgetter
from datetime import datetime
from django.utils import timezone

def daily_report(request):
    # Fetch all distinct dates for sales, purchases, and expenses
    sales_dates = SalesBill.objects.values_list('bill_date', flat=True).distinct()
    purchases_dates = Purchase.objects.values_list('date', flat=True).distinct()
    expenses_dates = Expense.objects.values_list('date', flat=True).distinct()

    # Combine all unique dates into one set
    all_dates = set(sales_dates) | set(purchases_dates) | set(expenses_dates)

    # Create a dictionary to hold the combined report
    report = defaultdict(lambda: {
        'cash_sales': 0,
        'upi_sales': 0,
        'cash_purchases': 0,
        'upi_purchases': 0,
        'cash_expenses': 0,
        'upi_expenses': 0
    })

    # Aggregate sales
    for date in sales_dates:
        sales_bills = SalesBill.objects.filter(bill_date=date)

        cash_sales = sum(
            sales_bill.total_amount_after_discount 
            for sales_bill in sales_bills
            if sales_bill.fund.name == 'Cash'
        )

        upi_sales = sum(
            sales_bill.total_amount_after_discount 
            for sales_bill in sales_bills
            if sales_bill.fund.name == 'Upi'
        )

        report[date]['cash_sales'] = cash_sales
        report[date]['upi_sales'] = upi_sales

    # Aggregate purchases
    for date in purchases_dates:
        purchase_bills = Purchase.objects.filter(date=date)
        upi_purchases = sum(
            purchases_bill.net_total_price
            for purchases_bill in purchase_bills
            if purchases_bill.fund.name == 'Upi'
        )
        cash_purchases = sum(
            purchases_bill.net_total_price
            for purchases_bill in purchase_bills
            if purchases_bill.fund.name == 'Cash'
        )

        report[date]['upi_purchases'] = upi_purchases
        report[date]['cash_purchases'] = cash_purchases

    # Aggregate expenses
    for date in expenses_dates:
        expense_bills = Expense.objects.filter(date=date)

        cash_expenses = sum(
            expenses_bill.amount 
            for expenses_bill in expense_bills
            if expenses_bill.fund.name == 'Cash'
        )

        upi_expenses = sum(
            expenses_bill.amount 
            for expenses_bill in expense_bills
            if expenses_bill.fund.name == 'Upi'
        )

        report[date]['cash_expenses'] = cash_expenses
        report[date]['upi_expenses'] = upi_expenses

    # Convert report to a list of dicts sorted by date
    report_list = [{
        'date': date,
        'cash_sales': data['cash_sales'],
        'upi_sales': data['upi_sales'],
        'cash_purchases': data['cash_purchases'],
        'upi_purchases': data['upi_purchases'],
        'cash_expenses': data['cash_expenses'],
        'upi_expenses': data['upi_expenses']}
        for date, data in report.items()]
    
    for i in report_list:
        print(i['date'])

    # Sort the report by date (newest first)
    report_list.sort(key=lambda x: x['date'], reverse=True)

    context = {
        'report_name': 'Daily', 
        'report': report_list
    }

    # Return the report as a JsonResponse
    return render(request, 'daily_report.html', context)


def monthly_report(request):
    # Fetch all distinct dates for sales, purchases, and expenses
    sales_dates = SalesBill.objects.values_list('bill_date', flat=True).distinct()
    purchases_dates = Purchase.objects.values_list('date', flat=True).distinct()
    expenses_dates = Expense.objects.values_list('date', flat=True).distinct()

    # Combine all unique months into one set (year-month format)
    all_months = set(
        (date.year, date.month) for date in sales_dates
    ) | set(
        (date.year, date.month) for date in purchases_dates
    ) | set(
        (date.year, date.month) for date in expenses_dates
    )

    # Create a dictionary to hold the combined report
    report = defaultdict(lambda: {'sales': 0, 'discount': 0, 'purchases': 0, 'expenses': 0})

    # Aggregate sales by year-month
    for date in sales_dates:
        year_month = (date.year, date.month)
        sales_bills = SalesBill.objects.filter(bill_date__year=date.year, bill_date__month=date.month)
        total_sales = sum(sales_bill.total_amount_after_discount for sales_bill in sales_bills)
        sales_discount = sum(sales_bill.discount_price for sales_bill in sales_bills)
        report[year_month]['sales'] = total_sales
        report[year_month]['discount'] =  sales_discount

    # Aggregate purchases by year-month
    for date in purchases_dates:
        year_month = (date.year, date.month)
        purchase_bills = Purchase.objects.filter(date__year=date.year, date__month=date.month)
        total_purchases = sum(purchases_bill.net_total_price for purchases_bill in purchase_bills)
        report[year_month]['purchases'] = total_purchases

    # Aggregate expenses by year-month
    for date in expenses_dates:
        year_month = (date.year, date.month)
        expense_bills = Expense.objects.filter(date__year=date.year, date__month=date.month)
        total_expenses = sum(expenses_bill.amount for expenses_bill in expense_bills)
        report[year_month]['expenses'] = total_expenses

    # Convert report to a list of dicts sorted by year-month
    report_list = [{
        'date': imported_date(year, month, 1),  # Use real date object (first day of the month)
        'sales': data['sales'],
        'discount': data['discount'],
        'purchases': data['purchases'],
        'expenses': data['expenses'],
        'total': data['sales'] - data['purchases'] - data['expenses']
    } for (year, month), data in report.items()]

    # Sort the report by year-month (newest first)
    report_list.sort(key=lambda x: x['date'], reverse=True)

    totals = {
        'sales': sum(item['sales'] for item in report_list),
        'purchases': sum(item['purchases'] for item in report_list),
        'expenses': sum(item['expenses'] for item in report_list),
        'total': sum(item['total'] for item in report_list)
    }

    context = {
        'report_name': 'Monthly', 
        'report': report_list, 
        'totals': totals
    }

    # Return the report as a JsonResponse
    return render(request, 'monthly_report.html', context)


def profit_report(request):
    # Fetch all distinct dates for sales, purchases, and expenses
    sales_dates = SalesBill.objects.values_list('bill_date', flat=True).distinct()
    expenses_dates = Expense.objects.values_list('date', flat=True).distinct()

    # Combine all unique dates into one set
    all_dates = set(sales_dates) | set(expenses_dates)

    # Create a dictionary to hold the combined report
    report = defaultdict(lambda: {
        'sales': 0,
        'profit': 0,
        'expenses': 0
    })

    # Aggregate sales
    for date in sales_dates:
        sales_bills = SalesBill.objects.filter(bill_date=date)

        sales = sum(
            sales_bill.total_amount_after_discount 
            for sales_bill in sales_bills
        )

        profit = sum(
            sales_bill.profit
            for sales_bill in sales_bills
        )

        report[date]['sales'] = sales
        report[date]['profit'] = profit

    # Aggregate expenses
    for date in expenses_dates:
        expense_bills = Expense.objects.filter(date=date)

        expenses = sum(
            expenses_bill.amount 
            for expenses_bill in expense_bills
        )

        report[date]['expenses'] = expenses

    # Convert report to a list of dicts sorted by date
    report_list = [{
        'date': date,
        'sales': data['sales'],
        'sales_profit': data['profit'],
        'expenses': data['expenses'],
        'net_profit': data['profit'] - data['expenses']}
        for date, data in report.items()]
    
    for i in report_list:
        print(i['date'])

    # Sort the report by date (newest first)
    report_list.sort(key=lambda x: x['date'], reverse=True)

    context = {
        'report_name': 'Profit', 
        'report': report_list
    }

    # Return the report as a JsonResponse
    return render(request, 'profit_report.html', context)


def day_book(request, date):
    sales_bills = SalesBill.objects.filter(bill_date=date)
    expense_bills = Expense.objects.filter(date=date)
    purchase_bills = Purchase.objects.filter(date=date)

    all_bills = []

    for bill in sales_bills:
        all_bills.append({
            'time':bill.bill_time,
            'type':'Sales',
            'mode':bill.fund.name,
            'amount':bill.total_amount_after_discount,
            'desc':bill.stocks
        })

    for bill in expense_bills:
        all_bills.append({
            'time':bill.time,
            'type':f'Expense',
            'mode':bill.fund.name,
            'amount':bill.amount,
            'desc':{bill.expense_type:bill.description}
        })

    for bill in purchase_bills:
        all_bills.append({
            'time':bill.time,
            'type':'Purchase',
            'mode':bill.fund.name,
            'amount':bill.net_total_price,
            'desc':{bill.stockset.name:bill.net_quantity}
        })

    
    # Sorting the bills based on time
    all_bills = sorted(all_bills, key=itemgetter('time'), reverse=True)

    # Pass the sorted bills to the template
    context = {
        'all_bills': all_bills,
        'date': datetime.strptime(date, "%Y-%m-%d").date(),
    }

    return render(request, 'day_book.html', context)


def redirect_to_selected_day_book(request):
    # Get the selected date from the query parameter
    selected_date = request.GET.get('date')

    if not selected_date:
        # If no date is selected, redirect to today's date
        today = datetime.today().strftime('%Y-%m-%d')
        return redirect('day_book', date=today)

    # Redirect to the daybook view with the selected date
    return redirect('day_book', date=selected_date)












