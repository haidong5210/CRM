import json
from tobacco.server import sites
from app01 import models
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import redirect,HttpResponse,render
from django.urls import reverse
from django.forms import ModelForm
from app01.basepermission import BasePermission



class UserInfoConfig(BasePermission,sites.TobaccoConfig):
    list_display = ["id","name","username","email","depart"]
    comb_list = [
        sites.PacComb("depart",val_func_name=lambda x:str(x.code))
    ]
    edit_link = ["name"]
    show_search_input = True
    condition_list = ["name__contains"]
    # catch_list = []
    # show_catch = True
sites.site.register(models.UserInfo,UserInfoConfig)


class DepartmentConfig(sites.TobaccoConfig):
    list_display = ["id","title","code"]
sites.site.register(models.Department,DepartmentConfig)


class CourseConfig(sites.TobaccoConfig):
    list_display = ["id","name"]
sites.site.register(models.Course,CourseConfig)


class SchoolConfig(sites.TobaccoConfig):
    list_display = ["id","title"]
sites.site.register(models.School,SchoolConfig)


class ClassListConfig(sites.TobaccoConfig):

    def teachers(self,obj=None,is_head=False):
        if is_head:
            return "任课老师"
        l = []
        for name in obj.teachers.all():
            l.append(str(name))
        return ",".join(l)

    def course_semester(self,obj=None,is_head=False):
        if is_head:
            return "课程"
        return "%s(%s期)"%(str(obj.course),str(obj.semester))

    def cls_num(self,obj=None,is_head=False):
        if is_head:
            return "班级人数"
        return obj.student_set.all().count()
    list_display = ["id","school",course_semester,cls_num,"price","start_date","graduate_date","memo",teachers,"tutor"]
    edit_link = [course_semester,]
sites.site.register(models.ClassList,ClassListConfig)


class SingleModelForm(ModelForm):
    class Meta:
        model = models.Customer
        exclude = ['consultant','status','recv_date','last_consult_date']


from configs.customer import CustomerConfig
sites.site.register(models.Customer,CustomerConfig)


class ConsultRecordConfig(sites.TobaccoConfig):
    list_display = ["customer","note","consultant"]
    comb_list = [
        sites.PacComb("customer")
    ]
sites.site.register(models.ConsultRecord,ConsultRecordConfig)


class CourseRecordConfig(sites.TobaccoConfig):
    def admin_Record(self,obj=None,is_head=False):
        if is_head:
            return '管理记录'
        return mark_safe('<a href="/haidong/app01/studyrecord/?course_record=%s">考勤管理</a>'%obj.pk)

    def extr_urls(self):
        app_model_name = (self.model_class._meta.app_label, self.model_class._meta.model_name)
        urls = [
            url(r'^(\d+)/score/$', self.wrap(self.score_view), name="%s_%s_score" % app_model_name),
        ]
        return urls

    def score_view(self,request,cid):
        if request.method == "GET":
            from django.forms import Form,fields,widgets
            studyrecord_set = models.StudyRecord.objects.filter(course_record_id=cid)
            data = []
            for obj in studyrecord_set:
                TempForm = type("TempForm",(Form,),{
                    'score_%s'%obj.pk:fields.ChoiceField(choices=models.StudyRecord.score_choices),
                    'homework_note_%s'%obj.pk:fields.CharField(widget=widgets.Textarea(attrs={"cols":"40",
                                                                                              "rows":"2"}))
                })
                data.append({"obj":obj,"form":TempForm(initial={'score_%s'%obj.pk:obj.score,'homework_note_%s'%obj.pk:obj.homework_note})})
            return render(request,"score.html",{"data":data})
        else:
            data_dict = {}
            for key,value in request.POST.items():
                if key == "csrfmiddlewaretoken":
                    continue
                name,sid = key.rsplit("_",1)
                if sid in data_dict:
                    data_dict[sid][name] = value
                else:
                    data_dict[sid]={name:value}
            for id,data in data_dict.items():
                models.StudyRecord.objects.filter(id=id).update(**data)
            return redirect('/haidong/app01/courserecord/')

    def score_list(self,obj=None,is_head=False):
        """
        录入成绩
        :param obj:
        :param is_head:
        :return:
        """
        if is_head:
            return '成绩录入'
        url = reverse('tobacco:app01_courserecord_score',args=(obj.pk,))
        return mark_safe("<a href='%s'>录入成绩</a>"%url)
    list_display = ["class_obj","day_num","teacher",admin_Record,score_list]
    show_catch = True
    #初始化的操作
    def del_catch(self, request):
        id_list = request.POST.getlist("pk")
        for courserecord_id in id_list:
            courserecord_obj = models.CourseRecord.objects.filter(pk=courserecord_id).first()
            for student_obj in courserecord_obj.class_obj.student_set.all():
                print(student_obj)
                is_exist = models.StudyRecord.objects.filter(course_record_id=courserecord_id,student=student_obj).exists()
                if not is_exist:
                    models.StudyRecord.objects.create(course_record_id=courserecord_id,student=student_obj)
                else:
                    continue
    del_catch.text = "批量初始化"
    catch_list = [del_catch]
sites.site.register(models.CourseRecord,CourseRecordConfig)


class StudentConfig(BasePermission,sites.TobaccoConfig):
    def class_list(self,obj=None,is_head=False):
        if is_head:
            return "已报班级"
        result=[]
        for cls_obj in obj.class_list.all():
            name = '%s(%s)'%(cls_obj.course,cls_obj.semester)
            result.append(name)
        return ",".join(result)

    def extr_urls(self):
        app_model_name = (self.model_class._meta.app_label, self.model_class._meta.model_name)
        urls = [
            url(r'^(\d+)/showc/$', self.wrap(self.showc), name="%s_%s_showc" % app_model_name),
            url(r'^dis/$', self.wrap(self.dis), name="%s_%s_dis" % app_model_name),
        ]
        return urls

    def dis(self,request):
        cls_id = request.GET.get("cls_id")
        stu_id = request.GET.get("stu_id")
        result = []
        score_set = models.StudyRecord.objects.filter(course_record__class_obj_id=cls_id,student_id=stu_id).order_by('course_record_id')
        for score_obj in score_set:
            l = []
            day = "day%s"%score_obj.course_record.day_num
            l.append(day)
            l.append(score_obj.score)
            result.append(l)
        return HttpResponse(json.dumps(result))

    def show_score(self,obj=None,is_head=False):
        if is_head:
            return "查看成绩"
        url=reverse('tobacco:app01_student_showc',args=(obj.id,))
        return mark_safe("<a href='%s'>查看成绩</a>"%url)

    def showc(self,request,sid):
        if request.method == "GET":
            cls_set = models.ClassList.objects.filter(student__id=sid)
            return render(request,"show_score.html",{"cls_set":cls_set,"sid":sid})
    list_display = ["customer",class_list,show_score]
    edit_link = ["customer"]
sites.site.register(models.Student,StudentConfig)


class StudyRecordConfig(sites.TobaccoConfig):

    def record(self,obj=None,is_head=False):
        if is_head:
            return '上课记录'
        return obj.get_record_display()
    list_display = ["course_record",'student','score',record]

    def checked(self,request):
        sid_list = request.POST.getlist("pk")
        models.StudyRecord.objects.filter(id__in =sid_list).update(record="checked")
    checked.text = '已签到'

    def vacate(self,request):
        sid_list = request.POST.getlist("pk")
        models.StudyRecord.objects.filter(id__in=sid_list).update(record="vacate")
    vacate.text = '请假'

    def late(self,request):
        sid_list = request.POST.getlist("pk")
        models.StudyRecord.objects.filter(id__in=sid_list).update(record="late")
    late.text = '迟到'

    def noshow(self, request):
        sid_list = request.POST.getlist("pk")
        models.StudyRecord.objects.filter(id__in=sid_list).update(record="noshow")
    noshow.text = '缺勤'

    def leave_early(self, request):
        sid_list = request.POST.getlist("pk")
        models.StudyRecord.objects.filter(id__in=sid_list).update(record="leave_early")
    leave_early.text = '早退'
    catch_list = [checked,vacate,late,noshow,leave_early]
    show_catch = True
    comb_list = [
        sites.PacComb('course_record')
    ]
    show_add_btn = False
    # edit_link = ['course_record']
sites.site.register(models.StudyRecord,StudyRecordConfig)

