#coding:utf-8
from django.db import models
# Create your models here.

#班级
class Class(models.Model):
    c_name = models.CharField(max_length = 50, primary_key=True)#班级名字
    c_time = models.DateTimeField(auto_now_add = True)#班级创建时间

    def __unicode__(self):
        return self.c_name

#从父类Model继承过来
class Student(models.Model):
    s_id = models.CharField(max_length = 10)    
    s_name = models.CharField(max_length = 20)
    s_passwd = models.CharField(max_length = 30)
    s_email = models.EmailField(max_length = 30)
    s_age = models.CharField(max_length = 10)
    s_gender = models.CharField(max_length = 5)
    s_call = models.DateTimeField(auto_now =  True)#用于点名时保存时间,每次save都会更新
    s_class = models.ManyToManyField(Class)#对于高级数据库这门可来说class是对不同学期而言的，
    #一个学生只能属于一班，他总共只能修一次这个课，后来考虑要是这个同学挂了，重修又会进来，
    #所以还是多对多的关系


    def __unicode__(self):
        return self.s_name
"""
#点赞类
class Like(models.Model):
    l_id = models.CharField(max_length = 10)#一个赞是一个学生的
    l_yes_or_not = models.BooleanField(default = False)
    l_comment_title = models.CharField(max_length = 50)
    def __unicode__(self):
        return '赞'
"""
#报告表
class Report(models.Model):
	r_title = models.CharField(max_length = 50)#标题
	r_reporter = models.CharField(max_length = 20)#报告者
	r_id = models.CharField(max_length = 10)#报告者学号
	r_time = models.DateTimeField(auto_now_add = True)#报告提交时间
	r_agree = models.BooleanField(default = False)#是否已经通过老师审核
	r_comment_num = models.CharField(max_length = 10)#已经收到评分数目
	r_agree_num = models.CharField(max_length = 10)#已经有多少人点赞
	r_average = models.CharField(max_length = 10)#平均分

#评分表
class Comment(models.Model):
	c_report = models.ForeignKey(Report)#一个报告会有多个评分表
	c_commenter = models.CharField(max_length = 10)#评分者id学号
	c_score = models.CharField(max_length = 10)#分数
	c_reason = models.CharField(max_length = 200)#原因
	c_like = models.BooleanField(default = False)#是否点赞



#公告版
class Board(models.Model):
    b_title = models.CharField(max_length = 50)
    b_content = models.CharField(max_length = 100)
    b_time = models.DateTimeField(auto_now_add = True)  
    b_class = models.ForeignKey(Class)#一个班级可以由多个公告
