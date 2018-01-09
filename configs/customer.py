from app01.basepermission import BasePermission
import datetime
from tobacco.server import sites
from app01 import models
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import redirect,HttpResponse,render
from django.db.models import Q
from django.db import transaction


class CustomerConfig(BasePermission,sites.TobaccoConfig):
    def gender(self,obj=None,is_head=False):
        if is_head:
            return "性别"
        return obj.get_gender_display()

    def education(self,obj=None,is_head=False):
        if is_head:
            return "学历"
        return obj.get_education_display()

    def experience(self,obj=None,is_head=False):
        if is_head:
            return "工作经验"
        return obj.get_experience_display()

    def work_status(self,obj=None,is_head=False):
        if is_head:
            return "职业状态"
        return obj.get_work_status_display()

    def source(self,obj=None,is_head=False):
        if is_head:
            return "客户来源"
        return obj.get_source_display()

    def course(self,obj=None,is_head=False):
        if is_head:
            return "咨询课程"
        course_list = []
        for course_obj in obj.course.all():
            temp = '<span style="border: 1px solid royalblue"><a class="glyphicon glyphicon-remove" href="/haidong/app01/customer/%s/%s/?%s">%s</a></span>'%(obj.id,course_obj.id,self.parm.urlencode(),str(course_obj),)
            course_list.append(temp)
        return mark_safe(",".join(course_list))

    def extr_urls(self):
        app_model_name = (self.model_class._meta.app_label, self.model_class._meta.model_name)
        return [
            url(r'^(\d+)/(\d+)/$',self.wrap(self.diy_delete_view),name="%s_%s_delete"%app_model_name),
            url(r'^public/$',self.wrap(self.public_view),name="%s_%s_public"%app_model_name),
            url(r'^user/$', self.wrap(self.user_view), name="%s_%s_user" % app_model_name),
            url(r'^(\d+)/competition/$', self.wrap(self.competition_view), name="%s_%s_competition" % app_model_name),
            url(r'^single/$', self.wrap(self.single_view), name="%s_%s_single" % app_model_name),
            url(r'^multi/$', self.wrap(self.multi_view), name="%s_%s_multi" % app_model_name),
        ]

    def diy_delete_view(self,request,custome_id,course_id):
        obj = self.model_class.objects.filter(pk=custome_id)[0]
        obj.course.remove(course_id)
        url="%s?%s"%(self.get_list_url(),self.parm[self.url_encode_key])
        return redirect(url)

    def public_view(self,request):
        current_time = datetime.datetime.now().date()
        my_want_time1 = current_time - datetime.timedelta(days=3)
        my_want_time2 = current_time - datetime.timedelta(days=15)
        con = Q()
        c1 = Q()
        c1.connector = 'or'
        c1.children.append(("last_consult_date__lt",my_want_time1))
        c1.children.append(("recv_date__lt",my_want_time2))
        c2 = Q()
        c2.children.append(("status",1))
        con.add(c1,'AND')
        con.add(c2,'AND')
        customer_set = models.Customer.objects.filter(con)
        # customer_set = models.Customer.objects.filter(Q(last_consult_date__lt=my_want_time1)|Q(recv_date__lt=my_want_time2),
        #                                               status=2)
        return render(request,"public.html",{"customer_set":customer_set})

    def user_view(self,request):
        """
                当前登录用户的所有客户
                :param request:
                :return:
                """
        # 去session中获取当前登录用户ID
        current_user_id = 1

        # 当前用户的所有客户列表
        customers = models.ConsultDestribution.objects.filter(consultant_id=current_user_id).order_by('status')
        return render(request, 'user_view.html', {'customers': customers})

    def competition_view(self,request,cid):
        """
        抢单
        :param request:
        :param nid:
        :return:
        """
        current_user_id = 1
        # 修改客户表
        # recv_date
        # last_consult_date
        # consultant
        ctime = datetime.datetime.now().date()
        # 必须原顾问不是自己
        # 状态必须是未报名
        # 3/15天
        # models.Customer.objects.filter(id=cid).
        # update(recv_date=ctime,last_consult_date=ctime,consultant_id=current_user_id)
        ctime = datetime.datetime.now().date()
        no_deal = ctime - datetime.timedelta(days=15)  # 接客
        no_follow = ctime - datetime.timedelta(days=3)  # 最后跟进日期

        row_count = models.Customer.objects.filter(Q(recv_date__lt=no_deal) | Q(last_consult_date__lt=no_follow),
                                                   status=1, id=cid).exclude(consultant_id=current_user_id).update(
            recv_date=ctime, last_consult_date=ctime, consultant_id=current_user_id)
        if not row_count:
            return HttpResponse('手速太慢了')

        models.ConsultDestribution.objects.create(consultant_id=current_user_id, customer_id=cid)

        return HttpResponse('抢单成功')

    def single_view(self,request):
        """
                单条录入客户信息
                :param request:
                :return:
                """

        if request.method == "GET":
            form = SingleModelForm()
            return render(request, 'single_view.html', {'form': form,"config":self})
        else:
            from app01.ass_user import Ass
            form = SingleModelForm(request.POST)
            if form.is_valid():
                sale_id = Ass.get_sale_id()
                if not sale_id:
                    return HttpResponse('无销售，不可分！')
                try:
                    with transaction.atomic():   #事务
                        now_time = datetime.datetime.now().date()
                        form.instance.consultant_id = sale_id
                        form.instance.recv_date = now_time
                        form.instance.last_consult_date = now_time
                        obj = form.save()
                        models.ConsultDestribution.objects.create(customer_id=obj.id,consultant_id=sale_id,date=now_time)
                        #发送消息

                    return HttpResponse('录入成功')
                except Exception as e:
                    Ass.rollback(sale_id)
                    return HttpResponse('录入失败')
            else:
                return render(request, 'single_view.html', {'form': form,"config":self})

    def multi_view(self,request):
        if request.method == 'GET':
            return render(request,'multi.html')
        else:
            from django.core.files.uploadedfile import InMemoryUploadedFile
            file = request.FILES.get('excl')
            file_name, suffix = file.name.rsplit(".")
            if suffix not in ['xlsx','xls']:
                return HttpResponse('格式不对')
            else:
                import xlrd
                workbook = xlrd.open_workbook(file_contents=file.read())
                sheet = workbook.sheet_by_index(0)
                maps = {
                    0: 'name',
                    1: 'qq',
                    2:'gender',
                    3:'course',
                }

                for index in range(1, sheet.nrows):
                    row = sheet.row(index)
                    row_dict = {}
                    for i in range(len(maps)):
                        key = maps[i]
                        cell = row[i]
                        row_dict[key] = cell.value
                    print(row_dict)
                # 自动获取ID
                from app01.ass_user import Ass
                sale_id = Ass.get_sale_id()
                # 录入客户表(咨询课程)
                # 录入客户分配表
                return HttpResponse('上传成功')

    def status(self,obj=None,is_head=False):
        if is_head:
            return "状态"
        return obj.get_status_display()

    def consultrecord(self,obj=None,is_head=False):
        if is_head:
            return "跟进状态"
        return mark_safe('<a href="/haidong/app01/consultrecord/?customer=%s">%s</a>'%(obj.id,"跟进状态"))

    list_display = ["qq","name",gender,education,"graduation_school",experience,
                    source,consultrecord,course,status,"consultant"]

    condition_list = []
    show_search_input = True
    comb_list = [
        sites.PacComb("gender",is_choice=True),
        sites.PacComb("education",is_choice=True,multi=True),
        sites.PacComb("experience",is_choice=True,multi=True),
        sites.PacComb("work_status",is_choice=True),
        sites.PacComb("source",is_choice=True,multi=True),
        sites.PacComb("course",multi=True),
        sites.PacComb("status",is_choice=True),
    ]
    edit_link = ["name"]