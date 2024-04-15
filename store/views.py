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

from django.shortcuts import render
import random
from django.http import JsonResponse
import re
import pandas as pd
import pyttsx3
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier,_tree
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.svm import SVC
import csv
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

training = pd.read_csv('C:/Users/saad/OneDrive/Desktop/CS comm/char/Data/Training.csv')
testing= pd.read_csv('C:/Users/saad/OneDrive/Desktop/CS comm/char/Data/Testing.csv')
cols= training.columns
cols= cols[:-1]
x = training[cols]
y = training['prognosis']
y1= y


reduced_data = training.groupby(training['prognosis']).max()

#mapping strings to numbers
le = preprocessing.LabelEncoder()
le.fit(y)
y = le.transform(y)


x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=42)
testx    = testing[cols]
testy    = testing['prognosis']  
testy    = le.transform(testy)


clf1  = DecisionTreeClassifier()
clf = clf1.fit(x_train,y_train)
print(clf.score(x_train,y_train))
print ("cross result========")
scores = cross_val_score(clf, x_test, y_test, cv=3)
print (scores)
print (scores.mean())


model=SVC()
model.fit(x_train,y_train)
print("for svm: ")
print(model.score(x_test,y_test))

importances = clf.feature_importances_
indices = np.argsort(importances)[::-1]
features = cols

def readn(nstr):
    engine = pyttsx3.init()

    engine.setProperty('voice', "english+f5")
    engine.setProperty('rate', 130)

    engine.say(nstr)
    engine.runAndWait()
    engine.stop()


severityDictionary=dict()
description_list = dict()
precautionDictionary=dict()

symptoms_dict = {}

for index, symptom in enumerate(x):
       symptoms_dict[symptom] = index

tree_ = clf.tree_
cols = [
    cols[i] if i != _tree.TREE_UNDEFINED else "undefined!"
    for i in tree_.feature
]

chk_dis=",".join(cols).split(",")
symptoms_present = []

def check_pattern(dis_list,inp):
    pred_list=[]
    inp=inp.replace(' ','_')
    patt = f"{inp}"
    regexp = re.compile(patt)
    pred_list=[item for item in dis_list if regexp.search(item)]
    if(len(pred_list)>0):
        return 1,pred_list
    else:
        return 0,[]
    
def getDescription():
    global description_list
    with open('C:/Users/saad/OneDrive/Desktop/CS comm/char/MasterData/symptom_Description.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _description={row[0]:row[1]}
            description_list.update(_description)



def getSeverityDict():
    global severityDictionary
    with open('C:/Users/saad/OneDrive/Desktop/CS comm/char/MasterData/symptom_severity.csv') as csv_file:

        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        try:
            for row in csv_reader:
                _diction={row[0]:int(row[1])}
                severityDictionary.update(_diction)
        except:
            pass


def getprecautionDict():
    global precautionDictionary
    with open('C:/Users/saad/OneDrive/Desktop/CS comm/char/MasterData/symptom_precaution.csv') as csv_file:

        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _prec={row[0]:[row[1],row[2],row[3],row[4]]}
            precautionDictionary.update(_prec)  


le = 0
def handle_user_input(symptom):
    conf, cnf_dis = check_pattern(chk_dis, symptom)
    le = len(cnf_dis)
    response = ""
    if conf == 1:
        response += "Searches related to input:\n"
        for num, it in enumerate(cnf_dis):
            response += str(num) + ")" + it + "\n"
    else:
        response = "Enter valid symptom.\n"
    return response

cnt = 0
def chatbot(request):
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
        return render(request, 'store/chatbot.html', {'server_message': initial_message})



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
    order = data['order']
    items = data['items']
    context = {'items':items, 'order':order, 'cartItems':cartItems}
    
    return render(request, 'store/search.html', {'medicines': results, 'query': query})