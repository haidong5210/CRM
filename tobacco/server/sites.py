'''
使用方法
class MyTobaccoConfig(sites.TobaccoConfig):
    def host(self,obj=None,is_head=False):
        if is_head:
            return "主机"
        show_list = []
        for item in obj.host.all():
            show_list.append(item.hostname)
        return ",".join(show_list)

    def gender(self,obj=None,is_head=False):
        if is_head:
            return "性别"
        return obj.get_gender_display()
    list_display = ["id","username","password","email","type",gender,host]
    condition_list = ["username__contains","email__contains"]
    show_search_input = True

    def del_catch(self,request):
        pk_list = request.POST.getlist("pk")
        models.UserInfo.objects.filter(id__in=pk_list).delete()
    del_catch.text="批量删除"
    catch_list = [del_catch,]
    show_catch = True
    comb_list = [
                 sites.PacComb("gender",is_choice=True),
                 sites.PacComb("type",multi=True),
                 sites.PacComb("host"),
                 ]
    edit_link = ['username']
sites.site.register(models.UserInfo, MyTobaccoConfig)
'''
import copy
import json

from django.conf.urls import url, include
from django.db.models import ForeignKey, ManyToManyField
from django.db.models import Q
from django.forms import ModelForm
from django.http import QueryDict
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from tobacco.page.pager import Pagination


class PacComb:
    """
    对comb_list的数据封装的类
    """
    def __init__(self,field_name,multi=False,condition=None,is_choice=False,text_func_name=None, val_func_name=None):
        """
        封装comb_list内的数据
        :param field_name: 字段名
        :param multi:  是否多选
        :param condition: 显示多少的条件
        :param is_choice: 是否是choice字段
        """
        self.field_name = field_name
        self.multi = multi
        self.condition = condition
        self.is_choice = is_choice
        self.text_func_name = text_func_name
        self.val_func_name = val_func_name

    def get_queryset(self,_field):
        if not self.condition:
            return _field.rel.to.objects.all()
        else:
            return _field.rel.to.objects.filter(**self.condition)

    def get_choice(self,_field):
        return _field.choices


class FilterRow:
    """
    返回到前端的样式，可迭代对象
    """
    def __init__(self,paccomb_obj, data, request):
        """
        :param paccomb_obj: comb_list里存的PacComb的对象
        :param data:  对应comb_list里字段的表的所有数据queryset
        :param request:为了得到request.GET
        """
        self.comb_obj = paccomb_obj
        self.data = data
        self.request = request

    def __iter__(self):
        current_id = self.request.GET.get(self.comb_obj.field_name)
        path = self.request.path
        param = copy.deepcopy(self.request.GET)
        param._mutable = True
        #生成全部的url
        if self.comb_obj.field_name in param:
            val = param.pop(self.comb_obj.field_name)      #pop拿出来的值是列表
            yield mark_safe('<a href="%s?%s">全部</a>'%(path,param.urlencode()))
            param.setlist(self.comb_obj.field_name, val)
        else:
            yield mark_safe('<a class="active" href="%s?%s">全部</a>' % (path, param.urlencode()))
        #生成选项的url
        for field_obj in self.data:
            if self.comb_obj.is_choice:
                pk, text = str(field_obj[0]), field_obj[1]
            else:
                pk = self.comb_obj.val_func_name(field_obj) if self.comb_obj.val_func_name else str(field_obj.pk)
                text =self.comb_obj.text_func_name(field_obj) if self.comb_obj.text_func_name else str(field_obj)
            if not self.comb_obj.multi:    #单选
                param[self.comb_obj.field_name] = pk
                if current_id == pk:
                    yield mark_safe('<a class="active" href="%s?%s">%s</a>'%(path,param.urlencode(),text))
                else:
                    yield mark_safe('<a href="%s?%s">%s</a>' % (path, param.urlencode(), text))
            else:    #多选
                _params = copy.deepcopy(param)
                id_list = _params.getlist(self.comb_obj.field_name)
                if pk in id_list:
                    id_list.remove(pk)
                    _params.setlist(self.comb_obj.field_name,id_list)
                    yield mark_safe('<a class="active" href="%s?%s">%s</a>' % (path, _params.urlencode(), text))
                else:
                    id_list.append(pk)
                    _params.setlist(self.comb_obj.field_name, id_list)
                    yield mark_safe('<a href="%s?%s">%s</a>' % (path, _params.urlencode(), text))


class PacListView(object):
    """
    封装list_view
    """
    def __init__(self,master_obj,model_set):
        self.master_obj = master_obj                         # 下面的TobaccoConfig的对象
        self.model_set = model_set                           # 对象的表所有数据

        self.get_list_display = master_obj.get_list_display()
        self.model_class = master_obj.model_class
        self.request = master_obj.request
        pager_obj = Pagination(self.request.GET.get('page', 1), len(self.model_set), self.request.path_info,
                           self.request.GET, per_page_count=10)        #分页默认10个一页
        self.pager_obj = pager_obj                                     #分页组件的对象
        self.show_search_input = master_obj.get_show_search_input()     #是否展示搜索框
        self.condition_value = master_obj.request.GET.get("condition", "")  # 在url上直接写搜索条件，显示在input框上用到
        self.get_catch_list = master_obj.get_catch_list()             #得到批量操作的列表
        self.show_catch = master_obj.get_show_catch()                 #是否展示批量操作框
        self.show_comb = master_obj.get_show_comb()
        self.comb_list = master_obj.get_comb_list()                   #组合搜索
        self.edit_link = master_obj.get_edit_link()
        self.parm = master_obj.parm

    def get_catch(self):
        """
        处理批量操作的显示在前端的内容，函数名和函数的自定义text
        :return:
        """
        result = []
        for func in self.get_catch_list:
            temp = {"name":func.__name__,"text":func.text}
            result.append(temp)
        return result

    def head_list(self):
        # 处理表头
        head_list = []
        if self.get_list_display:
            for filed_name in self.get_list_display:
                if isinstance(filed_name, str):
                    verbose_name = self.model_class._meta.get_field(filed_name).verbose_name
                else:
                    verbose_name = filed_name(self.master_obj, is_head=True)
                head_list.append(verbose_name)
        return head_list

    def data_list(self):
        # 处理数据
        data_list = []
        for obj in self.model_set:
            field_list = []
            if self.get_list_display:
                for filed_name in self.get_list_display:
                    if isinstance(filed_name, str):
                        text = getattr(obj, filed_name)
                    else:
                        text = filed_name(self.master_obj, obj)
                    if filed_name in self.edit_link:
                        text = self.get_edit_url(obj.id,text)
                    field_list.append(text)
            else:
                field_list.append(obj)
            data_list.append(field_list)
        return data_list[self.pager_obj.start:self.pager_obj.end]

    def add_url(self):
        add_url = "%s?%s" % (self.master_obj.get_add_url(),self.master_obj.parm.urlencode())
        return add_url

    def is_add(self):
        return self.master_obj.get_add_btn()

    def combinatorial(self):
        """
        展示组合搜索tag
        :return:
        """
        for paccomb_obj in self.comb_list:
            _field = self.model_class._meta.get_field(paccomb_obj.field_name)
            if isinstance(_field,ForeignKey):
                row = FilterRow(paccomb_obj,paccomb_obj.get_queryset(_field),self.request)
            elif isinstance(_field,ManyToManyField):
                row = FilterRow(paccomb_obj,paccomb_obj.get_queryset(_field),self.request)
            else:
                row = FilterRow(paccomb_obj,paccomb_obj.get_choice(_field),self.request)
            yield row

    def get_edit_url(self,pk,text,):
        """
        获取修改的url
        :param pk: 当前行的id
        :param text: 当前对应的文本
        :return:
        """
        return mark_safe("<a href='%s?%s'>%s</a>" % (self.master_obj.get_edit_url(pk), self.parm.urlencode(),text))


class TobaccoConfig(object):
    list_display = []       #显示那几个列，字段
    condition_list = []     #搜索对应的字段
    catch_list = []          #批量执行那个操作
    comb_list = []          #组合搜索
    edit_link = []          #编辑的字段是哪个
    order_by = []           #列表页面的展示
    show_add_btn = True
    model_form_class = None
    show_search_input = False
    show_catch = False
    show_comb = False

    def __init__(self,model_class,site):
        self.model_class = model_class
        self.site = site
        self.request = None
        self.parm = None
        self.url_encode_key = "_listfilter"

    def get_list_display(self):
        """
        处理生成check，删除，编辑按钮
        :return:
        """
        data = []
        if self.list_display:
            data.extend(self.list_display)
            # data.append(TobaccoConfig.edit)
            data.append(TobaccoConfig.delete)
            data.insert(0, TobaccoConfig.check)
        return data

    def edit(self,obj=None,is_head=False):
        if is_head:
            return "操作"
        return mark_safe("<a href='%s?%s'>编辑</a>"%(self.get_edit_url(obj.id),self.parm.urlencode()))

    def delete(self,obj=None,is_head=False):
        if is_head:
            return "操作"
        return mark_safe("<a href='%s?%s'>删除</a>"%(self.get_delete_url(obj.id),self.parm.urlencode()))

    def check(self,obj=None,is_head=False):
        if is_head:
            return "#"
        return mark_safe('<input type="checkbox" name="pk" value="%s">'%obj.id)

    def get_edit_url(self,nid):
        """
        反向生成修改的url
        :param nid:
        :return:
        """
        name = "tobacco:%s_%s_edit" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        current_url = reverse(name, args=(nid,))
        return current_url

    def get_list_url(self):
        """
        反向生成列表的url
        :return:
        """
        name = "tobacco:%s_%s_list" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        current_url = reverse(name)
        return current_url

    def get_add_url(self):
        """
        反向生成添加的url
        :return:
        """
        name = "tobacco:%s_%s_add" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        current_url = reverse(name)
        return current_url

    def get_delete_url(self,nid):
        """
        反向生成删除的url
        :param nid:
        :return:
        """
        name = "tobacco:%s_%s_delete" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        current_url = reverse(name,args=(nid,))
        return current_url

    @property
    def urls(self):
        return self.get_url()

    def wrap(self, view_func):
        """
        装饰器
        给self.request赋值
        :param view_func:
        :return:
        """
        def inner(request, *args, **kwargs):
            self.request = request
            return view_func(request, *args, **kwargs)
        return inner

    def get_url(self):
        app_model_name = (self.model_class._meta.app_label,self.model_class._meta.model_name)
        urlpatterns =[
            url(r'^$',self.wrap(self.list_view),name="%s_%s_list"%app_model_name),
            url(r'^add/$',self.wrap(self.add_view),name="%s_%s_add"%app_model_name),
            url(r'^(\d+)/edit/$',self.wrap(self.edit_view),name="%s_%s_edit"%app_model_name),
            url(r'^(\d+)/delete/$',self.wrap(self.delete_view),name="%s_%s_delete"%app_model_name),
        ]
        urlpatterns.extend(self.extr_urls())
        return urlpatterns

    def extr_urls(self):
        """
        自定义添加的url
        :return:[url(.......),url(.......),]
        """
        return []

    def get_add_btn(self):
        return self.show_add_btn

    def get_model_form_class(self):
        if not self.model_form_class:
            class List(ModelForm):
                class Meta:
                    model = self.model_class
                    fields = "__all__"
            return List
        else:
            return self.model_form_class

    def get_condition_list(self):
        result = []
        if self.condition_list:
            result.extend(self.condition_list)
        return result

    def get_condition(self):
        """
        得到搜索的字段条件，利用Q
        :return:con
        """
        condition_value = self.request.GET.get("condition")
        con = Q()
        con.connector = "or"
        if condition_value and self.get_show_search_input():
            for condition_field in self.get_condition_list():
                con.children.append((condition_field,condition_value))
        return con

    def get_show_search_input(self):
        """
        自定义是否显示搜索框，默认不显示
        :return:
        """
        if self.show_search_input:
            return self.show_search_input

    def get_catch_list(self):
        """
        批量
        :return:
        """
        result = []
        if self.catch_list:
            result.extend(self.catch_list)
        return result

    def get_show_catch(self):
        if self.show_catch:
            return self.show_catch

    def get_show_comb(self):
        """
        是否展示组合搜索
        :return:
        """
        if self.show_comb:
            return self.show_comb

    def get_comb_list(self):
        result = []
        if self.comb_list:
            result.extend(self.comb_list)
        return result

    def get_edit_link(self):
        result = []
        if self.edit_link:
            result.extend(self.edit_link)
        return result

    def get_order_by(self):
        result = []
        result.extend(self.order_by)
        return result

    def list_view(self,request,*args,**kwargs):
        """
        展示页面
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.parm = QueryDict(mutable=True)
        self.parm[self.url_encode_key] = self.request.GET.urlencode()
        if request.method == "POST" and self.get_show_catch():
            func_str = request.POST.get("list_action")
            if hasattr(self,func_str):
                catch_func = getattr(self,func_str)
                ret = catch_func(request)
                if ret:
                    return ret
        #处理组合搜索
        comb_condition = {}
        option_list = self.get_comb_list()
        for key in request.GET.keys():
            value_list = request.GET.getlist(key)
            flag = False
            for option in option_list:
                if option.field_name == key:
                    flag = True
                    break
            if flag:
                comb_condition["%s__in" % key] = value_list
        model_set = self.model_class.objects.filter(self.get_condition()).filter(**comb_condition).order_by(*self.get_order_by()).distinct()
        list_view_obj = PacListView(self,model_set)                       #封装的那个对象，只传对象到前端
        return render(request,"list.html",{"list_view_obj":list_view_obj})

    def add_view(self,request,*args,**kwargs):
        model_form_class = self.get_model_form_class()
        _popbackid = request.GET.get('_popbackid')
        if request.method == "GET":
            form = model_form_class()
            return render(request,"add.html",{"form":form,'config':self})
        else:
            form = model_form_class(request.POST)
            if form.is_valid():
                add_obj = form.save()
                if _popbackid:      #是popup请求
                    from django.db.models.fields.reverse_related import ManyToOneRel
                    result = {'status': False, 'id': None, 'text': None, 'popbackid': _popbackid}
                    model_name = request.GET.get('model_name')  # popup路径传来的customer,你点击的那个字段
                    related_name = request.GET.get('related_name')  # popup路径传来的
                    for related_object in add_obj._meta.related_objects:     #跟新添加的对象所有关联的字段相应的表
                        _model_name = related_object.field.model._meta.model_name    #related_object是ManyToOneRel的类实力，里面封装的init
                        _related_name = related_object.related_name
                        if type(related_object) == ManyToOneRel:   # foreignkey的时候是对象的to_field
                            _field_name = related_object.field_name       #_field_name是跟所关联字段to_field
                        else:    #manytomany的时候外键是id
                            _field_name = 'pk'
                        _limit_choices_to = related_object.limit_choices_to
                        if model_name == _model_name and related_name == str(_related_name):     #判断是点的那个popup按钮
                            is_exists = self.model_class.objects.filter(**_limit_choices_to, pk=add_obj.pk).exists()   #判断是否在对应的limitchoice里
                            if is_exists:
                                # 如果新创建的用户时，销售部的人，页面才增加
                                # 分门别类做判断：
                                result['status'] = True
                                result['text'] = str(add_obj)
                                result['id'] = getattr(add_obj, _field_name)
                                return render(request,"PopResponse.html",
                                              {"json_result":json.dumps(result,ensure_ascii=False)})
                    return render(request, 'PopResponse.html',
                                  {'json_result': json.dumps(result, ensure_ascii=False)})
                else:
                    list_url = "%s?%s"%(self.get_list_url(),self.request.GET.get(self.url_encode_key))
                    return redirect(list_url)
            else:
                return render(request, "add.html", {"form": form,'config':self})

    def edit_view(self,request,nid,*args,**kwargs):
        model_form_class = self.get_model_form_class()
        obj = self.model_class.objects.filter(pk=nid).first()
        if request.method == "GET":
            form = model_form_class(instance=obj)
            return render(request,"edit.html",{"form":form,'config':self})
        else:
            form = model_form_class(instance=obj,data=request.POST)
            if form.is_valid():
                form.save()
                list_url = "%s?%s" % (self.get_list_url(), self.request.GET.get(self.url_encode_key))
                return redirect(list_url)
            else:
                return render(request, "edit.html", {"form": form,'config':self})

    def delete_view(self,request,nid,*args,**kwargs):
        if request.method == "GET":
            return render(request,"delete.html")
        else:
            self.model_class.objects.filter(pk=nid).delete()
            list_url = "%s?%s" % (self.get_list_url(), self.request.GET.get(self.url_encode_key))
            return redirect(list_url)


class MasterSite(object):
    def __init__(self):
        self._registry = {}

    def register(self,model_class,master_class=None):
        if not master_class:
            master_class = TobaccoConfig
        self._registry[model_class] = master_class(model_class,self)

    @property
    def urls(self):
        return self.get_url(),None,"tobacco"

    def get_url(self):
        urlpatterns =[]
        for model_class,master_class in self._registry.items():
            app_name = model_class._meta.app_label
            model_name = model_class._meta.model_name
            url_patterns = url(r'^%s/%s/'%(app_name,model_name),include(master_class.urls))
            urlpatterns.append(url_patterns)
        return urlpatterns
site = MasterSite()