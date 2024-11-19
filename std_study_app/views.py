from django.contrib.auth import authenticate,logout,login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from youtubesearchpython import VideosSearch
from std_study_app.models import Homework
from django.contrib import messages
from django.views import generic
from . forms import DashboardFom  
from . models import Notes
from . forms import *
from . views import *
import wikipedia
import requests
# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You are now logged in.')
            return redirect('login') 
    else:
        form = UserCreationForm()
    return render(request, 'dashboard/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            user = authenticate(username=username, password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, You are Login Successfully.. {username} !')
                return redirect('home')  
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/login.html', {'form': form})

def user_logout(request):
   return render(request,'dashboard/logout.html')
   #return redirect('/home')


def home(request):
    return render(request,'dashboard/home.html')


@login_required
def notes(request):
    if request.method =="POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            notes=Notes(user=request.user,title=request.POST['title'],description=request.POST['description'])
            notes.save()
        messages.success(request,f"Notes Added from {request.user.username} Successfully..!")
    else:
        form=NotesForm()
    notes=Notes.objects.filter(user=request.user)
    context={
            'notes':notes,
            'form':form
            }
    
    return render(request,'dashboard/notes.html',context) 


@login_required
def delete_note(request,pk=None):
    Notes.objects.get(id=pk).delete()
    return redirect("notes")


class NotesDetailView(generic.DetailView):
    model = Notes
    template_name = 'dashboard/notes_detail.html'  
    context_object_name = 'note' 


@login_required
def homework(request):
    if request.method=="POST":
        form=HomeworkForm(request.POST)
        if form.is_valid():
            try:
                finished=request.POST['is_finished']
                if finished=='on':
                    finished=True
                else:
                    finished=False
            except:
                finished=False
            homeworks=Homework(
                user=request.user,
                subject=request.POST['subject'],
                title=request.POST['title'],
                description=request.POST['description'],
                due=request.POST['due'],
                is_finished=finished
            )
            homeworks.save()
            messages.success(request,f'HomeWork Added From {request.user.username}..!')
    else:
        form=HomeworkForm()
    homework=Homework.objects.filter(user=request.user)
    if len(homework) == 0:
        homework_done=True
    else:
        homework_done=False
    context={'homeworks':homework,'homeworks_done':homework_done,'form':form}
    return render(request,'dashboard/homework.html',context)


@login_required
def update_homework(request,pk=None):
    homework=Homework.objects.get(id=pk)
    if homework.is_finished == True:
        homework.is_finished =False
    else:
        homework.is_finished = True
        homework.save()
        return redirect('homework')
    
    
@login_required
def delete_homework(request,pk=None):
    Homework.objects.get(id=pk).delete()
    return redirect("homework")


def youtube(request):
    if request.method == 'POST':
        form = DashboardFom(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            video = VideosSearch(text, limit=10)
            result_list = []
            for i in video.result()['result']:
                result_dict = {
                    'input': text,
                    'title': i['title'],
                    'duration': i['duration'],
                    'thumbnail': i['thumbnails'][0]['url'],
                    'channel': i['channel']['name'],
                    'link': i['link'],
                    'views': i['viewCount']['short'],
                    'published': i['publishedTime']
                }
                desc = ''
                if i['descriptionSnippet']:
                    for j in i['descriptionSnippet']:
                        desc += j['text']
                result_dict['description'] = desc
                result_list.append(result_dict)

            context = {'form': form, 'results': result_list}
            return render(request, 'dashboard/youtube.html', context)
    else:
        form = DashboardFom()

    context = {'form': form}
    return render(request, 'dashboard/youtube.html', context)


@login_required
def todo(request):
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished =request.POST['is_finished']
                if finished =='on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            todos = Todo(
                user = request.user,
                title = request.POST['title'],
                is_finished = finished
            )
            todos.save()
            messages.success(request,f"Todo Added From {request.user.username} !!")
    else:
        form =TodoForm()
    todo = Todo.objects.filter(user=request.user)
    if len(todo) == 0:
        todos_done = True
    else:
        todos_done = False
    
    context ={
               'form':form,
               'todos':todo,
               'todos_done':todos_done
              }
    return render(request,'dashboard/todo.html',context)


@login_required
def update_todo(request,pk=None):
    todo =Todo.objects.get(id=pk)
    if todo.is_finished == True:
        todo.is_finished = False
    else:
        todo.is_finished = True
    todo.save()
    return redirect('todo')


@login_required
def delete_todo(request,pk=None):
    Todo.objects.get(id=pk).delete()
    return redirect('todo')


def books(request):
    if request.method == 'POST':
        form = DashboardFom(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            url = "https://www.googleapis.com/books/v1/volumes?q=" + text
            r = requests.get(url)
            if r.status_code == 200:
                answer = r.json()
                result_list = []
                for item in answer.get('items', [])[:10]:
                    volume_info = item.get('volumeInfo', {})
                    result_dict = {
                        'title': volume_info.get('title', ''),
                        'subtitle': volume_info.get('subtitle', ''),
                        'description': volume_info.get('description', ''),
                        'count': volume_info.get('pageCount', ''),
                        'categories': volume_info.get('categories', []),
                        'rating': volume_info.get('pageRating', ''),
                        'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                        'preview': volume_info.get('previewLink', '')
                    }
                    result_list.append(result_dict)

                context = {'form': form, 'results': result_list}
                return render(request, 'dashboard/books.html', context)
    else:
        form = DashboardFom()

    context = {'form': form}
    return render(request, 'dashboard/books.html', context)


def dictionary(request):
    if request.method == 'POST':
        form = DashboardFom(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            url = "https://api.dictionaryapi.dev/api/v2/entries/en_US/" + text
            r = requests.get(url)
            if r.status_code == 200:
                answer = r.json()
                try:
                    phonetics = answer[0]['phonetics'][0]['text']
                    audio = answer[0]['phonetics'][0]['audio']
                    definition = answer[0]['meanings'][0]['definitions'][0]['definition']
                    examples = answer[0]['meanings'][0]['definitions'][0]['examples']
                    synonyms = answer[0]['meanings'][0]['definitions'][0]['synonyms']
                    context = {
                        'form': form,
                        'input': text,
                        'phonetics': phonetics,
                        'audio': audio,
                        'definition': definition,
                        'examples': examples,
                        'synonyms': synonyms
                    }
                except (IndexError, KeyError):
                    context = {'form': form, 'input': text, 'error': 'Word not found or API response structure changed.'}
            else:
                context = {'form': form, 'input': text, 'error': 'Error fetching data from API.'}
        else:
            context = {'form': form, 'input': ''}
        return render(request, 'dashboard/dictionary.html', context)
    else:
        form = DashboardFom()
        context = {'form': form, 'input': ''}
    return render(request, 'dashboard/dictionary.html', context)


def wiki(request):
    if request.method == 'POST':
        text = request.POST['text']
        form = DashboardFom(request.POST)
        search = wikipedia.page(text)
        context = {
            'form': form,
            'title':search.title,
            'link':search.url,
            'details':search.summary
        }
        return render(request,'dashboard/wiki.html',context)
    else:
        form = DashboardFom()
        context ={
            'form':form
        }
    return render(request,'dashboard/wiki.html',context)


def conversion(request):
    if request.method == 'POST':
        form = ConversionForm(request.POST)
        if request.POST['measurement'] == 'length':
            measurement_form = ConversionLengthForm()
            context = {
                'form':form,
                'm_form':measurement_form,
                'input':True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >=0:
                    if first == 'yard' and second == 'foot':
                        answer = f'{input} yard = {int(input)*3} foot'
                    if first == 'foot' and second == 'yard':
                        answer = f'{input} foot = {int(input)*3} foot'
                context = {
                    'form':form,
                    'm_form':measurement_form,
                    'input':'True',
                    'answer':answer
                }
        if request.POST['measurement'] == 'mass':
            measurement_form = ConversionMassForm()
            context = {
                'form':form,
                'm_form':measurement_form,
                'input':True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >=0:
                    if first == 'pound' and second == 'kilogram':
                        answer = f'{input} pound = {int(input)*0.453592} kilogram'
                    if first == 'kilogram' and second == 'pound':
                        answer = f'{input} kilogram = {int(input)*2.20462} pound'
                context = {
                    'form':form,
                    'm_form':measurement_form,
                    'input':'True',
                    'answer':answer
                }
    else:
        form =ConversionForm()
        context = {
            'form':form,
            'input': False
        }
    return render(request,'dashboard/conversion.html',context)

@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished =False,user=request.user)
    todos =Todo.objects.filter(is_finished =False,user=request.user)
    if len(homeworks) == 0:
        homework_done =True
    else:
        homework_done =False

    if len(todos) == 0:
        todos_done =True
    else:
        todos_done =False
    context ={
        'homeworks':homeworks,
        'todos':todos,
        'homework_done':homework_done,
        'todos_done':todos_done
    }
    return render(request,'dashboard/profile.html',context)



