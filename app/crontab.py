import datetime
from .models import *
from decouple import config
import requests
from datetime import date, timedelta
from django.db.models import Count, Sum

# 매일 00:00, 01 마다 실행됨

def insert_today():
    # 오늘날짜 row 생성
    new_vc = VisitorCount()
    new_vc.visit_date = datetime.datetime.now().strftime('%Y-%m-%d')
    new_vc.visit_count = 1
    new_vc.save()


def daily_statistics():
    # 통계 날짜
    yesterday = (date.today() - timedelta(1)).strftime('%Y-%m-%d')
    # 총 방문자수
    total_visit = VisitorCount.objects.aggregate(Sum('visit_count'))['visit_count__sum']
    # 총 회원수
    total_user = NewUserInfo.objects.count()
    # 일일 방문자수
    daily_visit = VisitorCount.objects.get(visit_date = yesterday).visit_count
    # 일일 활동회원수
    daily_active = NewUserInfo.objects.filter(last_update_time__contains=yesterday).aggregate(Count('last_update_time'))['last_update_time__count']
    # 일일 가입자수
    daily_signup = NewUserInfo.objects.filter(register_time__contains=yesterday).aggregate(Count('register_time'))['register_time__count']
    # 일일 탈퇴자수
    daily_delete = DeleteAccountLog.objects.filter(delete_time__contains=yesterday).aggregate(Count('delete_time'))['delete_time__count']
    # 강의 총 데이터수
    total_user_data = UserGrade.objects.count()
    # 학번별 회원수
    user_with_snum = ''
    for row in NewUserInfo.objects.values_list('year').annotate(count=Count('year')):
        user_with_snum += str(row[0]) + "학번 - " + str(row[1]) + " 명\n"
    # 학과별 회원수
    user_with_major = ''
    for row in sorted(NewUserInfo.objects.values_list('major').annotate(count=Count('major')), key=lambda x: x[1], reverse=True):
        user_with_major +=  str(row[0]) + " - " + str(row[1]) + " 명\n"

    # 가입자/탈퇴자수 저장
    vc_qs = VisitorCount.objects.get(visit_date = yesterday)
    vc_qs.user_count = total_user
    vc_qs.signup_count = daily_signup
    vc_qs.delete_count = daily_delete
    vc_qs.save()

    # Slack 알림
    url = config('SLACK_WEBHOOK_URL_ALARM')
    context = {
        "blocks": [
            {
			    "type": "section",
			    "text": {
			    	"type": "mrkdwn",
			    	"text": "*🚀" + yesterday + " 통계*"
			    }
		    },
            {
			    "type": "divider"
		    },
	    	{
               
	    		"type": "section",
	    		"fields": [
                    {
	    				"type": "mrkdwn",
	    				"text": "*▪ 총 방문자 수 :*\n" + str(total_visit) + " 명"
	    			},
                    {
	    				"type": "mrkdwn",
	    				"text": "*▪ 총 회원 수 :*\n" + str(total_user) + " 명"
	    			},
	    			{
	    				"type": "mrkdwn",
	    				"text": "*▪ 일일 방문자 수 :*\n" + str(daily_visit) + " 명"
	    			},
                    {
	    				"type": "mrkdwn",
	    				"text": "*▪ 일일 활동 회원 수 :*\n" + str(daily_active) + " 명"
	    			},
	    			{
	    				"type": "mrkdwn",
	    				"text": "*▪ 일일 가입자 수 :*\n" + str(daily_signup) + " 명"
	    			},
	    			{
	    				"type": "mrkdwn",
	    				"text": "*▪ 일일 탈퇴자 수 :*\n" + str(daily_delete) + " 명"
	    			},
                    {
	    				"type": "mrkdwn",
	    				"text": "*▪ 강의 총 데이터 수 :*\n" + str(total_user_data) + " 개"
	    			},
	    		]
	    	},
            {
			    "type": "divider"
		    },
            {
               
	    		"type": "section",
	    		"fields": [
                    {
	    				"type": "mrkdwn",
	    				"text": "*▪ 학번별 회원수 :*\n" + user_with_snum
	    			},
                   {
	    				"type": "mrkdwn",
	    				"text": "*▪ 학과별 회원수 :*\n" + user_with_major
	    			},
                   
	    		]
	    	},
	    ]
    }
    requests.post(url=url, json=context)


def test():
    print('hi')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_tt = TestTable()
    new_tt.text = now
    new_tt.save()