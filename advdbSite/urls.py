# coding:utf-8
from django.conf.urls import patterns, include, url
from home.views import login, regist, home, comment, show_comment, admin, my_report, admin_home
from home.views import admin_report, add_class, give_board, my_board_history, admin_board_history
from home.views import call, call_home,setting,search,admin_setting
# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('home.views',
                       # Examples:
                       # url(r'^$', 'advdbSite.views.home', name='home'),
                       # url(r'^advdbSite/', include('advdbSite.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       # url(r'^admin/', include(admin.site.urls)),  #url(r'^$', 'home.views.index'),#后面是对应views中的视图处理函数
                       #url(r'^home/\d{2}/$','index'),#在浏览器中任意加入两个数字也是可以的
                       #对正则表达式中分组的应用，我们传递了一个参数叫id，参数是两位数的方式，传递给了index
                       url(r'^regist/$', 'regist'),
                       url(r'^login/$', 'login'),
                       url(r'^$', 'login'),
                       url(r'^home/(?P<id>\d+)/$', 'home'),
                       url(r'^comment/(?P<id>\d+)/$', 'comment'),  #会把评分唯一的id传回去
                       url(r'^showcomment/(?P<id>\d+)/$', 'show_comment'),
                       url(r'^myreport/(?P<id>\d+)/$', 'my_report'),
                       url(r'^home/admin/(?P<id>\d+)/$', 'admin'),
                       url(r'^home/admin/$', 'admin_home'),
                       url(r'^admin/reports/(?P<id>\d+)/$', 'admin_report'),
                       url(r'^admin/add_class/$', 'add_class'),
                       url(r'^admin/give_board/$', 'give_board'),
                       url(r'^admin/board_history/&', 'admin_board_history'),
                       url(r'^home/board_history/$', 'my_board_history'),
                       url(r'^admin/call/(?P<id>\d+)/$', 'call'),
                       url(r'^admin/call/$', 'call_home'),

                       url(r'^admin/search/$', 'search'),
                       url(r'^home/search/$', 'search'),
                       url(r'^admin/setting/$', 'admin_setting'),
                       url(r'^home/setting/$', 'setting'),

)



