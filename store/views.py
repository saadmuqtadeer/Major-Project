from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
import csv
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Customer
from .forms import RegistrationForm
from django.shortcuts import render, redirect

def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user_type = form.cleaned_data['user_type']
            user = User.objects.create_user(username=name, email=email, password=password)
            customer = Customer.objects.create(user=user, name=name, email=email, user_type=user_type)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'store/signup.html', {'form': form})

def login_view(request):
    error_message = None
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('store')
        else:
            error_message = 'Invalid email or password. Please try again.'
    return render(request, 'store/login.html', {'error_message': error_message})


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
    search_query = medicine.name  # Use medicine name as the search query
    related_medicines = []

    csv_path = 'C:/Users/saad/OneDrive/Desktop/django_ecommerce_mod5-master/django_ecommerce_mod5-master/store/datasets/1mgadded.csv'  # Path to your CSV file
    names = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            names.append(row['cleaned_combined_text'])

    # Calculate TF-IDF vectors for medicine names
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(names + [search_query])
    query_vector = vectors[-1]  # Vector representation of the search query
    item_vectors = vectors[:-1]  # Vector representations of the medicine names
    similarities = cosine_similarity(query_vector, item_vectors).flatten()

    # Sort medicines based on similarity scores
    sorted_indices = similarities.argsort()[::-1][:3]  # Get top 10 similar medicines
    for index in sorted_indices:
        related_medicines.append(names[index])

    return related_medicines

def user_location_view(request):
    return render(request, 'store/maps.html')