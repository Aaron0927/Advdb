# coding:utf-8
from django.http import HttpResponse, HttpResponseRedirect
#from django.template import loader,Context  #导入模板中的loader,Context
from django.shortcuts import render_to_response, get_object_or_404
from home.models import Student, Report, Comment, Class, Board
from django import forms
from django.template import RequestContext
from django.db.models import Avg
import memcache
mc = memcache.Client(['127.0.0.1:11211'])

import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )


# Create your views here.

#登录表单
class LoginForm(forms.Form):
    s_id = forms.CharField(label='学号', max_length=10)
    s_passwd = forms.CharField(label='密码', widget=forms.PasswordInput())


#注册表单
class RegistForm(forms.Form):
    s_id = forms.CharField(label='学号', max_length=10)
    s_name = forms.CharField(label='姓名', max_length=20)
    s_passwd = forms.CharField(label='密码', widget=forms.PasswordInput())
    s_email = forms.EmailField(label='邮箱', max_length=30)
    s_age = forms.CharField(label='年龄', max_length=10)
    #s_gender = forms.性别暂时不做


#报告题目表单
class TitleForm(forms.Form):
    t_title = forms.CharField(label='我的报告题目', max_length=50)


#打分表单
class ScoreForm(forms.Form):
    s_score = forms.CharField(label='分数', max_length=10)
    s_reason = forms.CharField(label='原因', max_length=200)


#注册
def regist(req):
    flag = 1  #等于0表示用户已经存在,2表示班级不存在，1表示正常，可以申请
    if req.method == 'POST':
        s_id = req.POST.get('s_id')
        s_name = req.POST.get('s_name')
        s_passwd = req.POST.get('s_passwd')
        s_email = req.POST.get('s_email')
        s_class = req.POST.get('s_class')
        if s_id and s_name and s_passwd and s_email:
            if Student.objects.filter(s_id=s_id):  #用户已经存在
                flag = 0
                return render_to_response('regist.html', {'flag': flag})
            elif s_name == 'admin':
                Student.objects.create(s_id=s_id, s_name=s_name, s_passwd=s_passwd, s_email=s_email)
                #注册成功，跳转home页面
                response = HttpResponseRedirect('/home/' + s_id)
                #将s_id写入浏览器cookie,失效时间为3600
                response.set_cookie('s_id', s_id, 3600)
                response.set_cookie('s_class', s_class, 3600)
                return response
            elif Class.objects.filter(c_name=s_class):  #班级已经存在
                stu = Student.objects.create(s_id=s_id, s_name=s_name, s_passwd=s_passwd, s_email=s_email)
                cla = Class.objects.filter(c_name=s_class)  #在学生中添加班级
                #这里默认是得到的是一个集合，但我们集合中只有一个元素，所以我们添加时直接取它的第一个元素
                stu.s_class.add(cla[0])
                #注册成功，跳转home页面
                response = HttpResponseRedirect('/home/' + s_id)
                #将s_id写入浏览器cookie,失效时间为3600
                response.set_cookie('s_id', s_id, 3600)
                return response

            elif s_class == '':
                flag = 3 #不能为空
                return render_to_response('regist.html', {'flag': flag})
            else:
                flag = 2  #班级不存在
                return render_to_response('regist.html', {'flag': flag})

    else:
        return render_to_response('regist.html', {'flag': flag}, context_instance=RequestContext(req))

#注册或登录成功后的主页
def home(req, id):

    s_id = req.COOKIES.get('s_id', '')
    sess = req.session.get(s_id)
    flag = 2  #0表示报告已经存在，1表示添加成功,2表示第一次访问
    s_class = req.COOKIES.get('s_class', '')  #只在首页显示我的第一个班级，其他班级用“我的班级”查看
    Cla = Class.objects.filter(c_name__exact=s_class)[0]

    if Cla.board_set.count() == 0:#这个班级还没有公告
        newest_board = ''
    else:
        newest_board = Cla.board_set.all()[Cla.board_set.count() - 1]#得到最新公告
    if req.method == 'POST':
        t_title = req.POST.get('r_title')
        if t_title:
            #查看该学生的相同主题的报告是否已经做过
            report = Report.objects.filter(r_title__exact=t_title, r_id__exact=s_id)
            if report:  #报告已经存在
                reports = Report.objects.all()  #获取当前提交的所有报告
                #已经评分的报告,注意这里的reported和reporting的对象类型不一样

                reported = Comment.objects.filter(c_commenter__exact=s_id)

                #我已经提交的报告
                my_report = reports.filter(r_id__exact=s_id)

                #没有评论的报告，这里用exclude(),和in,用循环将所有报告中的不符合条件的一个一个剔除
                reporting = reports
                for re in reported:
                    reporting = reporting.exclude(id__exact=re.c_report.id)
                #还要把自己的报告去掉，不能对自己的报告评分
                reporting = reporting.exclude(r_id__exact=s_id)
                flag = 0
                return render_to_response('home.html', {'sess': sess, 'newest_board': newest_board, 's_id': s_id,
                                                        's_class': s_class, 'reported': reported,
                                                        'reporting': reporting, 'my_report': my_report, 'flag': flag})
            else:  #创建这个报告
                stu = Student.objects.get(s_id=s_id)
                Report.objects.create(r_title=t_title, r_id=s_id, r_reporter=stu.s_name)
                #我提交的报告
                sql1 = 'select * from home_student as s,home_report as r,home_student_s_class as c '
                sql2 = 'where s.s_id = r.r_id and s.id = c.student_id and  c.class_id =\"'
                sql3 = s_class + '\" and r.r_id = \"' + s_id + '\"'
                my_report = Report.objects.raw(sql1 + sql2 + sql3)

                #已经评分的报告
                sql1 = 'select * from home_student as s,home_report as r,home_student_s_class as c, home_comment as m '
                sql2 = 'where s.s_id = r.r_id and s.id = c.student_id and  c.class_id =\"'
                sql3 = s_class + '\" and r.r_agree = True and m.c_commenter = \"' + s_id + '\" and m.c_report_id = r.id'
                sql_reported = sql1 + sql2 + sql3
                reported = Report.objects.raw(sql_reported)

                #待评分报告
                sql0 = 'select r.id from home_student as s,home_report as r,home_student_s_class as c, home_comment as m '
                sql_reported = sql0 + sql2 + sql3
                sql1 = 'select r.id from home_student as s,home_report as r,home_student_s_class as c '
                sql2 = 'where s.s_id = r.r_id and r.r_id != \"' + s_id + '\" and s.id = c.student_id and  c.class_id =\"'
                sql3 = s_class + '\" and r.r_agree = True'
                sql_reporte = sql1 + sql2 + sql3
                #select 嵌套查询
                sql1 = 'select * from ' + '(' + sql_reporte + ') as A '
                sql2 = 'where A.id not in (' + sql_reported + ')'
                reporting = Report.objects.raw(sql1 + sql2)  #这里获得了这个班所有要评价的报告
                flag = 1
                mc.set("my_report", my_report)
                mc.set("reported", reported)
                mc.set("reporting", reporting)
                return render_to_response('home.html',
                                          {'sess': sess, 'newest_board': newest_board, 's_id': s_id, 's_class': s_class,
                                           'reported': reported, 'reporting': reporting, 'my_report': my_report,
                                           'flag': flag})

        #####搜索提交#####
        if req.method == 'POST':  # 用户已经提交表单
            admin_search = req.POST.get('student_search')
            response = HttpResponseRedirect('/home/search/')
            response.set_cookie('student_search', admin_search, 3600)
            return response
        #####end#######
    else:
        if mc.get("my_report1") and mc.get("reported") and mc.get("reporting"):#memcache中已经缓存了数据
            my_report = mc.get("my_report")
            reported = mc.get("reported")
            reporting = mc.get("reporting")
        else:
            # 我提交的报告
            sql1 = 'select * from home_student as s,home_report as r,home_student_s_class as c '
            sql2 = 'where s.s_id = r.r_id and s.id = c.student_id and  c.class_id =\"'
            sql3 = s_class + '\" and r.r_id = \"' + s_id + '\"'
            my_report = Report.objects.raw(sql1 + sql2 + sql3)

            # 已经评分的报告
            sql1 = 'select * from home_student as s,home_report as r,home_student_s_class as c, home_comment as m '
            sql2 = 'where s.s_id = r.r_id and s.id = c.student_id and  c.class_id =\"'
            sql3 = s_class + '\" and r.r_agree = True and m.c_commenter = \"' + s_id + '\" and m.c_report_id = r.id'
            sql_reported = sql1 + sql2 + sql3
            reported = Report.objects.raw(sql_reported)

            #待评分报告
            sql0 = 'select r.id from home_student as s,home_report as r,home_student_s_class as c, home_comment as m '
            sql_reported = sql0 + sql2 + sql3
            sql1 = 'select r.id from home_student as s,home_report as r,home_student_s_class as c '
            sql2 = 'where s.s_id = r.r_id and r.r_id != \"' + s_id + '\" and s.id = c.student_id and  c.class_id =\"'
            sql3 = s_class + '\" and r.r_agree = True'
            sql_reporte = sql1 + sql2 + sql3
            #select 嵌套查询
            sql1 = 'select * from ' + '(' + sql_reporte + ') as A '
            sql2 = 'where A.id not in (' + sql_reported + ')'

            reporting = Report.objects.raw(sql1 + sql2)  #这里获得了这个班所有要评价的报告

            #mc.set("my_report", my_report)
            #mc.set("reported", reported)
            #mc.set("reporting", reporting)
        return render_to_response('home.html',
                                  {'sess': sess, 'newest_board': newest_board, 's_id': s_id,
                                   'reported': reported,
                                   'reporting': reporting, 'my_report': my_report, 'flag': flag, 's_class': s_class})


#登录页面
def login(req):
    if req.method == 'POST':  #用户已经提交表单
        s_id = req.POST.get('stuID')
        s_passwd = req.POST.get('passwd')
        if s_id and s_passwd:
            #获取的表单数据与数据库进行比较
            user = Student.objects.filter(s_id__exact=s_id, s_passwd__exact=s_passwd)
            if user:  #比较成功，跳转home
                response = HttpResponseRedirect('/home/' + s_id)  #跳转主页
                #将username写入浏览器cookie,失效时间为3600
                response.set_cookie('s_id', s_id, 3600)
                if(Class.objects.count() == 0):#还没有创建班级
                    s_class = ""
                else:
                    s_class = Class.objects.all()[0]#显示第一个班级

                if s_id != 'admin':
                    s_class = user[0].s_class.all()[0]  #学生肯定属于一个班级
                response.set_cookie('s_class', s_class, 3600)
                return response
            else:  #比较失败，还在login
                return HttpResponseRedirect('/login/')
    else:
        return render_to_response('login.html', {}, context_instance=RequestContext(req))


#评论评分,id是url部分传过来的
def comment(req, id):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    class_sets = Class.objects.all()
    if req.method == 'POST':  #用户已经提交表单
        s_score = req.POST.get('c_score')
        s_reason = req.POST.get('c_reason')
        if s_score and s_reason:  #绑定的数据有效
            report = get_object_or_404(Report, pk=int(id))
            #获取的表单数据与数据库进行比较
            Comment.objects.create(c_commenter=s_id, c_score=s_score, c_reason=s_reason,
                                   c_report=report)
            return HttpResponseRedirect('/home/' + s_id)
    else:
        report = get_object_or_404(Report, pk=int(id))
        #		sf = ScoreForm()
        return render_to_response('comment.html',
                                  {'class_sets': class_sets, 'report': report, 's_id': s_id, 's_class': s_class},
                                  context_instance=RequestContext(req))


#显示我已经评分的页面
def show_comment(req, id):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    comment = get_object_or_404(Comment, pk=int(id))
    class_sets = Class.objects.all()
    return render_to_response('show_comment.html',
                              {'class_sets': class_sets, 'comment': comment, 's_id': s_id, 's_class': s_class},
                              context_instance=RequestContext(req))


#显示我提交report的评分
def my_report(req, id):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    report = get_object_or_404(Report, pk=int(id))
    comment_set = report.comment_set.all()
    class_sets = Class.objects.all()
    num = comment_set.count()  #已经有多少人评分了
    avg = comment_set.aggregate(Avg('c_score'))
    return render_to_response('my_report.html',
                              {'class_sets': class_sets, 'report': report, 'comment_set': comment_set, 'num': num,
                               'avg': avg, 's_id': s_id, 's_class': s_class})


#老师管理后台(用于参数返回)
def admin(req, id):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    #####搜索提交#####
    if req.method == 'POST':  # 用户已经提交表单
        admin_search = req.POST.get('admin_search')
        response = HttpResponseRedirect('/admin/search/')
        response.set_cookie('admin_search', admin_search, 3600)
        return response
    #####end#######

    if mc.get("class_sets") and mc.get("stu"):#memcache中已经缓存了数据
        class_sets = mc.get("class_sets")
        stu = mc.get("stu")
    else:
        class_sets = Class.objects.all()
        #所有学生
        stu = Student.objects.exclude(s_id__exact=s_id)
        mc.set("class_sets", class_sets)
        mc.set("stu", stu)


    #待审核报告

    #for s in stu:
    agring = Report.objects.filter(r_agree__exact=False)

    #已审核报告
    #for s in stu:
    agreed = Report.objects.filter(r_agree__exact=True)
    report = get_object_or_404(Report, pk=int(id))
    report.r_agree = True
    report.save()

    return render_to_response('admin.html',
                              {'stu': stu, 'class_sets': class_sets, 'agring': agring, 'agreed': agreed, 's_id': s_id,
                               's_class': s_class})


#老师管理后台
def admin_home(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    #####搜索提交#####
    if req.method == 'POST':  # 用户已经提交表单
        admin_search = req.POST.get('admin_search')
        response = HttpResponseRedirect('/admin/search/')
        response.set_cookie('admin_search', admin_search, 3600)
        return response
    #####end#######

    if mc.get("class_sets") and mc.get("stu") and mc.get("agring") and mc.get("agreed"):#memcache中已经缓存了数据
        class_sets = mc.get("class_sets")
        stu = mc.get("stu")
        agring = mc.get("agring")
        agreed = mc.get("agreed")
    else:
        class_sets = Class.objects.all()
        #所有学生
        stu = Student.objects.exclude(s_id__exact=s_id)
        #待审核报告
        agring = Report.objects.filter(r_agree__exact=False)
        #已审核报告
        agreed = Report.objects.filter(r_agree__exact=True)
        mc.set("class_sets", class_sets)
        mc.set("stu", stu)
        mc.set("agring", agring)
        mc.set("agreed", agreed)
    return render_to_response('admin.html',
                              {'stu': stu, 'agring': agring, 'agreed': agreed, 's_id': s_id, 'class_sets': class_sets,
                               's_class': s_class})


#老师查看报告情况
def admin_report(req, id):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    class_sets = Class.objects.all()
    report = get_object_or_404(Report, pk=int(id))
    comment_set = report.comment_set.all()
    class_sets = Class.objects.all()
    num = comment_set.count()  #已经有多少人评分了
    avg = comment_set.aggregate(Avg('c_score'))
    return render_to_response('admin_report.html',
                              {'class_sets': class_sets, 'report': report, 'comment_set': comment_set, 'num': num,
                               'avg': avg, 's_id': s_id, 's_class': s_class})


#创建班级
def add_class(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    flag = 0  #0不存在,1表示已经存在
    if req.method == 'POST':  #用户已经提交表单
        c_name = req.POST.get('c_name')
        if c_name:  #绑定的数据有效
            if Class.objects.filter(c_name__exact=c_name):  #教室已经存在
                flag = 1
            else:  #教室不存在
                Class.objects.create(c_name=c_name)
            class_sets = Class.objects.all()  #更新当前班级标签

            if(Class.objects.count() == 1):#创建的第一个班级，需要修改右上角的当前班级标题，将当前班级加到缓存中去
                s_class = Class.objects.all()[0]
            response = render_to_response('add_class.html',
                                          {'flag': flag, 's_id': s_id, 'class_sets': class_sets, 's_class': s_class})

            response.set_cookie('s_class',s_class)

            return response

    else:
        class_sets = Class.objects.all()
        return render_to_response('add_class.html', {'s_id': s_id, 'class_sets': class_sets, 's_class': s_class})


#发布公告
def give_board(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    flag = 0
    class_sets = Class.objects.all()
    if req.method == 'POST':  #用户已经提交表单
        b_title = req.POST.get('b_title')
        b_content = req.POST.get('b_content')
        if b_title and b_content:  #绑定的数据有效
            flag = 1
            cla = Class.objects.filter(c_name__exact=s_class)[0]
            Board.objects.create(b_title=b_title, b_content=b_content, b_class=cla)
            return render_to_response('give_board.html',
                                      {'class_sets': class_sets, 's_id': s_id, 'flag': flag, 's_class': s_class})

    else:
        return render_to_response('give_board.html',
                                  {'s_id': s_id, 's_class': s_class, 'flag': flag, 'class_sets': class_sets})


#显示我的历史公告
def my_board_history(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    board_set = Board.objects.filter(b_class_id__exact=s_class)

    return render_to_response('my_board_history.html', {'board_set': board_set, 's_id': s_id, 's_class': s_class})


#显示admin历史公告
def admin_board_history(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    board_set = Board.objects.filter(b_class_id__exact=s_class)

    return render_to_response('admin_board_history.html', {'board_set': board_set, 's_id': s_id, 's_class': s_class})


#我的班级
def my_class(req, cla):
    s_id = req.COOKIES.get('s_id', '')
    response = HttpResponseRedirect('/home/' + s_id)  #跳转主页
    response.set_cookie('s_class', cla, 3600)
    return response


#点名
def call(req, id):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')

    call_stu = Student.objects.filter(id__exact=id)[0].s_id
    req.session.set_expiry(60)  #后面接整数,以秒为单位
    req.session[call_stu] = call_stu

    stu = Student.objects.exclude(s_id__exact=s_id)
    stu1 = stu
    flag = 1#1表示还有人要i点  0表示点完了
    for s in stu1:
        if req.session.get(s.s_id):
            stu = stu.exclude(s_id__exact=s.s_id)
    if stu:  #不是空的
        return render_to_response('call.html', {'stu': stu, 's_id': s.s_id, 's_class': s_class, 'flag':flag})
    else:
        flag = 0
        return render_to_response('call.html', {'s_id': s.s_id, 's_class': s_class, 'flag':flag})


#点名
def call_home(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    stu = Student.objects.exclude(s_id__exact=s_id)
    stu1 = stu
    flag = 1#1表示还有人要i点  0表示点完了
    for s in stu1:
        if req.session.get(s.s_id):
            stu = stu.exclude(s_id__exact=s.s_id)
    if stu:
        return render_to_response('call.html', {'stu': stu, 's_id': s_id, 's_class': s_class,'flag':flag})
    else:
        flag = 0
        return render_to_response('call.html', {'stu': stu, 's_id': s_id, 's_class': s_class,'flag':flag})
#设置
def setting(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    flag = 0#0表示完成修改，1表示两次密码不一样
    if req.method == 'POST':  #用户已经提交表单
        passwd1 = req.POST.get('passwd1')
        passwd2 = req.POST.get('passwd2')
        if passwd1 == passwd2:  #绑定的数据有效
            Student.objects.filter(s_id__exact=s_id).update(s_passwd=passwd1)
            return render_to_response('setting.html',{'s_id': s_id, 'flag': flag, 's_class': s_class})
        else:
            flag = 1
            return render_to_response('setting.html',{'s_id': s_id, 'flag': flag, 's_class': s_class})

    else:
        return render_to_response('setting.html', {'s_id': s_id, 's_class': s_class})

#设置
def admin_setting(req):
    s_id = req.COOKIES.get('s_id', '')
    s_class = req.COOKIES.get('s_class', '')
    flag = 0#0表示完成修改，1表示两次密码不一样
    if req.method == 'POST':  #用户已经提交表单
        passwd1 = req.POST.get('passwd1')
        passwd2 = req.POST.get('passwd2')
        if passwd1 == passwd2:  #绑定的数据有效
            Student.objects.filter(s_id__exact=s_id).update(s_passwd=passwd1)
            return render_to_response('admin_setting.html',{'s_id': s_id, 'flag': flag, 's_class': s_class})
        else:
            flag = 1
            return render_to_response('admin_setting.html',{'s_id': s_id, 'flag': flag, 's_class': s_class})

    else:
        return render_to_response('admin_setting.html', {'s_id': s_id, 's_class': s_class})

# 搜索
def search(req):
    s_id = req.COOKIES.get('s_id', '')
    admin_search = req.COOKIES.get('admin_search')
    student_search = req.COOKIES.get('student_search')
    s_class = req.COOKIES.get('s_class', '')
    if admin_search:
        users = Student.objects.filter(s_name__icontains=admin_search)  # 查找所有用户
        reports = Report.objects.filter(r_title__icontains=admin_search)  # 所有报告题目
        boards = Board.objects.filter(b_content__icontains=admin_search)
        return render_to_response('admin_search.html',
                                  {'s_id': s_id, 's_class':s_class, 'users': users, 'reports': reports, 'boards': boards})
    else:
        users = Student.objects.filter(s_name__icontains=student_search)  # 查找所有用户
        reports = Report.objects.filter(r_title__icontains=student_search)  # 所有报告题目
        boards = Board.objects.filter(b_content__icontains=student_search)
        return render_to_response('search.html',
                                  {'s_id': s_id, 's_class':s_class, 'users': users, 'reports': reports, 'boards': boards})


