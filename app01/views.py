from django.shortcuts import render,redirect
from django.forms import ModelForm
from django.forms import widgets as wd
from rbac import models
from django.conf import settings


class UserInfo(ModelForm):
    class Meta:
        model = models.User
        fields = ['username','password']
        widgets = {
            'password':wd.PasswordInput()
        }


def login(request):
    if request.method == "GET":
        form = UserInfo()
        return render(request,"login.html",{"form":form})
    else:
        form = UserInfo(request.POST)
        if form.is_valid():
            obj = models.User.objects.filter(**form.cleaned_data).first()
            if obj:
                request.session[settings.USERINFO] = {'id': obj.id, 'name': obj.userinfo.name}
                from rbac.server.begin import begin
                begin(obj,request)
                return redirect('/index/')
            else:
                error = {"msg":'用户名密码不匹配！'}
                return render(request, "login.html", {"form": form,'error':error})
        else:
            return render(request, "login.html", {"form": form})


from django.http import StreamingHttpResponse


def big_file_download(request):
    def file_iterator(file_name, chunk_size=512):
        with open(file_name,'rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    the_file_name = "text.xlsx"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
    return response


def index(request):
    return render(request,'index.html')