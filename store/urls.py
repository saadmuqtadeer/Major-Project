from django.urls import path
from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),

	path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
 
	path('medicine/<int:medicine_id>/', views.medicine_detail, name='medicine_detail'),
 
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('signup/', views.signup, name='signup'),
 
	path('lab-tests/', views.user_location_view, name="maps"),
 
	path('chatbot/', views.chatbot, name='chatbot'),
	path('search/', views.search, name='search'),
 
	path('doctor/', views.doctor, name='doctor'),
    path('user-appointments/', views.user_appointments, name='user_appointments'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('view-doctors/', views.view_do3ctors, name='view_doctors'),
    path('doctor-appointments/<int:doctor_id>/', views.doctor_appointments, name='doctor_appointments'),
   	path('book-appointment/<int:appointment_id>/', views.book_appointment, name='book_appointment'),

]