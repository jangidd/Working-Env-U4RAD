from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import callback_form_view, callback_complete_view  


urlpatterns = [
    path('', views.login, name='login'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('check_profile_completion/', views.check_profile_completion, name='check_profile_completion'),
    path('check_user_exists/', views.check_user_exists, name='check_user_exists'),
    path('services/', views.service_list, name='service_list'),
    path('services/add/', views.service_create, name='service_create'),
    path('services/<int:pk>/edit/', views.service_update, name='service_update'),
    path('services/<int:pk>/delete/', views.service_delete, name='service_delete'),
    path('services/<int:service_id>/rates/', views.service_rate_list, name='service_rate_list'),
    path('services/<int:service_id>/rates/add/', views.service_rate_create, name='service_rate_create'),
    path('services/<int:service_id>/rates/<int:pk>/edit/', views.service_rate_update, name='service_rate_update'),
    path('services/<int:service_id>/rates/<int:pk>/delete/', views.service_rate_delete, name='service_rate_delete'),
    path('calculate-amount/', views.calculate_amount, name='calculate_amount'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('save_cart_data/', views.save_cart_data, name='save_cart_data'),
    path('user_dashboard/', login_required(views.user_dashboard), name='user_dashboard'),
    path('calculate-amount/user_dashboard/', login_required(views.user_dashboard), name='calculate-amount/user_dashboard'),
    path('logout/', views.logout, name='logout'),
    path("payment/", views.generate_order, name="generate_order"),
    path("topuppayment/", views.generate_topup_order, name="generate_topup_order"),
    path("home/", views.home, name="home"),
    path("quality/", views.quality, name="quality"),
    path("payment/update-status/", views.update_payment_status, name='update_payment_status'),
    path('download-invoice/', views.download_invoice, name='download_invoice'),
    path('coordinator_dashboard/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('update_casecount/<int:cart_item_id>/', views.update_casecount, name='update_casecount'),
    path('upload_file/<int:profileId>/', views.upload_file, name='upload_file'),
    path('download_latest_file/<int:user_id>/', views.download_latest_file, name='download_latest_file'),
    path('user/details/', views.get_user_details, name='get_user_details'),
    path('get_user_files/<int:user_id>/', views.get_user_files, name='get_user_files'),
    path('download_all_files_as_zip/<int:user_id>/', views.download_all_files_as_zip, name='download_all_files_as_zip'),
    path('get_user_orders/<int:user_id>/', views.get_user_orders, name='get_user_orders'),
    path('download_single_invoice/<int:user_id>/<str:provider_order_id>/', views.download_single_invoice, name='download_single_invoice'),

    ################################### Multiform URL's ########################################
    #------------------------------------ Himanshu --------------------------------------------#
    path('radiologist', views.index, name='index'), 
    path('work', views.work, name='work'), 
    path('coordinator', views.coordinator, name = 'coordinator'),
    path('step1/', views.step1, name='step1'),
    path('step2/', views.step2, name='step2'),
    path('step3/', views.step3, name='step3'),
    path('step4/', views.step4, name='step4'),
    path('step5/', views.step5, name='step5'),
    path('step6/', views.step6, name='step6'),
    path('step7/', views.step7, name='step7'),
    path('submit/', views.submit, name='submit'),
    path('registration_pending/<int:pk>/', views.registration_pending, name='registration_pending'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('coordinator/', views.multiform_coordinator_dashboard, name='coordinator'),
    path('supercoordinator/', views.supercoordinator_dashboard, name='supercoordinator_dashboard'),
    # path('update_status/<int:pk>/', views.update_status, name='update_status'),
    path('update_stage1status/<int:pk>/', views.update_stage1status, name='update_stage1status'),
    path('update_stage2status/<int:pk>/', views.update_stage2status, name='update_stage2status'),
    # the below url is for handling the logic of the callback form page.
    path('callback-form/', callback_form_view, name='callback_form'),
    path('callback-complete/', callback_complete_view, name='callback_complete'),
    path('view_complete_form/<int:pk>/', views.view_complete_form, name='view_complete_form'),
    path('update_messages/', views.update_messages, name='update_messages'),
    # The below url is for getting the response in pdf format.
    path('generate_pdf/<int:pk>/', views.generate_pdf, name='generate_pdf'),
    # This is the url to go to the success page after submitting the form.
    path('success/<int:pk>/', views.success, name='success'),
    # This is the url to see the response page after form submission.
    path('view_response/<int:pk>/', views.view_response, name='view_response'),
    # This is the url to go to the ratelist page.
    path('rate_list/<int:radiologist_id>/', views.rate_list, name='rate_list'),
    
    # This is the url to update the ratelist status.
    path('update_status_rate_list/', views.update_status_rate_list, name='update_status_rate_list'),
    path('check_email_existence/', views.check_email_existence, name='check_email_existence'),
    # To get the callback form modal on the coordinator's page.
    path('view_callback_form/<int:pk>/', views.view_callback_form, name='view_callback_form'),
    # Here are the urls to get the ratelist status and update form on the coordinator's page .
    path('view_rate_list_form/<int:radiologist_id>/', views.view_rate_list_form, name='view_rate_list_form'),
    path('update_rate_list/<int:radiologist_id>/', views.update_rate_list, name='update_rate_list'),
    # the url to send the confirmation email from the coordinator's page.
    path('send_confirmation_mail/<int:user_id>/', views.send_confirmation_mail, name='send_confirmation_mail'),

    #################################### End of Multiform URL's #####################################
]
