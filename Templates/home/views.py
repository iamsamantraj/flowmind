from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def Home(request):
    context={
        'name':'Panda',
        'age':22,
        'hobbies':{'cricket','movies'}
    }
    return render(request, 'home.html',context)

def about(request):
    return render(request, 'about.html')