from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Appointment
from django.utils import timezone
import json
from .models import  Appointment
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
import csv
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from .models import Customer
from .forms import RegistrationForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def signup(request):
    if request.method== 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        user_type = request.POST.get('user_type')
        print(name, email, pass1, pass2, user_type)
        if pass1 != pass2: 
            error_message = "Your password and confrom password are same!!"
            return render(request, 'store/signup.html', {'error_message': error_message})
        else:
            user = User.objects.create_user(username = name, email = email, password = pass1)
            customer = Customer.objects.create(user=user, name=name, email=email, user_type=user_type)
            return redirect('login')
    return render(request, 'store/signup.html')

def login_view(request):
    error_message = None
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')
        user = authenticate(request, username = name, password = password)
        print(name, password, user)
        if user is not None:
            login(request, user)
            try:
                user_type = user.customer.user_type
                if user_type == 'doctor':
                    return redirect('store')
                else:
                    return redirect('store')
            except Customer.DoesNotExist:
                pass
        else:
            error_message = 'Invalid email or password. Please try again.'
            return render(request, 'store/login.html', {'error_message': error_message})
    return render(request, 'store/login.html')

def logout_view(request):
    logout(request)
    return redirect('store')

def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	medicines = Medicine.objects.all()
	context = {'medicines': medicines, 'cartItems': cartItems}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    medicineId = data['medicineId']  # Changed from 'productId' to 'medicineId'
    action = data['action']
    print('Action:', action)
    print('Medicine:', medicineId)

    customer = request.user.customer
    medicine = Medicine.objects.get(id=medicineId)  # Fetch Medicine object
    print(medicine)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, medicine=medicine)  # Changed from 'product' to 'medicine'

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

def medicine_detail(request, medicine_id):
    # Retrieve the medicine object
    medicine = get_object_or_404(Medicine, id=medicine_id)

    # Get cart data to display cart count
    cart_data = cartData(request)
    cartItems = cart_data['cartItems']

 	# Calculate cosine similarity between the given medicine and all other medicines in the dataset
    related_medicines = find_related_medicines(medicine)
    # print(related_medicines)
    # Pass medicine and cart count to template context
    context = {'medicine': medicine, 'cartItems': cartItems, 'related_medicines': related_medicines}
    return render(request, 'store/medicine_detail.html', context)


def find_related_medicines(medicine):
    search_query = medicine.name
    related_medicines = []

    csv_path = 'C:/Users/rajku/Desktop/major/Major-Project/store/datasets/1mgadded.csv'  # Replace 'path/to/dataset.csv' with the actual path to your dataset file
    names = []
    descriptions = []
    manufacturers = []
    active_ingredients = []

    # Read the dataset and extract relevant information
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            names.append(row['name'])
            descriptions.append(row['desc'])
            manufacturers.append(row['manufacturer'])
            active_ingredients.append(row['activeIngredient'])

    # Combine name, description, manufacturer, and active ingredients into a single text
    combined_text = [f"{name} {description} {manufacturer} {active_ingredient}" for name, description, manufacturer, active_ingredient in zip(names, descriptions, manufacturers, active_ingredients)]

    # Calculate TF-IDF vectors
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(combined_text + [search_query])
    query_vector = vectors[-1]  # Vector representation of the search query
    item_vectors = vectors[:-1]  # Vector representations of the medicine information
    similarities = cosine_similarity(query_vector, item_vectors).flatten()

    # Sort medicines based on similarity scores
    sorted_indices = similarities.argsort()[::-1][:3]  # Get top 3 similar medicines
    for index in sorted_indices:
        related_medicines.append({
            'name': names[index],
            'description': descriptions[index],
            'manufacturer': manufacturers[index],
            'active_ingredient': active_ingredients[index]
        })

    return related_medicines

def user_location_view(request):
    data = cartData(request)
    cartItems = data['cartItems']
    return render(request, 'store/maps.html', {'cartItems':cartItems})

cnt = 0
def chatbot(request):
    data = cartData(request)
    cartItems = data['cartItems']
    global cnt
    if request.method == 'POST':
        cnt = cnt + 1
        if cnt == 1:
            user_message = request.POST.get('message')
            server_response = "Hello " + user_message + "!! Enter the symptom you are experiencing?"
            return JsonResponse({'message': server_response})
        elif cnt == 2:
            user_message = request.POST.get('message')
            server_response = handle_user_input(user_message)
            if "Enter valid symptom." in server_response:
                cnt -= 1
                return JsonResponse({'message': server_response})
            elif "Searches related to input:" in server_response:
                if le > 1:
                    server_response += "Select the one you meant (0 - {len(cnf_dis) - 1}):  "
                else:
                    server_response += "Enter valid symptom: "
                return JsonResponse({'message': server_response})
            else:
                return JsonResponse({'message': server_response})
    else:
        initial_message = get_initial_message()
        return render(request, 'store/chatbot.html', {'server_message': initial_message, 'cartItems': cartItems})


import random
def get_initial_message():
    greetings = ["Hello! I am the HealthCare ChatBot. What is your name?", 
                 "Hi there! I'm here to assist you with your health concerns. What's your name?",
                 "Greetings! I'm the HealthCare ChatBot. What's your name?"]
    return random.choice(greetings)


def search(request):
    query = request.GET.get('q')
    results = []
    if query:
        # Perform search query on Medicine model
        results = Medicine.objects.filter(
            name__icontains=query
            # Add other fields for search as needed
        )
    data = cartData(request)
    cartItems = data['cartItems']
    
    return render(request, 'store/search.html', {'medicines': results, 'query': query, 'cartItems' :cartItems})

def doctor(request):
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    
    if request.method == 'POST':
        start_time = request.POST.get('start-time')
        end_time = request.POST.get('end-time')
        # gmeet_link = request.POST.get('gmeet-link')
        gmeet_link = "meet.google.com"

        # Get the logged-in doctor (assuming they are authenticated)
        doctor = request.user  # This is the logged-in user (doctor)

        # Create a new appointment entry
        appointment = Appointment.objects.create(
            start_time=start_time,
            end_time=end_time,
            doctor_id=doctor.id,  # Assign the ID of the logged-in user as doctor_id
            doctor_name=doctor.username,  # Assign the username of the logged-in user as doctor_name
            gmeet=gmeet_link
        )

        print('Appointment created successfully')

        # Redirect or render success message
        # return redirect('appointment_success')  

    return render(request, 'store/doctor.html', context)

def user_appointments(request):
    # Get the doctor_id of the logged-in user
    doctor_id = request.user.id  # Assuming doctor_id is stored as the user ID

    # Retrieve appointments filtered by doctor_id
    appointments = Appointment.objects.filter(doctor_id=doctor_id)

    # Pass appointments to the template
    return render(request, 'store/user_appointments.html', {'appointments': appointments})

def cancel_appointment(request, appointment_id):
    if request.method == 'DELETE':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.delete()
        return JsonResponse({'message': 'Appointment canceled successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
    

def view_doctors(request):
    doctors = Customer.objects.filter(user_type='doctor')
    return render(request, 'store/doctors_list.html', {'doctors': doctors})

# def doctor_appointments(request, doctor_id):
#     doctor = get_object_or_404(Customer, id=doctor_id, user_type='doctor')
#     appointments = Appointment.objects.filter(doctor=doctor)

#     return render(request, 'store/doctor_appointments.html', {'doctor': doctor, 'appointments': appointments})

from django.shortcuts import render, get_object_or_404
from .models import Customer, Appointment


def doctor_appointments(request, doctor_id):
    doctor = get_object_or_404(Customer, id=doctor_id, user_type='doctor')
    # appointments = Appointment.objects.all()
    appointments = Appointment.objects.filter(doctor_name=doctor.name)
    print('doc',doctor_id)
    print('app',appointments)
    for i in appointments:
         print(i)

    return render(request, 'store/doctor_appointments.html', {'doctor': doctor, 'appointments': appointments})


def book_appointment(request, appointment_id):
    print('yes')
    if request.method == 'POST':
        print('yes1')
        appointment = Appointment.objects.get(id=appointment_id)

        # Extract patient information from POST data
        patient_name = request.POST.get('patient_name')
        patient_id = request.POST.get('patient_id')
        print('yes11')

        # Update appointment with patient information
        appointment.patient_name = patient_name
        appointment.patient_id = patient_id
        appointment.save()
        print('yes111')

        return JsonResponse({'message': 'Appointment booked successfully.'})

    return JsonResponse({'message': 'Invalid request method.'}, status=400)


def process_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        total_amount = data.get('total_amount')

        # Process the order and update status in database
        # Implement your logic to handle order processing and payment status

        return JsonResponse({'message': 'Order processed successfully.'})
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=400)