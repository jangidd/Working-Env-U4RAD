import os
from django.shortcuts import render, get_object_or_404, redirect
from .models.models import Service, ServiceRate
from .models.profile import Profile, UploadFile
from .models.CartItem import Cart
from .models.CartValue import CartValue
from .models.OrderHistory import OrderHistory
from .forms import ServiceForm, ServiceRateForm
from django.contrib.auth import login as ContribLogin, authenticate
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as ContribLogout
import json
from .forms import ProfileForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import messages
import logging
from django.conf import settings
import razorpay
from .models.Order import Order
from .models.OrderHistory import OrderHistory
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.core.serializers import serialize
from django.forms.models import model_to_dict
import openpyxl
from io import BytesIO
from django.views.decorators.http import require_POST
from datetime import timedelta

################################# imports for the multiform ########################################
#-----------------------------------------Himanshu-------------------------------------------------#
import io
from django.http import FileResponse
from datetime import datetime
from .forms import CallbackForm
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from datetime import date, timedelta
from .models.CallbackForm import Callback

# reportlab imports :
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import blue, black
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet , ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors

# model imports :
from .models.ratelist import RateList

from .models.personal_info import PersonalInformation
from .models.educational_info import EducationalDetails
from .models.workexp_info import ExperienceDetails
from .models.achievement_info import AchievementDetails
from .models.banking_info import BankingDetails 

from .models.reportingarea_info import ReportingAreaDetails
from .models.timeavailability_info import AvailabilityDetails
from .models.CallbackForm import Callback

from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.files.storage import default_storage
import zipfile
import re
################################ End of Multiform Imports ##########################################

def login(request):
    if request.method == 'POST':
        identifier = request.POST['identifier']
        password = request.POST.get('password')
        new_password = request.POST.get('new_password')

        # Check if the identifier is a phone number or an email
        if '@' in identifier:
            # Email-based login
            user = authenticate(request, username=identifier, password=password)
            if user is not None:
                ContribLogin(request, user)
                groups = user.groups.values_list('name', flat=True)
                if 'radiologist' in groups:
                    return redirect('work')
                elif 'supercoordinator' in groups:
                    return redirect('coordinator')
                elif 'coordinator' in groups:
                    return redirect('coordinator')
                else:
                    return render(request, 'services/login.html', {'error': 'Invalid credentials'})
            else:
                try:
                    personal_info = PersonalInformation.objects.get(email=identifier)
                    if personal_info.password == password:
                        context = {'personal_info': personal_info}
                        if personal_info.stage2status in ['under_progress', 'applied', 'verification_failed', 'verified_by_supercoordinator']:
                                return render(request, 'pending.html', context)
                    else:
                        return render(request, 'services/login.html', {'error': 'Invalid credentials'})
                except PersonalInformation.DoesNotExist:
                    return render(request, 'services/login.html', {'error': 'Invalid credentials'})
        else:
            # Phone number-based login
            if User.objects.filter(username=identifier).exists():
                if password:
                    user = authenticate(request, username=identifier, password=password)
                    if user is not None:
                        ContribLogin(request, user)
                        group = user.groups.values_list('name', flat=True).first()
                        if group == 'coordinator':
                            return redirect('coordinator')
                        else:
                            return redirect('quality')
                    else:
                        return render(request, 'services/login.html', {'error': 'Invalid login credentials'})
                else:
                    return render(request, 'services/login.html', {'error': 'Password is required for existing users'})
            else:
                if new_password:
                    new_user = User.objects.create_user(username=identifier, password=new_password)
                    ContribLogin(request, new_user)
                    return redirect('quality')
                else:
                    return render(request, 'services/login.html', {'error': 'Please provide a new password to create an account'})
    return render(request, 'services/login.html')

#------------------------------------------------------------

# def login(request):
#     if request.method == 'POST':
#         phone = request.POST['phone']
#         password = request.POST.get('password')
#         new_password = request.POST.get('new_password')

#         if User.objects.filter(username=phone).exists():
#             # Existing user
#             if password:  # Password should be provided for existing users
#                 user = authenticate(request, username=phone, password=password)
#                 if user is not None:
#                     ContribLogin(request, user)
#                     group = user.groups.values_list('name', flat=True).first()
#                     if group == 'coordinator':
#                         return redirect('service_list')
#                     else:
#                         return redirect('quality')
#                 else:
#                     return render(request, 'services/login.html', {'error': 'Invalid login credentials'})
#             else:
#                 return render(request, 'services/login.html', {'error': 'Password is required for existing users'})
#         else:
#             # New user
#             if new_password:
#                 new_user = User.objects.create_user(username=phone, password=new_password)
#                 ContribLogin(request, new_user)
#                 return redirect('quality')
#             else:
#                 return render(request, 'services/login.html', {'error': 'Please provide a new password to create an account'})

#     return render(request, 'services/login.html')

def logout(request):
    ContribLogout(request)
    return redirect('login')
    # return redirect(settings.LOGOUT_REDIRECT_URL)

############################## RAZORPAY ###################################

def home(request):
    return render(request, "services/index.html")

@login_required
def quality(request):
    return render(request, "services/quality.html")    

def update_payment_status(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(data)
        order = Order.objects.get(provider_order_id=data['order_id'])
        order.payment_id = data['payment_id']
        order.signature_id = data['signature']
        order.status = data['status']
        order.save()
        return HttpResponse(status=200)


@csrf_protect
def generate_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        profile = Profile.objects.get(user=request.user)
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        try:
            razorpay_order = client.order.create(
                {"amount": int(data['grand_total']) * 100, "currency": "INR", "payment_capture": "1"}
            )
        except razorpay.errors.BadRequestError as e:
            return render(request, "services/error.html", {"error": "Failed to create Razorpay order. Authentication failed."})

        # Create Order in your database
        order = Order.objects.create(
            name=profile.organization, amount=data['grand_total'], provider_order_id=razorpay_order["id"], user=request.user
        )
        order.save()

        return JsonResponse({'message': 'RZP Order generated successfully', 'order_id': order.provider_order_id, 'amount': int(data['grand_total']) * 100, 'key': settings.RAZORPAY_KEY_ID, 'user': { 'name': profile.organization, 'email': profile.email, 'contact': profile.user.username }})

    return render(request, "services/payment.html")

@csrf_protect
def generate_topup_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        profile = Profile.objects.get(user=request.user)
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

         # Create Razorpay order
        try:
            razorpay_order = client.order.create(
                {"amount": int(data['topup_amount']) * 100, "currency": "INR", "payment_capture": "1"}
            )
        except razorpay.errors.BadRequestError as e:
            return render(request, "services/error.html", {"error": "Failed to create Razorpay order. Authentication failed."})
        
        # Create Order in your database
        order = Order.objects.create(
            name=profile.organization, amount=data['topup_amount'], provider_order_id=razorpay_order["id"], user=request.user
        )
        order.save()
        return JsonResponse({'message': 'RZP Order generated successfully', 'order_id': order.provider_order_id, 'amount': int(data['topup_amount']) * 100, 'key': settings.RAZORPAY_KEY_ID, 'user': { 'name': profile.organization, 'email': profile.email, 'contact': profile.user.username }})

    return render(request, "services/payment.html")
############################################################################

@login_required
def user_dashboard(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        cart_value = CartValue.objects.filter(user=request.user).first()
        orders = Order.objects.filter(user=request.user)
        context = {
            'cart_items': cart_items,
            'cart_value': cart_value,
            'orders': orders
        }
        return render(request, 'services/user_dashboard.html', context)
    else:
        return redirect('login')  # Redirect to login page if user is not authenticated
    


# def download_invoice(request):
#     if not request.user.is_authenticated:
#         return redirect('login')

#     # Get the last order for the current user
#     last_order = Order.objects.filter(user=request.user).order_by('-order_date').first()

#     if not last_order:
#         return HttpResponse("No orders found.", content_type='text/plain')

#     # Calculate the time window for filtering order histories (±5 minutes)
#     time_window_start = last_order.order_date - timedelta(minutes=5)
#     time_window_end = last_order.order_date + timedelta(minutes=5)

#     # Get all order histories for the user within the time window
#     last_order_histories = OrderHistory.objects.filter(
#         user=request.user,
#         order_date__range=(time_window_start, time_window_end)
#     )

#     workbook = openpyxl.Workbook()
#     sheet = workbook.active
#     sheet.title = "Invoice"

#     # Add order histories to the sheet
#     if last_order_histories.exists():
#         sheet['A1'] = 'Order History'
#         sheet.append(['Service Name', 'Quantity', 'Amount'])
#         for history in last_order_histories:
#             service_name = history.service_name
#             quantity = history.quantity
#             amount = history.amount
#             sheet.append([service_name, quantity, amount])

#     sheet.append([])  # Empty row

#     # Add the last order details to the sheet
#     if last_order:
#         sheet.append(['Order'])
#         sheet.append(['Order ID', 'Customer Name', 'Amount', 'Status', 'Payment ID', 'Signature ID'])
#         provider_order_id = last_order.provider_order_id
#         name = last_order.name
#         amount = last_order.amount
#         status = last_order.status
#         payment_id = last_order.payment_id
#         signature_id = last_order.signature_id
#         sheet.append([provider_order_id, name, amount, status, payment_id, signature_id])

#     # Save the workbook to a BytesIO object
#     response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = 'attachment; filename=invoice.xlsx'
#     buffer = BytesIO()
#     workbook.save(buffer)
#     buffer.seek(0)
#     response.write(buffer.read())
#     return response

def download_invoice(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get the last order for the current user
    last_order = Order.objects.filter(user=request.user).order_by('-order_date').first()

    if not last_order:
        return HttpResponse("No orders found.", content_type='text/plain')

    # Calculate the time window for filtering order histories (±5 minutes)
    time_window_start = last_order.order_date - timedelta(minutes=5)
    time_window_end = last_order.order_date + timedelta(minutes=5)

    # Get all order histories for the user within the time window
    last_order_histories = OrderHistory.objects.filter(
        user=request.user,
        order_date__range=(time_window_start, time_window_end)
    )

    # Create a BytesIO buffer to receive the PDF data
    buffer = BytesIO()

    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    elements = []

    # Add the new logo
    logo_path = os.path.join('services', 'static', 'image', 'Logo.png')
    if os.path.isfile(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
        elements.append(logo)
    else:
        elements.append(Paragraph("Logo not found", getSampleStyleSheet()['Normal']))

    # Add a title
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title = "Invoice"
    elements.append(Paragraph(title, title_style))

    # Add a space
    elements.append(Spacer(1, 12))

    # Customer Details
    customer_name = last_order.name
    order_date = last_order.order_date.strftime('%Y-%m-%d %H:%M:%S')
    
    customer_details = [
        ['Customer Details'],
        ['Customer Name:', customer_name],
        ['Date:', order_date]
    ]
    
    customer_table = Table(customer_details, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (0, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(customer_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Service Details Heading
    service_details_heading = [['Service Details']]
    service_heading_table = Table(service_details_heading, colWidths=[6*inch])
    service_heading_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(service_heading_table)

    # Service Details
    service_details = [['S.No', 'Service', 'Quantity', 'Amount']]
    for idx, history in enumerate(last_order_histories, start=1):
        service_details.append([
            str(idx),
            history.service_name,
            str(history.quantity),
            f"{history.amount:.2f}"
        ])

    service_table = Table(service_details, colWidths=[0.5*inch, 2*inch, 1.5*inch, 2*inch])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(service_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Order Details Heading
    order_details_heading = [['Order Details']]
    order_heading_table = Table(order_details_heading, colWidths=[6*inch])
    order_heading_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(order_heading_table)

    # Add last order details
    order_data = [
        ['Order ID', 'Amount', 'Status', 'Payment ID', 'Signature ID'],
        [last_order.provider_order_id, f"{last_order.amount:.2f}", last_order.status, last_order.payment_id, last_order.signature_id]
    ]

    # Transpose order data for columnar display
    transposed_order_data = list(map(list, zip(*order_data)))

    order_table = Table(transposed_order_data, colWidths=[1.1*inch, 4.9*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), '#d0d0d0'),  # Background for the first column
        ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
    ]))
    elements.append(order_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Declaration and Signature table
    declaration_details = [
        ['Declaration', 'Signature'],
        ['We declare that this invoice shows the actual \n price of the services described and that all \n    particulars are true and correct.', 'U4RAD Technologies LLP\n(Authorised Signatory)']
    ]

    declaration_table = Table(declaration_details, colWidths=[3*inch, 3*inch])
    declaration_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(declaration_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Footer
    footer_data = [
        ['U4RAD Technologies LLP'],
        ['XRAI DIGITAL'],
        ['C406, 4th Floor Nirvana Courtyard, Sector-50 Gurugram Haryana 122018'],
        ['PAN: AAGFU2874A, UAM: HR05E0030329 LLPIN: AAR-6317'],
        ['GSTIN : 06AAGFU2874A1ZC'],
        ['Contact: 0124 - 4254012, Email: info@xraidigital.com']
    ]

    footer_table = Table(footer_data, colWidths=[6*inch])
    footer_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
    ]))
    elements.append(footer_table)

    # Footer Note
    footer_note_style = ParagraphStyle(name='FooterNote', alignment=1, fontName='Helvetica-Bold')
    footer_note = Paragraph(
        "* This is a computer-generated invoice and does not require a physical signature *",
        footer_note_style
    )

    # Add a spacer to push the footer note to the bottom
    elements.append(Spacer(1, 100))
    elements.append(footer_note)

    # Build the PDF
    doc.build(elements)

    # Get the PDF data from the buffer
    pdf_data = buffer.getvalue()
    buffer.close()

    # Create a response to return the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    response.write(pdf_data)

    return response

# This view i have created to download a single order invoice on the coordinator page (customer's dashboard.)
@login_required
def download_single_invoice(request, user_id, provider_order_id):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch the user profile
    user_profile = get_object_or_404(Profile, user_id=user_id)
    user = user_profile.user  # Get the User instance

    # Fetch the specific order using provider_order_id
    order = get_object_or_404(Order, provider_order_id=provider_order_id, user=user)

    # Get all order histories for the specific order
    order_histories = OrderHistory.objects.filter(user=user)  # Use the User instance

    # Create a BytesIO buffer to receive the PDF data
    buffer = BytesIO()

    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    elements = []

    # Add the new logo
    logo_path = os.path.join('services', 'static', 'image', 'Logo.png')
    if os.path.isfile(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
        elements.append(logo)
    else:
        elements.append(Paragraph("Logo not found", getSampleStyleSheet()['Normal']))

    # Add a title
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title = "Invoice"
    elements.append(Paragraph(title, title_style))

    # Add a space
    elements.append(Spacer(1, 12))

    # Customer Details
    customer_name = order.name
    order_date = order.order_date.strftime('%Y-%m-%d %H:%M:%S')
    
    customer_details = [
        ['Customer Details'],
        ['Customer Name:', customer_name],
        ['Date:', order_date]
    ]
    
    customer_table = Table(customer_details, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (0, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(customer_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Service Details Heading
    service_details_heading = [['Service Details']]
    service_heading_table = Table(service_details_heading, colWidths=[6*inch])
    service_heading_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(service_heading_table)

    # Initialize service_details to avoid UnboundLocalError
    service_details = []

    # Append service details table if order histories are available
    if order_histories.exists():
        service_details = [['S.No', 'Service', 'Quantity', 'Amount']]
        for idx, history in enumerate(order_histories, start=1):
            service_details.append([
                str(idx),
                history.service_name,
                str(history.quantity),
                f"{history.amount:.2f}"
            ])

        service_table = Table(service_details, colWidths=[0.5*inch, 2*inch, 1.5*inch, 2*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(service_table)
    else:
        # Create a table with a single row for the message
        no_service_details = [['No service details available.']]
        no_service_table = Table(no_service_details, colWidths=[6*inch])
        no_service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(no_service_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Order Details Heading
    order_details_heading = [['Order Details']]
    order_heading_table = Table(order_details_heading, colWidths=[6*inch])
    order_heading_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(order_heading_table)

    # Add order details
    order_data = [
        ['Order ID', 'Amount', 'Status', 'Payment ID', 'Signature ID'],
        [order.provider_order_id, f"{order.amount:.2f}", order.status, order.payment_id, order.signature_id]
    ]

    # Transpose order data for columnar display
    transposed_order_data = list(map(list, zip(*order_data)))

    order_table = Table(transposed_order_data, colWidths=[1.1*inch, 4.9*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), '#d0d0d0'),  # Background for the first column
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
    ]))
    elements.append(order_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Declaration and Signature table
    declaration_details = [
        ['Declaration', 'Signature'],
        ['We declare that this invoice shows the actual \n price of the services described and that all \n    particulars are true and correct.', 'U4RAD Technologies LLP\n(Authorised Signatory)']
    ]

    declaration_table = Table(declaration_details, colWidths=[3*inch, 3*inch])
    declaration_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(declaration_table)

    # Add a space
    elements.append(Spacer(1, 12))

    # Footer
    footer_data = [
        ['U4RAD Technologies LLP'],
        ['XRAI DIGITAL'],
        ['C406, 4th Floor Nirvana Courtyard, Sector-50 Gurugram Haryana 122018'],
        ['PAN: AAGFU2874A, UAM: HR05E0030329 LLPIN: AAR-6317'],
        ['GSTIN : 06AAGFU2874A1ZC'],
        ['Contact: 0124 - 4254012, Email: info@xraidigital.com']
    ]

    footer_table = Table(footer_data, colWidths=[6*inch])
    footer_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
    ]))
    elements.append(footer_table)

    # Footer Note
    footer_note_style = ParagraphStyle(name='FooterNote', alignment=1, fontName='Helvetica-Bold')
    footer_note = Paragraph(
        "* This is a computer-generated invoice and does not require a physical signature *",
        footer_note_style
    )

    # Add a spacer to push the footer note to the bottom
    elements.append(Spacer(1, 100))
    elements.append(footer_note)


    # Build the PDF
    doc.build(elements)

    # Get the PDF value from buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Send the PDF response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.provider_order_id}.pdf"'

    return response


@login_required
def coordinator_dashboard(request):
    # Fetch all profiles and cart items
    profiles = Profile.objects.select_related('user').all().order_by('-id')
    cart_items = Cart.objects.select_related('user', 'service').all()
    all_orders = Order.objects.select_related('user').all()

    # Create a dictionary to hold orders for each user
    orders_dict = {}
    for profile in profiles:
        user_orders = all_orders.filter(user=profile.user)
        orders_dict[profile.user.id] = user_orders

    context = {
        'profiles': profiles,
        'cart_items': cart_items,
        'orders_dict': orders_dict,
    }

    return render(request, 'services/coordinator_dashboard.html', context)

@login_required
def get_user_orders(request, user_id):
    try:
        profile = Profile.objects.get(user_id=user_id)
        orders = Order.objects.filter(user=profile.user).values(
            'provider_order_id', 'name', 'amount', 'status', 'payment_id'
        ).order_by('-provider_order_id')
        orders_list = list(orders)
        return JsonResponse({'status': 'success', 'orders': orders_list})
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_user_files(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    files = profile.uploads.all().order_by('-id')
    files_data = [{'id': file.id, 'file_name': file.file.name, 'file_url': file.file.url} for file in files]
    
    return JsonResponse({'status': 'success', 'files': files_data})

def download_all_files_as_zip(request, user_id):
    try:
        profile = Profile.objects.get(user_id=user_id)
        files = profile.uploads.all()

        if not files:
            return JsonResponse({'status': 'error', 'message': f'No files present for {profile.user.username}'})
        
        zip_subdir = profile.user.username
        zip_filename = f"{zip_subdir}.zip"

        s = io.BytesIO()
        with zipfile.ZipFile(s, "w") as zf:
            for file in files:
                file_path = default_storage.path(file.file.name)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    file_name = os.path.basename(file_path)
                    zip_path = os.path.join(zip_subdir, file_name)
                    zf.writestr(zip_path, file_data)

        s.seek(0)
        response = HttpResponse(s, content_type="application/zip")
        response['Content-Disposition'] = f'attachment; filename={zip_filename}'
        return response

    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Profile not found'})


@require_POST
def update_casecount(request, cart_item_id):
    cart_item = get_object_or_404(Cart, pk=cart_item_id)
    casecount = request.POST.get('casecount')
    cart_item.casecount = casecount
    cart_item.save()
    return redirect('coordinator_dashboard')


def update_profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()  # Redirect to payment success after updating the profile
            return JsonResponse({'success': True})  # Return success JSON response
    else:
        form = ProfileForm(instance=user_profile)

    return render(request, 'services/update_profile.html', {'form': form})

@require_POST
def upload_file(request, profileId):
    profile = get_object_or_404(Profile, id=profileId)
    if 'file' in request.FILES:
        file = request.FILES['file']
        upload_file = UploadFile(profile=profile, file=file)
        upload_file.save()
        return JsonResponse({'status': 'success', 'message': 'File uploaded successfully!'})
    else:
        return JsonResponse({'status': 'error', 'message': 'No file chosen!'})

def download_latest_file(request, user_id):
    # Find the profile for the user
    profile = Profile.objects.filter(user_id=user_id).first()
    
    if not profile:
        return JsonResponse({'error': 'No Profile found for this user.'}, status=400)
    
    # Find the latest uploaded file associated with this profile
    latest_file = UploadFile.objects.filter(profile=profile).order_by('-upload_time').first()
    
    if latest_file:
        file_path = latest_file.file.path
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{latest_file.file.name}"'
            return response
    else:
        return JsonResponse({'error': 'No file found for this profile.'}, status=400)
        
########################################### 26-06 ###############################################
@login_required
def save_cart_data(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received Data:", data)
            user = request.user
            cart_items = data.get('cart_items', [])
            promo_code = data.get('promo_code', '')
            total_amount = data.get('total_amount', 0)
            discount = data.get('discount', 0)
            grand_total = data.get('grand_total', 0)

            # Fetch the latest cart value for the user, if it exists
            cart_value, created = CartValue.objects.get_or_create(user=user)

            if not created:
                # Add the values to the existing ones
                cart_value.total_amount += total_amount
                cart_value.discount += discount
                cart_value.grand_total += grand_total
            else:
                # If it's a new CartValue instance, set the values
                cart_value.total_amount = total_amount
                cart_value.discount = discount
                cart_value.grand_total = grand_total
            cart_value.promo_code = promo_code
            cart_value.save()

            print(f"Cart Value Updated: {cart_value}")

            # Process each cart item only if there are items in the cart
            if cart_items:
                for item in cart_items:
                    quantity = item.get('quantity')
                    amount = item.get('amount')
                    service_name = item.get('service_name')

                    # Ensure all required fields are present
                    if not all([quantity, amount, service_name]):
                        return JsonResponse({'error': 'Missing fields in cart item'}, status=400)

                    try:
                        # Retrieve the Service instance using service_name
                        service = Service.objects.get(service_name=service_name)
                    except Service.DoesNotExist:
                        return JsonResponse({'error': f'Service "{service_name}" not found'}, status=404)

                    # Save the order to OrderHistory
                    OrderHistory.objects.create(
                        user=user,
                        service_name=service_name,
                        quantity=quantity,
                        amount=amount
                    )

                    # Check if a cart with the same user and service already exists
                    cart_instance, created = Cart.objects.get_or_create(user=user, service=service)

                    # If a cart with the same user and service already exists, update its fields
                    if not created:
                        cart_instance.quantity += quantity
                        cart_instance.amount += amount
                    else:
                        # If it doesn't exist, create a new cart instance
                        cart_instance.quantity = quantity
                        cart_instance.amount = amount
                    cart_instance.save()

                    print(f"Cart Item Updated: {cart_instance}")

             # Call the checkUserInCart function after saving cart data
            checkUserInCart(user)

            return JsonResponse({'message': 'Cart data saved successfully', 'cart': cart_value.pk}, status=201)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def checkUserInCart(user):
    # Fetch all services
    all_services = Service.objects.all()
    
    for service in all_services:
        # Check if a cart with the same user and service already exists
        cart_instance, created = Cart.objects.get_or_create(user=user, service=service)
        
        if created:
            # If it doesn't exist, create a new cart instance with zero data
            cart_instance.quantity = 0
            cart_instance.amount = 0
            cart_instance.save()
            print(f"New Cart Item Created: {cart_instance}")
        else:
            print(f"Cart Item Already Exists: {cart_instance}")

#################################################################################################


def payment_success(request):
    return render(request, 'services/payment_success.html')





def check_profile_completion(request):
    user = request.user
    if hasattr(user, 'profile'):
        user_profile = user.profile
        print("User Email:", user_profile.email)
        print("User Address:", user_profile.address)
        print("User Organization:", user_profile.organization)
        
        profile_complete = all([
            user_profile.email, 
            user_profile.address, 
            user_profile.organization
        ])
        print("Profile Complete:", profile_complete)
        
        return JsonResponse({"profile_complete": profile_complete})
    else:
        print("User profile does not exist.")
        return JsonResponse({"profile_complete": False, "message": "User profile does not exist."})
    




@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)





def checkout(request):
    try:
        user = User.objects.filter(username=request.user.username).first()
        
        if not user:
            return redirect('update_profile')

        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)

        if not user.email or not user.profile.address or not user.profile.organization:
            return redirect('update_profile')

        return redirect('payment_success')

    except Exception as e:
        logging.exception("An error occurred during checkout:")
        return render(request, 'error.html', {'error': str(e)})
    

@login_required
def get_user_details(request):
    profile = Profile.objects.get(user=request.user)
    user_details = {
        'username': profile.user.username,
        'organization': profile.organization,
        'email': profile.email,
        'address': profile.address,
    }
    print(user_details)
    return JsonResponse({'success': True, 'user': user_details})


# def check_user_exists(request):
#     phone = request.GET.get('phone')
#     exists = User.objects.filter(username=phone).exists()
#     return JsonResponse({'exists': exists})

def check_user_exists(request):
    phone = request.GET.get('phone')
    personalinfoexists = PersonalInformation.objects.filter(contact_no=phone).exists()
    servicesphoneexists = User.objects.filter(username=phone).exists()
    exists = personalinfoexists or servicesphoneexists
    return JsonResponse({'exists': exists})



def convert_decimal(value):
    return int(value)



@login_required
def calculate_amount(request):
    services = Service.objects.filter(is_active=True).prefetch_related('rates')
    services_with_rates = []

    for service in services:
        rates = list(service.rates.values('min_quantity', 'max_quantity', 'rate'))
        for rate in rates:
            rate['rate'] = convert_decimal(rate['rate'])
        services_with_rates.append({
            'id': service.id,
            'service_name': service.service_name,
            'rates_json': json.dumps(rates),
            'rates': rates,
        })

    return render(request, 'services/calculate_amount.html', {'services': services_with_rates})





def cart(request):
    services = Service.objects.filter(is_active=True).prefetch_related('rates')
    services_with_rates = []

    for service in services:
        rates = list(service.rates.values('min_quantity', 'max_quantity', 'rate'))
        for rate in rates:
            rate['rate'] = convert_decimal(rate['rate'])
        services_with_rates.append({
            'id': service.id,
            'service_name': service.service_name,
            'rates_json': json.dumps(rates)
        })
    return render(request, 'services/cart.html', {'services': services_with_rates})




def home_redirect(request):
    return render(request, 'services/base_generic.html')




def service_list(request):
    services = Service.objects.all()
    return render(request, 'services/service_list.html', {'services': services})




@login_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.added_by = request.user
            service.modified_by = request.user
            service.save()
            return redirect('service_list')
    else:
        form = ServiceForm()
    return render(request, 'services/service_form.html', {'form': form})





def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'services/service_form.html', {'form': form})





def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        return redirect('service_list')
    return render(request, 'services/service_confirm_delete.html', {'service': service})





def service_rate_list(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    rates = service.rates.all()
    return render(request, 'services/service_rate_list.html', {'service': service, 'rates': rates})





def service_rate_create(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        form = ServiceRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.service = service
            rate.save()
            return redirect('service_rate_list', service_id=service_id)
    else:
        form = ServiceRateForm()
    return render(request, 'services/service_rate_form.html', {'form': form, 'service': service})





def service_rate_update(request, service_id, pk):
    rate = get_object_or_404(ServiceRate, service_id=service_id, pk=pk)
    if request.method == 'POST':
        form = ServiceRateForm(request.POST, instance=rate)
        if form.is_valid():
            form.save()
            return redirect('service_rate_list', service_id=service_id)
    else:
        form = ServiceRateForm(instance=rate)
    return render(request, 'services/service_rate_form.html', {'form': form, 'service': rate.service})





def service_rate_delete(request, service_id, pk):
    rate = get_object_or_404(ServiceRate, service_id=service_id, pk=pk)
    if request.method == 'POST':
        rate.delete()
        return redirect('service_rate_list', service_id=service_id)
    return render(request, 'services/service_rate_confirm_delete.html', {'rate': rate})


################################## All the Views for the Multiform ############################################
# --------------------------------------------Himanshu--------------------------------------------------------#

# Some extra view functions to handle different redirections.

def registration_pending(request, pk):
    personal_info = get_object_or_404(PersonalInformation, pk=pk)
    context = {
        'personal_info': personal_info,
    }
    return render(request, 'pending.html', context)

@login_required
def dashboard(request):
    user = request.user
    groups = user.groups.values_list('name', flat=True)
    context = {
        'user': user,
        'groups': groups,
    }
    return render(request, 'dashboard.html', context)



@login_required
def supercoordinator_dashboard(request):
    # Logic specific to supercoordinator dashboard
    return render(request, 'supercoordinator_dashboard.html')

@login_required
def multiform_coordinator_dashboard(request):
    # Logic specific to coordinator dashboard
    return render(request, 'coordinator.html')

# End of extra view functions.

# This below view is for handling the logic of the callback page and redirecting it to a submission page.
def callback_form_view(request):
    if request.method == 'POST':
        form = CallbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('callback_complete')
    else:
        form = CallbackForm()
    return render(request, 'callback_form.html', {'form': form})

def callback_complete_view(request):
    return render(request, 'callback_complete.html')

def work(request):
    return render(request, 'work.html')

def index(request):
    return render(request, 'multiform.html')

# The below view is form showing the callback form on the coordinator's dashboard.
# (Don't get confused in the above and below view.)

# def view_callback_form(request):
#     user_id = request.GET.get('user_id')
#     try:
#         personal_information = PersonalInformation.objects.get(id=user_id)
#         callback_form = Callback.objects.get(personal_information=personal_information)
#         data = {
#             'callback_form': {
#                 'name': callback_form.name,
#                 'phone_number': callback_form.phone_number,
#                 'email': callback_form.email,
#                 'qualification': callback_form.qualification,
#                 'experience': callback_form.experience,
#                 'ctcheckbox': callback_form.ctcheckbox,
#                 'mricheckbox': callback_form.mricheckbox,
#                 'xraycheckbox': callback_form.xraycheckbox,
#                 'mammographycheckbox': callback_form.mammographycheckbox,
#             }
#         }
#     except (PersonalInformation.DoesNotExist, Callback.DoesNotExist):
#         data = {
#             'callback_form': None
#         }
#     return JsonResponse(data)

def view_callback_form(request, pk):
    # Retrieve the Callback object based on pk
    callback_details = get_object_or_404(Callback, pk=pk)

    # Prepare data to send back as JSON response
    response_data = {
        'callback_details': {
            'name': callback_details.name,
            'phone_number': callback_details.phone_number,
            'email': callback_details.email,
            'qualification': callback_details.qualification,
            'experience': callback_details.experience,
            'ctcheckbox': callback_details.ctcheckbox,
            'mricheckbox': callback_details.mricheckbox,
            'xraycheckbox': callback_details.xraycheckbox,
            'mammographycheckbox': callback_details.mammographycheckbox,
        }
    }

    return JsonResponse(response_data)

# The logic to handle the coordinator page.

@login_required
def coordinator(request):
    personal_info = PersonalInformation.objects.all().order_by('-pk')
    callback_details = Callback.objects.all().order_by('-pk')
    # Check if the user belongs to the 'supercoordinator' group
    is_supercoordinator = request.user.groups.filter(name='supercoordinator').exists()
    for info in personal_info:
        try:
            rate_list = RateList.objects.get(radiologist=info)
            info.rate_list_status = rate_list.status
        except RateList.DoesNotExist:
            info.rate_list_status = 'No Status Yet'

    # Print callback_details for debugging
    # print("Callback Details:")
    # for callback in callback_details:
    # print(f"Name: {callback.name}, Email: {callback.email}, Phone Number: {callback.phone_number}")
    
    context = {
        'personal_info': personal_info,
        'is_supercoordinator': is_supercoordinator,
        'callback_details': callback_details,
    }
    return render(request, 'coordinator.html', context)     

# End of the coordinator logic.

@csrf_exempt
def check_email_existence(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print('Email received:', email)  # Debugging log
        if email:
            exists_in_personal_info = PersonalInformation.objects.filter(email=email).exists()
            exists_in_users = User.objects.filter(email=email).exists()
            exists = exists_in_personal_info or exists_in_users
            return JsonResponse({'exists': exists})
    return JsonResponse({'exists': False})

def step1(request):
    if request.method == 'POST':
        request.session['first_name'] = request.POST.get('first_name', '')
        request.session['last_name'] = request.POST.get('last_name', '')
        request.session['email'] = request.POST.get('email', '')
        request.session['password'] = request.POST.get('password', '')
        request.session['cnfpassword'] = request.POST.get('cnfpassword', '')
        request.session['address'] = request.POST.get('address', '')
        request.session['contact_no'] = request.POST.get('contact_no', '')
        request.session['experience_years'] = request.POST.get('experience_years', '')
        request.session['resume'] = request.FILES.get('resume', '')
        request.session['photo'] = request.FILES.get('photo', '')
        return redirect('step2')
    return render(request, 'step1.html')

def step2(request):
    if request.method == 'POST':
        request.session['tenthname'] = request.POST.get('tenthname', '')
        request.session['tenthgrade'] = request.POST.get('tenthgrade', '')
        request.session['tenthpsyr'] = request.POST.get('tenthpsyr', '')
        request.session['tenthcertificate'] = request.FILES.get('tenthcertificate', '')
        request.session['twelthname'] = request.POST.get('twelthname', '')
        request.session['twelthgrade'] = request.POST.get('twelthgrade', '')
        request.session['twelthpsyr'] = request.POST.get('twelthpsyr', '')
        request.session['twelthcertificate'] = request.FILES.get('twelthcertificate', '')
        request.session['mbbsinstitution'] = request.POST.get('mbbsinstitution', '')
        request.session['mbbsgrade'] = request.POST.get('mbbsgrade', '')
        request.session['mbbspsyr'] = request.POST.get('mbbspsyr', '')
        request.session['mbbsmarksheet'] = request.FILES.get('mbbsmarksheet', '')
        request.session['mbbsdegree'] = request.FILES.get('mbbsdegree', '')
        request.session['mdinstitution'] = request.POST.get('mdinstitution', '')
        request.session['mdgrade'] = request.POST.get('mdgrade', '')
        request.session['mdpsyr'] = request.POST.get('mdpsyr', '')
        request.session['mdmarksheet'] = request.FILES.get('mdmarksheet', '')
        request.session['mddegree'] = request.FILES.get('mddegree', '')
        request.session['regno'] = request.POST.get('regno', '')
        request.session['regfile'] = request.FILES.get('regfile', '')
        request.session['videofile'] = request.FILES.get('videofile', '')
        return redirect('step3')
    return render(request, 'step2.html')

def step3(request):
    if request.method == 'POST':
        request.session['exinstitution1'] = request.POST.get('exinstitution1', '')
        request.session['exstdate1'] = request.POST.get('exstdate1', '')
        request.session['exenddate1'] = request.POST.get('exenddate1', '')
        request.session['exinstitution2'] = request.POST.get('exinstitution2', '')
        request.session['exstdate2'] = request.POST.get('exstdate2', '')
        request.session['exenddate2'] = request.POST.get('exenddate2', '')
        request.session['exinstitution3'] = request.POST.get('exinstitution3', '')
        request.session['exstdate3'] = request.POST.get('exstdate3', '')
        request.session['exenddate3'] = request.POST.get('exenddate3', '')
        return redirect('step4')
    return render(request, 'step3.html')

def step4(request):
    if request.method == 'POST':
        request.session['award1'] = request.POST.get('award1', '')
        request.session['awarddate1'] = request.POST.get('awarddate1', '')
        request.session['award2'] = request.POST.get('award2', '')
        request.session['awarddate2'] = request.POST.get('awarddate2', '')
        request.session['award3'] = request.POST.get('award3', '')
        request.session['awarddate3'] = request.POST.get('awarddate3', '')
        request.session['award4'] = request.POST.get('award4', '')
        request.session['awarddate4'] = request.POST.get('awarddate4', '')
        request.session['award5'] = request.POST.get('award5', '')
        request.session['awarddate5'] = request.POST.get('awarddate5', '')
        request.session['publishlink'] = request.POST.get('publishlink', '')
        return redirect('step5')
    return render(request, 'step4.html')

def step5(request):
    if request.method == 'POST':
        request.session['accholdername'] = request.POST.get('accholdername', '')
        request.session['bankname'] = request.POST.get('bankname', '')
        request.session['branchname'] = request.POST.get('branchname', '')
        request.session['acnumber'] = request.POST.get('acnumber', '')
        request.session['ifsc'] = request.POST.get('ifsc', '')
        request.session['pancardno'] = request.POST.get('pancardno', '')
        request.session['aadharcardno'] = request.POST.get('aadharcardno', '')
        request.session['pancard'] = request.FILES.get('pancard', '')
        request.session['aadharcard'] = request.FILES.get('aadharcard', '')
        request.session['cheque'] = request.FILES.get('cheque', '')
        return redirect('step6')
    return render(request, 'step5.html')

def step6(request):
    if request.method == 'POST':
        request.session['mriopt'] = request.POST.get('mriopt', '')
        request.session['mriothers'] = request.POST.get('mriothers', '')
        request.session['ctopt'] = request.POST.get('ctopt', '')
        request.session['ctothers'] = request.POST.get('ctothers', '')
        request.session['xray'] = request.POST.get('xray', '')
        request.session['others'] = request.POST.get('others', '')
        return redirect('step7')
    return render(request, 'step6.html')

def step7(request):
    if request.method == 'POST':
        request.session['monday'] = request.POST.get('monday', '')
        request.session['tuesday'] = request.POST.get('tuesday', '')
        request.session['wednesday'] = request.POST.get('wednesday', '')
        request.session['thursday'] = request.POST.get('thursday', '')
        request.session['friday'] = request.POST.get('friday', '')
        request.session['saturday'] = request.POST.get('saturday', '')
        request.session['sunday'] = request.POST.get('sunday', '')
        request.session['starttime1'] = request.POST.get('starttime1', '')
        request.session['endtime1'] = request.POST.get('endtime1', '')
        request.session['starttime2'] = request.POST.get('starttime2', '')
        request.session['endtime2'] = request.POST.get('endtime2', '')
        request.session['starttime3'] = request.POST.get('starttime3', '')
        request.session['endtime3'] = request.POST.get('endtime3', '')
        request.session['starttime4'] = request.POST.get('starttime4', '')
        request.session['endtime4'] = request.POST.get('endtime4', '')
        return redirect('submit')
    return render(request, 'step7.html')

def submit(request):
    if request.method == 'POST':
        print("before saving..")
        try:

            # Extract and format date fields
            tenthpsyr = parse_date(request.POST.get('tenthpsyr', ''))
            twelthpsyr = parse_date(request.POST.get('twelthpsyr', ''))
            mbbspsyr = parse_date(request.POST.get('mbbspsyr', ''))
            mdpsyr = parse_date(request.POST.get('mdpsyr', ''))
            awarddate1 = parsing_date(request.POST.get('awarddate1', ''))
            awarddate2 = parsing_date(request.POST.get('awarddate2', ''))
            awarddate3 = parsing_date(request.POST.get('awarddate3', ''))
            awarddate4 = parsing_date(request.POST.get('awarddate4', ''))
            awarddate5 = parsing_date(request.POST.get('awarddate5', ''))

           # Helper function to get a list of selected options' names
            def get_selected_options_names(field_name):
                options = request.POST.getlist(field_name)
                return options




             # Create or update PersonalInformation instance
            email = request.POST.get('email', '')
            if 'update_existing' in request.POST:
                user = User.objects.get(email=email)
                personal_info = user.personalinformation
                # Update personal_info fields here if needed
            else:
                personal_info = PersonalInformation.objects.create(
                    first_name=request.POST.get('first_name', ''),
                    last_name=request.POST.get('last_name', ''),
                    email=email,
                    password=request.POST.get('password', ''),
                    cnfpassword=request.POST.get('cnfpassword', ''),
                    address=request.POST.get('address', ''),
                    contact_no=request.POST.get('contact_no', ''),
                    experience_years=int(request.POST.get('experience_years', 0)),
                    resume=request.FILES.get('resume', ''),
                    photo=request.FILES.get('photo', '')
                )

            # Create EducationalDetails instance
            educational_info = EducationalDetails.objects.create(
                tenthname=request.POST.get('tenthname', ''),
                tenthgrade=request.POST.get('tenthgrade', ''),
                tenthpsyr=tenthpsyr,
                tenthcertificate=request.FILES.get('tenthcertificate', ''),
                twelthname=request.POST.get('twelthname', ''),
                twelthgrade=request.POST.get('twelthgrade', ''),
                twelthpsyr=twelthpsyr,
                twelthcertificate=request.FILES.get('twelthcertificate', ''),
                mbbsinstitution=request.POST.get('mbbsinstitution', ''),
                mbbsgrade=request.POST.get('mbbsgrade', ''),
                mbbspsyr=mbbspsyr,
                mbbsmarksheet=request.FILES.get('mbbsmarksheet', ''),
                mbbsdegree=request.FILES.get('mbbsdegree', ''),
                mdinstitution=request.POST.get('mdinstitution', ''),
                mdgrade=request.POST.get('mdgrade', ''),
                mdpsyr=mdpsyr,
                mdmarksheet=request.FILES.get('mdmarksheet', ''),
                mddegree=request.FILES.get('mddegree', ''),
                regno=request.POST.get('regno', ''),
                regfile=request.FILES.get('regfile', ''),
                videofile=request.FILES.get('videofile', ''),
                personal_information=personal_info
            )

            # Create ExperienceDetails instance
            experience_info = ExperienceDetails.objects.create(
                exinstitution1=request.POST.get('exinstitution1', ''),
                exstdate1=parsing_date(request.POST.get('exstdate1', '')),
                exenddate1=parsing_date(request.POST.get('exenddate1', '')),
                exinstitution2=request.POST.get('exinstitution2', ''),
                exstdate2=parsing_date(request.POST.get('exstdate2', '')),
                exenddate2=parsing_date(request.POST.get('exenddate2', '')),
                exinstitution3=request.POST.get('exinstitution3', ''),
                exstdate3=parsing_date(request.POST.get('exstdate3', '')),
                exenddate3=parsing_date(request.POST.get('exenddate3', '')),
                exinstitution4=request.POST.get('exinstitution4', ''),
                exstdate4=parsing_date(request.POST.get('exstdate4', '')),
                exenddate4=parsing_date(request.POST.get('exenddate4', '')),
                exinstitution5=request.POST.get('exinstitution5', ''),
                exstdate5=parsing_date(request.POST.get('exstdate5', '')),
                exenddate5=parsing_date(request.POST.get('exenddate5', '')),
                personal_information=personal_info
            )

            # Create AchievementDetails instance
            achievement_info = AchievementDetails.objects.create(
                award1=request.POST.get('award1', ''),
                awarddate1=awarddate1,
                award2=request.POST.get('award2', ''),
                awarddate2=awarddate2,
                award3=request.POST.get('award3', ''),
                awarddate3=awarddate3,
                award4=request.POST.get('award4', ''),
                awarddate4=awarddate4,
                award5=request.POST.get('award5', ''),
                awarddate5=awarddate5,
                publishlink=request.POST.get('publishlink', ''),
                personal_information=personal_info
            )

            # Create BankingDetails instance
            banking_info = BankingDetails.objects.create(
                accholdername=request.POST.get('accholdername', ''),
                bankname=request.POST.get('bankname', ''),
                branchname=request.POST.get('branchname', ''),
                acnumber=request.POST.get('acnumber', ''),
                ifsc=request.POST.get('ifsc', ''),
                pancardno=request.POST.get('pancardno', ''),
                aadharcardno=request.POST.get('aadharcardno', ''),
                pancard=request.FILES.get('pancard', ''),
                aadharcard=request.FILES.get('aadharcard', ''),
                cheque=request.FILES.get('cheque', ''),
                personal_information=personal_info
            )

            # Helper function to convert boolean to "Yes" or "No"
            def bool_to_yes_no(value):
                return 'Yes' if value else 'No'

            # Create AvailabilityDetails instance
            availability_info = AvailabilityDetails.objects.create(
                monday=bool(request.POST.get('monday', False)),
                tuesday=bool(request.POST.get('tuesday', False)),
                wednesday=bool(request.POST.get('wednesday', False)),
                thursday=bool(request.POST.get('thursday', False)),
                friday=bool(request.POST.get('friday', False)),
                saturday=bool(request.POST.get('saturday', False)),
                sunday=bool(request.POST.get('sunday', False)),
                starttime1=request.POST.get('starttime1', ''),
                endtime1=request.POST.get('endtime1', ''),
                starttime2=request.POST.get('starttime2', ''),
                endtime2=request.POST.get('endtime2', ''),
                starttime3=request.POST.get('starttime3', ''),
                endtime3=request.POST.get('endtime3', ''),
                starttime4=request.POST.get('starttime4', ''),
                endtime4=request.POST.get('endtime4', ''),
                personal_information=personal_info
            )

            # Create ReportingAreaDetails instance
            reporting_area_info = ReportingAreaDetails.objects.create(
                mriopt=', '.join(get_selected_options_names('mriopt')),
                mriothers=request.POST.get('mriothers', ''),
                ctopt=', '.join(get_selected_options_names('ctopt')),
                ctothers=request.POST.get('ctothers', ''),
                xray=bool(request.POST.get('xray', False)),
                others=bool(request.POST.get('others', False)),
                otherText=request.POST.get('otherText', ''),
                personal_information=personal_info
            )

            print("saving rate list...")
            # Create Rate List Instance 
            rate_list = RateList.objects.create(
                mri1=int(request.POST.get('mri1', 200)),
                mri2=int(request.POST.get('mri2', 100)),
                mri3=int(request.POST.get('mri3', 250)),
                mri4=int(request.POST.get('mri4', 250)),
                mri5=int(request.POST.get('mri5', 300)),
                mri6=int(request.POST.get('mri6', 300)),
                ct1=int(request.POST.get('ct1', 150)),
                ct2=int(request.POST.get('ct2', 150)),
                ct3=int(request.POST.get('ct3', 150)),
                ct4=int(request.POST.get('ct4', 200)),
                ct5=int(request.POST.get('ct5', 225)),
                ct6=int(request.POST.get('ct6', 200)),
                ct7=int(request.POST.get('ct7', 500)),
                xray1=int(request.POST.get('xray1', 20)),
                xray2=int(request.POST.get('xray2', 75)),
                radiologist=personal_info
            )
            


            # Continue creating other model instances as needed

        except Exception as e:
            return HttpResponse(f"An error occurred: {e}")

        # Clear session data after successful submission
        request.session.flush()

        # return HttpResponse("Data saved successfully.")
        return redirect('success', pk=personal_info.pk)

    return render(request, 'submit.html')

# View function to redirect to the success page.
def success(request, pk):
    personal_info = get_object_or_404(PersonalInformation, pk=pk)
    
    context = {
        'first_name': personal_info.first_name,
        'last_name': personal_info.last_name,
        'personal_info': personal_info,
        'personal_info_pk': personal_info.pk,  # Pass the personal_info pk for linking back
    }
    return render(request, 'success.html', context)

# This is the view for the rate list .
def rate_list(request, radiologist_id):
    radiologist = get_object_or_404(PersonalInformation, pk=radiologist_id)
    # personal_info = get_object_or_404(PersonalInformation, pk=pk)
    rate_list = get_object_or_404(RateList, radiologist=radiologist)
    return render(request, 'rate_list.html', {'rate_list': rate_list, 'radiologist': radiologist})

# views.py
def view_rate_list_form(request, radiologist_id):
    try:
        radiologist = PersonalInformation.objects.get(pk=radiologist_id)
        rate_list = RateList.objects.get(radiologist=radiologist)
        rate_list_data = {
            'mri1': rate_list.mri1,
            'mri2': rate_list.mri2,
            'mri3': rate_list.mri3,
            'mri4': rate_list.mri4,
            'mri5': rate_list.mri5,
            'mri6': rate_list.mri6,
            'ct1': rate_list.ct1,
            'ct2': rate_list.ct2,
            'ct3': rate_list.ct3,
            'ct4': rate_list.ct4,
            'ct5': rate_list.ct5,
            'ct6': rate_list.ct6,
            'ct7': rate_list.ct7,
            'xray1': rate_list.xray1,
            'xray2': rate_list.xray2
        }
        return JsonResponse({'rate_list': rate_list_data})
    except RateList.DoesNotExist:
        return JsonResponse({'error': 'RateList not found'}, status=404)
    except PersonalInformation.DoesNotExist:
        return JsonResponse({'error': 'Radiologist not found'}, status=404)


@csrf_exempt
def update_rate_list(request, radiologist_id):
    if request.method == 'POST':
        try:
            radiologist = PersonalInformation.objects.get(pk=radiologist_id)
            rate_list = RateList.objects.get(radiologist=radiologist)
            for field in ['mri1', 'mri2', 'mri3', 'mri4', 'mri5', 'mri6', 'ct1', 'ct2', 'ct3', 'ct4', 'ct5', 'ct6', 'ct7', 'xray1', 'xray2']:
                value = request.POST.get(field)
                if value is not None:
                    setattr(rate_list, field, value)
            rate_list.save()
            return JsonResponse({'success': True})
        except RateList.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'RateList not found'}, status=404)
        except PersonalInformation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Radiologist not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


def update_status_rate_list(request):
    if request.method == 'POST':
        rate_list_id = request.POST.get('rate_list_id')
        status = request.POST.get('status')
        try:
            rate_list = RateList.objects.get(pk=rate_list_id)
            rate_list.status = status
            rate_list.save()
            return JsonResponse({'success': True})
        except RateList.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'RateList not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


# View function to render the view response on the success page.
def view_response(request, pk):
    # Replace 1 with the appropriate ID of the saved form data
    personal_info = get_object_or_404(PersonalInformation, pk=pk)
    educational_info = get_object_or_404(EducationalDetails, personal_information=personal_info)
    experience_info = get_object_or_404(ExperienceDetails, personal_information=personal_info)
    achievement_info = get_object_or_404(AchievementDetails, personal_information=personal_info)
    banking_info = get_object_or_404(BankingDetails, personal_information=personal_info)
    availability_info = get_object_or_404(AvailabilityDetails, personal_information=personal_info)
    reporting_area_info = get_object_or_404(ReportingAreaDetails, personal_information=personal_info)

    context = {
        'personal_info': personal_info,
        'educational_info': educational_info,
        'experience_info': experience_info,
        'achievement_info': achievement_info,
        'banking_info': banking_info,
        'availability_info': availability_info,
        'reporting_area_info': reporting_area_info
    }

    return render(request, 'view_response.html', context)

def parse_date(date_string):
    if date_string:
        try:
            return datetime.strptime(date_string + '-01', '%Y-%m-%d')
        except ValueError:
            # Handle invalid date format here
            return None
    return None

def parsing_date(date_string):
    if date_string:
        try:
            return datetime.strptime(date_string , '%Y-%m-%d')
        except ValueError:
            # Handle invalid date format here
            return None
    return None

@require_POST
@csrf_exempt
def update_stage1status(request, pk):
    try:
        data = PersonalInformation.objects.get(pk=pk)
        stage1status = request.POST.get('stage1status')
        data.stage1status = stage1status
        data.save()
        return JsonResponse({'status': 'success'})
    except PersonalInformation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)

@require_POST
@csrf_exempt
def update_stage2status(request, pk):
    try:
        data = PersonalInformation.objects.get(pk=pk)
        stage2status = request.POST.get('stage2status')
        data.stage2status = stage2status
        data.save()
        return JsonResponse({'status': 'success'})
    except PersonalInformation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Data not found'}, status=404)
# def register_user(request):
#     if request.method == 'POST':
#         # Process form data to create a new user
#         # Example: Assuming form data is POSTed to this view
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         email = request.POST.get('email')
#         # Fetch other necessary fields

#         # Check if user already exists based on email or other unique identifier
#         # Example: Check if user with email already exists
#         if PersonalInformation.objects.filter(email=email).exists():
#             return redirect('/registration_error/')  # Redirect to error page if user already exists

#         # Assuming status is 'under_progress' by default for new registrations
#         new_user = PersonalInformation.objects.create(
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             # Populate other fields as needed
#             status='under_progress'  # Default status for new registrations
#         )

#         # Redirect logic based on status
#         if new_user.status == 'under_progress':
#             return redirect('/registration_pending/')  # Redirect to pending registration page

#         return redirect('/registration_success/')  # Redirect to success page after registration

#     return render(request, 'registration_form.html')
@login_required
def view_complete_form(request, pk):
    try:
        # Fetch all related model instances using the primary key
        personal_information = get_object_or_404(PersonalInformation, pk=pk)
        educational_info = get_object_or_404(EducationalDetails, personal_information=personal_information)
        experience_info = get_object_or_404(ExperienceDetails, personal_information=personal_information)
        achievement_info = get_object_or_404(AchievementDetails, personal_information=personal_information)
        banking_info = get_object_or_404(BankingDetails, personal_information=personal_information)
        reporting_area_info = get_object_or_404(ReportingAreaDetails, personal_information=personal_information)
        availability_info = get_object_or_404(AvailabilityDetails, personal_information=personal_information)

        # pdf_url = generate_pdf(personal_information, educational_info, experience_info, achievement_info, banking_info, reporting_area_info, availability_info)

        # Constructing the response data as JSON
        response = {
            'personal_information': {
                'first_name': personal_information.first_name,
                'last_name': personal_information.last_name,
                'email': personal_information.email,
                'password': personal_information.password,
                'address': personal_information.address,
                'contact_no': personal_information.contact_no,
                'resume': request.build_absolute_uri(personal_information.resume.url) if personal_information.resume else None,
                'photo': request.build_absolute_uri(personal_information.photo.url) if personal_information.photo else None,
                'experience_years': personal_information.experience_years,
                # Add more fields as needed
            },
            'educational_info': {
                'tenthname': educational_info.tenthname,
                'tenthgrade': educational_info.tenthgrade,
                'tenthpsyr': educational_info.tenthpsyr,
                'tenthcertificate': request.build_absolute_uri(educational_info.tenthcertificate.url) if educational_info.tenthcertificate else None,
                'twelthname': educational_info.twelthname,
                'twelthgrade': educational_info.twelthgrade,
                'twelthpsyr': educational_info.twelthpsyr,
                'twelthcertificate': request.build_absolute_uri(educational_info.twelthcertificate.url) if educational_info.twelthcertificate else None,
                'mbbsinstitution': educational_info.mbbsinstitution,
                'mbbsgrade': educational_info.mbbsgrade,
                'mbbspsyr': educational_info.mbbspsyr,
                'mbbsmarksheet': request.build_absolute_uri(educational_info.mbbsmarksheet.url) if educational_info.mbbsmarksheet else None,
                'mbbsdegree': request.build_absolute_uri(educational_info.mbbsdegree.url) if educational_info.mbbsdegree else None,
                'mdinstitution': educational_info.mdinstitution,
                'mdgrade': educational_info.mdgrade,
                'mdpsyr': educational_info.mdpsyr,
                'mdmarksheet': request.build_absolute_uri(educational_info.mdmarksheet.url) if educational_info.mdmarksheet else None,
                'mddegree': request.build_absolute_uri(educational_info.mddegree.url) if educational_info.mddegree else None,
                'regno' : educational_info.regno,
                'regfile' : request.build_absolute_uri(educational_info.regfile.url) if educational_info.regfile else None,
                'videofile': request.build_absolute_uri(educational_info.videofile.url) if educational_info.videofile else None,
                # Add more fields as needed
            },
            'experience_info': {
                'exinstitution1': experience_info.exinstitution1,
                'exstdate1': experience_info.exstdate1,
                'exenddate1': experience_info.exenddate1,
                'exinstitution2': experience_info.exinstitution2,
                'exstdate2': experience_info.exstdate2,
                'exenddate2': experience_info.exenddate2,
                'exinstitution3': experience_info.exinstitution3,
                'exstdate3': experience_info.exstdate3,
                'exenddate3': experience_info.exenddate3,
                'exinstitution4': experience_info.exinstitution4,
                'exstdate4': experience_info.exstdate4,
                'exenddate4': experience_info.exenddate4,
                'exinstitution5': experience_info.exinstitution5,
                'exstdate5': experience_info.exstdate5,
                'exenddate5': experience_info.exenddate5,
                # Add more fields as needed
            },
            'achievement_info': {
                'award1': achievement_info.award1,
                'awarddate1': achievement_info.awarddate1,
                'award2': achievement_info.award2,
                'awarddate2': achievement_info.awarddate2,
                'award3': achievement_info.award3,
                'awarddate3': achievement_info.awarddate3,
                'award4': achievement_info.award4,
                'awarddate4': achievement_info.awarddate4,
                'award5': achievement_info.award5,
                'awarddate5': achievement_info.awarddate5,
                'publishlink': achievement_info.publishlink,
                # Add more fields as needed
            },
            'banking_info': {
                'accholdername': banking_info.accholdername,
                'bankname': banking_info.bankname,
                'branchname': banking_info.branchname,
                'acnumber': banking_info.acnumber,
                'ifsc': banking_info.ifsc,
                'pancardno': banking_info.pancardno,
                'aadharcardno': banking_info.aadharcardno,
                'pancard': request.build_absolute_uri(banking_info.pancard.url) if banking_info.pancard else None,
                'aadharcard': request.build_absolute_uri(banking_info.aadharcard.url) if banking_info.aadharcard else None,
                'cheque': request.build_absolute_uri(banking_info.cheque.url) if banking_info.cheque else None,
                # Add more fields as needed
            },
            'reporting_area_info': {
                'mriopt': reporting_area_info.mriopt,
                'mriothers': reporting_area_info.mriothers,
                'ctopt': reporting_area_info.ctopt,
                'ctothers': reporting_area_info.ctothers,
                'xray': reporting_area_info.xray,
                'others': reporting_area_info.others,
                'otherText': reporting_area_info.otherText,
                # Add more fields as needed
            },
            'availability_info': {
                'monday': availability_info.monday,
                'tuesday': availability_info.tuesday,
                'wednesday': availability_info.wednesday,
                'thursday': availability_info.thursday,
                'friday': availability_info.friday,
                'saturday': availability_info.saturday,
                'sunday': availability_info.sunday,
                'starttime1': availability_info.starttime1,
                'endtime1': availability_info.endtime1,
                'starttime2': availability_info.starttime2,
                'endtime2': availability_info.endtime2,
                'starttime3': availability_info.starttime3,
                'endtime3': availability_info.endtime3,
                'starttime4': availability_info.starttime4,
                'endtime4': availability_info.endtime4,
                # Add more fields as needed
            },
            # "pdf_url": pdf_url,  # Add the PDF URL to the response
        }

        logging.info(f"Successfully fetched complete form data for PK={pk}")
        return JsonResponse(response)

    except ObjectDoesNotExist as e:
        error_message = f"Object does not exist: {str(e)}"
        logging.error(error_message)
        return JsonResponse({'error': error_message}, status=404)

    except Exception as e:
        error_message = f"Error fetching complete form data: {str(e)}"
        logging.error(error_message)
        return JsonResponse({'error': error_message}, status=500)

@csrf_exempt
def update_messages(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        coordinator_message = request.POST.get('coordinator_message')
        supercoordinator_message = request.POST.get('supercoordinator_message')
        stage1status = request.POST.get('stage1status')
        stage2status = request.POST.get('stage2status')

        try:
            data = PersonalInformation.objects.get(pk=pk)
            if coordinator_message is not None:
                data.coordinator_message = coordinator_message
            if supercoordinator_message is not None:
                data.supercoordinator_message = supercoordinator_message
            if stage1status is not None:
                data.stage1status = stage1status
            if stage2status is not None:
                data.stage2status = stage2status
            data.save()
            return JsonResponse({'status': 'success'})
        except PersonalInformation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Data not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# This is the view to generate the pdf of the responses.

# def generate_response_pdf(request, pk):
#     personal_info = PersonalInformation.objects.get(pk=pk)
#     educational_info = EducationalDetails.objects.get(pk=pk)
#     experience_info = ExperienceDetails.objects.get(pk=pk)
#     achievement_info = AchievementDetails.objects.get(pk=pk)
#     banking_info = BankingDetails.objects.get(pk=pk)
#     reporting_info = ReportingAreaDetails.objects.get(pk=pk)
#     availability_info = AvailabilityDetails.objects.get(pk=pk)

#     html_string = render_to_string('response_pdf.html', {
#         'personal_information': personal_info,
#         'educational_info': educational_info,
#         'experience_info': experience_info,
#         'achievement_info': achievement_info,
#         'banking_info': banking_info,
#         'reporting_info': reporting_info,
#         'availability_info': availability_info,
#     })

#     html = weasyprint.HTML(string=html_string)
#     pdf = html.write_pdf()

#     response = HttpResponse(pdf, content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="response.pdf"'
#     return response

# def generate_pdf(request, pk):
#     if request.method == 'POST':
#         try:
#             personal_information = get_object_or_404(PersonalInformation, pk=pk)
#             educational_info = EducationalDetails.objects.filter(personal_information=personal_information).first()
#             experience_info = ExperienceDetails.objects.filter(personal_information=personal_information).first()
#             achievement_info = AchievementDetails.objects.filter(personal_information=personal_information).first()
#             banking_info = BankingDetails.objects.filter(personal_information=personal_information).first()
#             reporting_area_info = ReportingAreaDetails.objects.filter(personal_information=personal_information).first()
#             availability_info = AvailabilityDetails.objects.filter(personal_information=personal_information).first()

#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename="form_data_{pk}.pdf"'
            
#             doc = SimpleDocTemplate(response, pagesize=letter)
#             styles = getSampleStyleSheet()
#             elements = []

#             def add_paragraph(elements, text, style=styles['Normal']):
#                 elements.append(Paragraph(text, style))

#             # Personal Information
#             add_paragraph(elements, "Personal Information:", styles['Heading1'])
#             add_paragraph(elements, f"First Name: {personal_information.first_name or 'N/A'}")
#             add_paragraph(elements, f"Last Name: {personal_information.last_name or 'N/A'}")
#             add_paragraph(elements, f"Email: {personal_information.email or 'N/A'}")
#             add_paragraph(elements, f"Password: {personal_information.password or 'N/A'}")
#             add_paragraph(elements, f"Address: {personal_information.address or 'N/A'}")
#             add_paragraph(elements, f"Contact No.: {personal_information.contact_no or 'N/A'}")
#             add_paragraph(elements, f"Resume: {personal_information.resume.url if personal_information.resume else 'No Resume Uploaded'}")
#             add_paragraph(elements, f"Photo: {personal_information.photo.url if personal_information.photo else 'No Photo Uploaded'}")
#             add_paragraph(elements, f"Experience Years: {personal_information.experience_years or 'N/A'}")

#             # Educational Details
#             if educational_info:
#                 add_paragraph(elements, "Educational Details:", styles['Heading1'])
#                 add_paragraph(elements, f"10th School Name: {educational_info.tenthname or 'N/A'}")
#                 add_paragraph(elements, f"10th Grade: {educational_info.tenthgrade or 'N/A'}")
#                 add_paragraph(elements, f"10th Passing Year: {educational_info.tenthpsyr or 'N/A'}")
#                 add_paragraph(elements, f"10th Certificate: {educational_info.tenthcertificate.url if educational_info.tenthcertificate else 'No Certificate Uploaded'}")
#                 add_paragraph(elements, f"12th School Name: {educational_info.twelthname or 'N/A'}")
#                 add_paragraph(elements, f"12th Grade: {educational_info.twelthgrade or 'N/A'}")
#                 add_paragraph(elements, f"12th Passing Year: {educational_info.twelthpsyr or 'N/A'}")
#                 add_paragraph(elements, f"12th Certificate: {educational_info.twelthcertificate.url if educational_info.twelthcertificate else 'No Certificate Uploaded'}")
#                 add_paragraph(elements, f"MBBS Institution: {educational_info.mbbsinstitution or 'N/A'}")
#                 add_paragraph(elements, f"MBBS Grade: {educational_info.mbbsgrade or 'N/A'}")
#                 add_paragraph(elements, f"MBBS Passing Year: {educational_info.mbbspsyr or 'N/A'}")
#                 add_paragraph(elements, f"MBBS Marksheet: {educational_info.mbbsmarksheet.url if educational_info.mbbsmarksheet else 'No Marksheet Uploaded'}")
#                 add_paragraph(elements, f"MBBS Degree: {educational_info.mbbsdegree.url if educational_info.mbbsdegree else 'No Degree Uploaded'}")
#                 add_paragraph(elements, f"MD Institution: {educational_info.mdinstitution or 'N/A'}")
#                 add_paragraph(elements, f"MD Grade: {educational_info.mdgrade or 'N/A'}")
#                 add_paragraph(elements, f"MD Passing Year: {educational_info.mdpsyr or 'N/A'}")
#                 add_paragraph(elements, f"MD Marksheet: {educational_info.mdmarksheet.url if educational_info.mdmarksheet else 'No Marksheet Uploaded'}")
#                 add_paragraph(elements, f"MD Degree: {educational_info.mddegree.url if educational_info.mddegree else 'No Degree Uploaded'}")
#                 add_paragraph(elements, f"Video File: {educational_info.videofile.url if educational_info.videofile else 'No Video Uploaded'}")
#             else:
#                 add_paragraph(elements, "Educational Details: No educational details available.", styles['Heading1'])

#             # Experience Details
#             if experience_info:
#                 add_paragraph(elements, "Experience Details:", styles['Heading1'])
#                 add_paragraph(elements, f"Experience 1 Institution: {experience_info.exinstitution1 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 1 Starting Date: {experience_info.exstdate1 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 1 Ending Date: {experience_info.exenddate1 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 2 Institution: {experience_info.exinstitution2 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 2 Starting Date: {experience_info.exstdate2 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 2 Ending Date: {experience_info.exenddate2 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 3 Institution: {experience_info.exinstitution3 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 3 Starting Date: {experience_info.exstdate3 or 'N/A'}")
#                 add_paragraph(elements, f"Experience 3 Ending Date: {experience_info.exenddate3 or 'N/A'}")
#             else:
#                 add_paragraph(elements, "Experience Details: No experience details available.", styles['Heading1'])

#             # Achievement Details
#             if achievement_info:
#                 add_paragraph(elements, "Achievement Details:", styles['Heading1'])
#                 add_paragraph(elements, f"Award 1: {achievement_info.award1 or 'N/A'}")
#                 add_paragraph(elements, f"Award Date 1: {achievement_info.awarddate1 or 'N/A'}")
#                 add_paragraph(elements, f"Award 2: {achievement_info.award2 or 'N/A'}")
#                 add_paragraph(elements, f"Award Date 2: {achievement_info.awarddate2 or 'N/A'}")
#                 add_paragraph(elements, f"Publish Link: {achievement_info.publishlink or 'N/A'}")
#             else:
#                 add_paragraph(elements, "Achievement Details: No achievement details available.", styles['Heading1'])

#             # Banking Details
#             if banking_info:
#                 add_paragraph(elements, "Banking Details:", styles['Heading1'])
#                 add_paragraph(elements, f"Account Holder Name: {banking_info.accholdername or 'N/A'}")
#                 add_paragraph(elements, f"Bank Name: {banking_info.bankname or 'N/A'}")
#                 add_paragraph(elements, f"Branch Name: {banking_info.branchname or 'N/A'}")
#                 add_paragraph(elements, f"Account Number: {banking_info.acnumber or 'N/A'}")
#                 add_paragraph(elements, f"IFSC Code: {banking_info.ifsc or 'N/A'}")
#                 add_paragraph(elements, f"Pan Card Number: {banking_info.pancardno or 'N/A'}")
#                 add_paragraph(elements, f"Aadhar Card Number: {banking_info.aadharcardno or 'N/A'}")
#                 add_paragraph(elements, f"Pan Card: {banking_info.pancard or 'No Pan Card Uploaded'}")
#                 add_paragraph(elements, f"Aadhar Card: {banking_info.aadharcard or 'No Aadhar Card Uploaded'}")
#                 add_paragraph(elements, f"Cheque: {banking_info.cheque or 'No Cheque Uploaded'}")
#             else:
#                 add_paragraph(elements, "Banking Details: No banking details available.", styles['Heading1'])

#             # Reporting Area Details
#             if reporting_area_info:
#                 add_paragraph(elements, "Reporting Area Details:", styles['Heading1'])
#                 add_paragraph(elements, f"MRI Option: {reporting_area_info.mriopt or 'N/A'}")
#                 add_paragraph(elements, f"MRI Others: {reporting_area_info.mriothers or 'N/A'}")
#                 add_paragraph(elements, f"CT Options: {reporting_area_info.ctopt or 'N/A'}")
#                 add_paragraph(elements, f"CT Others: {reporting_area_info.ctothers or 'N/A'}")
#                 add_paragraph(elements, f"Xray: {reporting_area_info.xray or 'N/A'}")
#                 add_paragraph(elements, f"Others: {reporting_area_info.others or 'N/A'}")
#                 add_paragraph(elements, f"Others Description: {reporting_area_info.otherText or 'N/A'}")
#             else:
#                 add_paragraph(elements, "Reporting Area Details: No reporting area details available.", styles['Heading1'])

#             # Availability Details
#             if availability_info:
#                 add_paragraph(elements, "Availability Details:", styles['Heading1'])
#                 add_paragraph(elements, f"Monday: {availability_info.monday or 'N/A'}")
#                 add_paragraph(elements, f"Tuesday: {availability_info.tuesday or 'N/A'}")
#                 add_paragraph(elements, f"Wednesday: {availability_info.wednesday or 'N/A'}")
#                 add_paragraph(elements, f"Thursday: {availability_info.thursday or 'N/A'}")
#                 add_paragraph(elements, f"Friday: {availability_info.friday or 'N/A'}")
#                 add_paragraph(elements, f"Saturday: {availability_info.saturday or 'N/A'}")
#                 add_paragraph(elements, f"Sunday: {availability_info.sunday or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 1 (start): {availability_info.starttime1 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 1 (end): {availability_info.endtime1 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 2 (start): {availability_info.starttime2 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 2 (end): {availability_info.endtime2 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 3 (start): {availability_info.starttime3 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 3 (end): {availability_info.endtime3 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 4 (start): {availability_info.starttime4 or 'N/A'}")
#                 add_paragraph(elements, f"Time Slot 4 (end): {availability_info.endtime4 or 'N/A'}")
#             else:
#                 add_paragraph(elements, "Availability Details: No availability details available.", styles['Heading1'])

#             doc.build(elements)
#             return response

#         except ObjectDoesNotExist as e:
#             error_message = f"Object does not exist: {str(e)}"
#             return JsonResponse({'error': error_message}, status=404)

#         except Exception as e:
#             error_message = f"Error generating PDF: {str(e)}"
#             return JsonResponse({'error': error_message}, status=500)
#     else:
#         return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_pdf(request, pk):
    personal_info = get_object_or_404(PersonalInformation, pk=pk)
    educational_info = get_object_or_404(EducationalDetails, personal_information=personal_info)
    experience_info = get_object_or_404(ExperienceDetails, personal_information=personal_info)
    achievement_info = get_object_or_404(AchievementDetails, personal_information=personal_info)
    banking_info = get_object_or_404(BankingDetails, personal_information=personal_info)
    reporting_area_info = get_object_or_404(ReportingAreaDetails, personal_information=personal_info)
    availability_info = get_object_or_404(AvailabilityDetails, personal_information=personal_info)

    response = HttpResponse(content_type='application/pdf')
    filename = f"{personal_info.first_name}_{personal_info.last_name}_form_data_{personal_info.pk}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 80

    # Draw the logo at the top center
    logo_path = 'services/static/image/Logo.png' 
    logo_width = 100  
    logo_height = 30  
    p.drawImage(logo_path, x=(width - logo_width) / 2, y=height - logo_height - 20, width=logo_width, height=logo_height, mask='auto')

    def add_new_page(p, y):
        p.showPage()
        y = height - 40
        return y

    def draw_text(text, data, y, p, indent=100):
        if y < 40:
            y = add_new_page(p, y)
        data_str = str(data) if not isinstance(data, date) else data.strftime('%Y-%m-%d')  # Convert date to string if necessary
        p.drawString(indent, y, text)
        p.drawString(indent + 150, y, ":")
        p.drawString(indent + 170, y, data_str)
        return y - 15
    
    def draw_last_text(text, data, y, p, indent=100):
        if y < 40:
            y = add_new_page(p, y)
        data_str = str(data) if not isinstance(data, date) else data.strftime('%Y-%m-%d')  # Convert date to string if necessary
        p.drawString(indent, y, text)
        p.drawString(indent + 150, y, ":")
        p.drawString(indent + 170, y, data_str)
        return y - 25
    
    def draw_text_heading(text, data, y, p, indent=100):
        if y < 40:
            y = add_new_page(p, y)
        data_str = str(data) if not isinstance(data, date) else data.strftime('%Y-%m-%d')  # Convert date to string if necessary
        p.drawString(indent, y, text)
        p.drawString(indent, y - 7, "------------------------------------------")
        
        return y - 25

    def draw_link(text, url, link_text, y, p, indent=100):
        if y < 40:
            y = add_new_page(p, y)
        text_width = stringWidth(link_text, fontName="Helvetica", fontSize=12)
        p.drawString(indent, y, text)
        p.drawString(indent + 150, y, ":")
        # Debugging print statement to ensure URL is correctly passed
        print(f"Drawing link: {text}, URL: {url}")
        if url:
            p.setFillColor(blue)
            p.drawString(indent + 170, y, link_text)
            p.linkURL(f'{url}#target=_blank', (indent + 170, y, indent + 170 + text_width, y + 10), relative=1, thickness=1, color=blue)
            p.setFillColor(black)  # Reset color to black for other texts
        else:
            p.drawString(indent + 170, y, "N/A")
        return y - 15

    def draw_last_link(text, url, link_text, y, p, indent=100):
        if y < 40:
            y = add_new_page(p, y)
        text_width = stringWidth(link_text, fontName="Helvetica", fontSize=12)
        p.drawString(indent, y, text)
        p.drawString(indent + 150, y, ":")
        # Debugging print statement to ensure URL is correctly passed
        print(f"Drawing link: {text}, URL: {url}")
        if url:
            p.setFillColor(blue)
            p.drawString(indent + 170, y, link_text)
            p.linkURL(f'{url}#target=_blank', (indent + 170, y, indent + 170 + text_width, y + 10), relative=1, thickness=1, color=blue)
            p.setFillColor(black)  # Reset color to black for other texts
        else:
            p.drawString(indent + 170, y, "N/A")
        return y - 25


    # Draw the title at the top of the page
    title = f"Form Details of {personal_info.first_name} {personal_info.last_name}"
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y, title)
    y -= 30  # Adjust the space after the title

    p.setFont("Helvetica", 12)  # Reset font size to normal

    # Draw Personal Information section
    y = draw_text_heading("Personal Information","", y, p)
    y = draw_text("First Name", personal_info.first_name or 'N/A', y, p)
    y = draw_text("Last Name", personal_info.last_name or 'N/A', y, p)
    y = draw_text("Email", personal_info.email or 'N/A', y, p)
    y = draw_text("Password", personal_info.password or 'N/A', y, p)
    y = draw_text("Confirm Password", personal_info.cnfpassword or 'N/A', y, p)
    y = draw_text("Address", personal_info.address or 'N/A', y, p)
    y = draw_text("Contact Number", personal_info.contact_no or 'N/A', y, p)
    y = draw_text("Years of Experience", str(personal_info.experience_years or 'N/A'), y, p)
    if personal_info.resume:
        resume_url = request.build_absolute_uri(personal_info.resume.url) if personal_info.resume else None
        y = draw_link("Resume", resume_url, "View Resume", y, p)
    if personal_info.photo:
        photo_url = request.build_absolute_uri(personal_info.photo.url) if personal_info.photo else None
        y = draw_last_link("Photo", photo_url, "View Photo", y, p)

    # Draw Educational Details section
    y = draw_text_heading("Educational Details","", y, p)
    y = draw_text("Tenth Name", educational_info.tenthname or 'N/A', y, p)
    y = draw_text("Tenth Grade", educational_info.tenthgrade or 'N/A', y, p)
    y = draw_text("Tenth Passing Year", educational_info.tenthpsyr or 'N/A', y, p)
    if educational_info.tenthcertificate:
        tenth_cert_url = request.build_absolute_uri(educational_info.tenthcertificate.url) if educational_info.tenthcertificate else None
        y = draw_link("Tenth Certificate", tenth_cert_url, "View Tenth Certificate", y, p)
    y = draw_text("Twelfth Name", educational_info.twelthname or 'N/A', y, p)
    y = draw_text("Twelfth Grade", educational_info.twelthgrade or 'N/A', y, p)
    y = draw_text("Twelfth Passing Year", educational_info.twelthpsyr or 'N/A', y, p)
    if educational_info.twelthcertificate:
        twelfth_cert_url = request.build_absolute_uri(educational_info.twelthcertificate.url) if educational_info.twelthcertificate else None
        y = draw_link("Twelfth Certificate", twelfth_cert_url, "View Twelfth Certificate", y, p)
    y = draw_text("MBBS Institution", educational_info.mbbsinstitution or 'N/A', y, p)
    y = draw_text("MBBS Grade", educational_info.mbbsgrade or 'N/A', y, p)
    y = draw_text("MBBS Passing Year", educational_info.mbbspsyr or 'N/A', y, p)
    if educational_info.mbbsmarksheet:
        mbbs_marksheet_url = request.build_absolute_uri(educational_info.mbbsmarksheet.url) if educational_info.mbbsmarksheet else None
        y = draw_link("MBBS Marksheets", mbbs_marksheet_url, "View MBBS Marksheets", y, p)
    if educational_info.mbbsdegree:
        mbbs_degree_url = request.build_absolute_uri(educational_info.mbbsdegree.url) if educational_info.mbbsdegree else None
        y = draw_link("MBBS Degree", mbbs_degree_url, "View MBBS Degree", y, p)
    y = draw_text("MD Institution", educational_info.mdinstitution or 'N/A', y, p)
    y = draw_text("MD Grade", educational_info.mdgrade or 'N/A', y, p)
    y = draw_text("MD Passing Year", educational_info.mdpsyr or 'N/A', y, p)
    if educational_info.mdmarksheet:
        md_marksheet_url = request.build_absolute_uri(educational_info.mdmarksheet.url) if educational_info.mdmarksheet else None
        y = draw_link("MD Marksheets", md_marksheet_url, "View MD Marksheets", y, p)
    if educational_info.mddegree:
        md_degree_url = request.build_absolute_uri(educational_info.mddegree.url) if educational_info.mddegree else None
        y = draw_link("MD Degree", md_degree_url, "View MD Degree", y, p)
    y = draw_text("State Registration Number", educational_info.regno or 'N/A', y, p)
    if educational_info.regfile:
        regfile_url = request.build_absolute_uri(educational_info.regfile.url) if educational_info.regfile else None
        y = draw_link("State Registration File", regfile_url, "View Registration File", y, p)
    if educational_info.videofile:
        video_url = request.build_absolute_uri(educational_info.videofile.url) if educational_info.videofile else None
        y = draw_last_link("Video File", video_url, "View Video", y, p)

    # Draw Experience Details section
    y = draw_text_heading("Experience Details","", y, p)
    if experience_info.exinstitution1:
        y = draw_text("Experience Institution", experience_info.exinstitution1 or 'N/A', y, p)
        y = draw_text("Experience Starting Date", experience_info.exstdate1 or 'N/A', y, p)
        y = draw_last_text("Experience Ending Date", experience_info.exenddate1 or 'N/A', y, p)
    if experience_info.exinstitution2:
        y = draw_text("Experience Institution", experience_info.exinstitution2 or 'N/A', y, p)
        y = draw_text("Experience Starting Date", experience_info.exstdate2 or 'N/A', y, p)
        y = draw_last_text("Experience Ending Date", experience_info.exenddate2 or 'N/A', y, p)
    if experience_info.exinstitution3:
        y = draw_text("Experience Institution", experience_info.exinstitution3 or 'N/A', y, p)
        y = draw_text("Experience Starting Date", experience_info.exstdate3 or 'N/A', y, p)
        y = draw_last_text("Experience Ending Date", experience_info.exenddate3 or 'N/A', y, p)
    if experience_info.exinstitution4:
        y = draw_text("Experience Institution", experience_info.exinstitution2 or 'N/A', y, p)
        y = draw_text("Experience Starting Date", experience_info.exstdate2 or 'N/A', y, p)
        y = draw_last_text("Experience Ending Date", experience_info.exenddate2 or 'N/A', y, p)
    if experience_info.exinstitution5:
        y = draw_text("Experience Institution", experience_info.exinstitution3 or 'N/A', y, p)
        y = draw_text("Experience Starting Date", experience_info.exstdate3 or 'N/A', y, p)
        y = draw_last_text("Experience Ending Date", experience_info.exenddate3 or 'N/A', y, p)
    

    # Draw Achievement Details section
    y = draw_text_heading("Achievement Details","", y, p)
    if achievement_info.award1:
        y = draw_text("Award ", achievement_info.award1 or 'N/A', y, p)
        y = draw_last_text("Award Date ", achievement_info.awarddate1 or 'N/A', y, p)
    if achievement_info.award2:
        y = draw_text("Award ", achievement_info.award2 or 'N/A', y, p)
        y = draw_last_text("Award Date ", achievement_info.awarddate2 or 'N/A', y, p)
    if achievement_info.award3:
        y = draw_text("Award ", achievement_info.award1 or 'N/A', y, p)
        y = draw_last_text("Award Date ", achievement_info.awarddate1 or 'N/A', y, p)
    if achievement_info.award4:
        y = draw_text("Award ", achievement_info.award1 or 'N/A', y, p)
        y = draw_last_text("Award Date ", achievement_info.awarddate1 or 'N/A', y, p)
    if achievement_info.award5:
        y = draw_text("Award ", achievement_info.award2 or 'N/A', y, p)
        y = draw_last_text("Award Date ", achievement_info.awarddate2 or 'N/A', y, p)
    y = draw_last_text("Publish Link", achievement_info.publishlink or 'N/A', y, p)
    

    # Draw Banking Details section
    y = draw_text_heading("Banking Details","", y, p)
    y = draw_text(f"Account Holder Name:", banking_info.accholdername or 'N/A', y, p)
    y = draw_text(f"Bank Name:" , banking_info.bankname or 'N/A', y, p)
    y = draw_text(f"Branch Name:", banking_info.branchname or 'N/A', y, p)
    y = draw_text(f"IFSC Code:",banking_info.ifsc or 'N/A', y, p)
    y = draw_text(f"Account Number:",banking_info.acnumber or 'N/A', y, p)
    y = draw_text(f"Pan Card Number:",banking_info.pancardno or 'N/A', y, p)
    y = draw_text(f"Aadhar Card Number:",banking_info.aadharcardno or 'N/A', y, p)
    if banking_info.pancard:
        pancard_url = request.build_absolute_uri(banking_info.pancard.url) if banking_info.pancard else None
        y = draw_link("Pan Card", pancard_url, "View Pan Card", y, p)
    if banking_info.aadharcard:
        aadharcard_url = request.build_absolute_uri(banking_info.aadharcard.url) if banking_info.aadharcard else None
        y = draw_link("Aadhar Card", aadharcard_url, "View Aadhar Card", y, p)
    if banking_info.cheque:
        cheque_url = request.build_absolute_uri(banking_info.cheque.url) if banking_info.cheque else None
        y = draw_last_link("Cheque", cheque_url, "View Cheque", y, p)

    # Draw Reporting Area Details section
    y = draw_text_heading("Reporting Area Details","", y, p)
    y = draw_text(f"MRI Option:",reporting_area_info.mriopt or 'N/A', y, p)
    y = draw_text(f"MRI Others:",reporting_area_info.mriothers or 'N/A', y, p)
    y = draw_text(f"CT Option:",reporting_area_info.ctopt or 'N/A', y, p)
    y = draw_text(f"CT Others:",reporting_area_info.ctothers or 'N/A', y, p)
    y = draw_text(f"Xray:",reporting_area_info.xray or 'N/A', y, p)
    y = draw_text(f"Others:",reporting_area_info.others or 'N/A', y, p)
    y = draw_last_text(f"Others Description:",reporting_area_info.otherText or 'N/A', y, p)

    # Draw Availability Details section
    y = draw_text_heading("Availability Details","", y, p)
    y = draw_text(f"Monday:",availability_info.monday or 'N/A', y, p)
    y = draw_text(f"Tuesday:",availability_info.tuesday or 'N/A', y, p)
    y = draw_text(f"Wednesday:",availability_info.wednesday or 'N/A', y, p)
    y = draw_text(f"Thursday:",availability_info.thursday or 'N/A', y, p)
    y = draw_text(f"Friday:",availability_info.friday or 'N/A', y, p)
    y = draw_text(f"Saturday:",availability_info.saturday or 'N/A', y, p)
    y = draw_text(f"Sunday:",availability_info.sunday or 'N/A', y, p)
    if availability_info.starttime1:
        y = draw_text(f"Time Slot (start):",availability_info.starttime1 or 'N/A', y, p)
        y = draw_last_text(f"Time Slot (end):",availability_info.endtime1 or 'N/A', y, p)
    if availability_info.starttime2:
        y = draw_text(f"Time Slot (start):",availability_info.starttime2 or 'N/A', y, p)
        y = draw_last_text(f"Time Slot (end):",availability_info.endtime2 or 'N/A', y, p)
    if availability_info.starttime3:
        y = draw_text(f"Time Slot (start):",availability_info.starttime3 or 'N/A', y, p)
        y = draw_last_text(f"Time Slot (end)",availability_info.endtime3 or 'N/A', y, p)
    if availability_info.starttime4:
        y = draw_text(f"Time Slot (start):",availability_info.starttime4 or 'N/A', y, p)
        y = draw_last_text(f"Time Slot (end):",availability_info.endtime4 or 'N/A', y, p)

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename=f"{personal_info.first_name}_{personal_info.last_name}_form_data_{personal_info.pk}.pdf")


def send_confirmation_mail(request, user_id):
    # Fetch the PersonalInformation instance
    person = get_object_or_404(PersonalInformation, pk=user_id)

    # Retrieve RateList objects associated with the PersonalInformation instance
    rate_lists = RateList.objects.filter(radiologist=person)

    # Get the current date
    current_date = timezone.now().strftime("%d %B %Y")

    # Fetch time availability info
    time_availabilities = AvailabilityDetails.objects.filter(personal_information=person)
    
    # Initialize lists to hold days and time slots
    days = []
    slots = []

    for availability in time_availabilities:
        # Collect time slots for each day
        if availability.monday:
            days.append('Monday')
        if availability.tuesday:
            days.append('Tuesday')
        if availability.wednesday:
            days.append('Wednesday')
        if availability.thursday:
            days.append('Thursday')
        if availability.friday:
            days.append('Friday')
        if availability.saturday:
            days.append('Saturday')
        if availability.sunday:
            days.append('Sunday')

        if availability.starttime1:
            slots.extend([
                    f"{availability.starttime1} to {availability.endtime1}",
                ])
        if availability.starttime2:
            slots.extend([
                    f"{availability.starttime2} to {availability.endtime2}",
                ])
        if availability.starttime3:
            slots.extend([
                    f"{availability.starttime3} to {availability.endtime3}",
                ])
        if availability.starttime4:
            slots.extend([
                    f"{availability.starttime4} to {availability.endtime4}",
                ])

    # Join days with commas and 'and'
    if len(days) > 1:
        days_info = ", ".join(days[:-1]) + " and " + days[-1]
    elif days:
        days_info = days[0]
    else:
        days_info = "No days specified"

    # Join slots with commas
    if len(slots) > 1:
        slots_info = ", ".join(slots[:-1]) + " and " + slots[-1]
    elif slots:
        slots_info = slots[0]
    else:
        slots_info = "No time slots available"
    # slots_info = ", ".join(slots) if slots else "No time slots available"

    # Format timings information
    timings_info = f" {days_info} with the Time Slots: {slots_info}"

    # Fetch reporting availability info
    reporting_availabilities = ReportingAreaDetails.objects.filter(personal_information=person)
    
    for availability in reporting_availabilities:
        sections = []
        if availability.mriopt:
            sections.append(f"MRI Options: {availability.mriopt}")
        if availability.mriothers:
            sections.append(f"MRI Others: {availability.mriothers}")
        if availability.ctopt:
            sections.append(f"CT Options: {availability.ctopt}")
        if availability.ctothers:
            sections.append(f"CT Others: {availability.ctothers}")
        if availability.xray:
            sections.append("X-Ray")
        if availability.others:
            sections.append(f"Other: {availability.otherText}")
        

    # Join sections with commas
    if len(sections) > 1:
        role_sections = ", ".join(sections[:-1]) + " and " + sections[-1]
    elif slots:
        role_sections = sections[0]
    else:
        role_sections = "No time slots available"
    # role_sections = ", ".join(reporting_sections)

    # Email subject and message
    subject = 'Confirmation Mail from U4RAD'
    message = render_to_string('confirmation_mail_template.txt', {
        'person': person,
        'rate_lists': rate_lists,
        'current_date': current_date,
        'timings_info': timings_info,
        'role_sections': role_sections,
    })

    # Render HTML message
    html_message = render_to_string('confirmation_mail_template.html', {
        'person': person,
        'rate_lists': rate_lists,
        'current_date': current_date,
        'timings_info': timings_info,
        'role_sections': role_sections,
    })

    # Send the email
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [person.email],  # Assuming 'email' is a field in PersonalInformation
            fail_silently=False,
            html_message=html_message,
        )
        person.email_sent = True
        person.save()
        response_data = {
            'status': 'success',
            'message': 'Email Sent Successfully!'
        }
    except Exception as e:
        response_data = {
            'status': 'error',
            'message': 'Email Not Sent! Try after some time.'
        }

    return JsonResponse(response_data)

