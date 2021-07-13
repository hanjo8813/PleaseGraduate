
import os
from uuid import uuid4
from django.db import models
from django.utils import timezone

# DB 테이블의 구조를 파이썬 클래스로 보여주고, 수정가능

# 테스트용 테이블

class TestTable(models.Model):
    num = models.AutoField(primary_key=True)
    text = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'test_table'
        

class TestAllLecture(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)
    subject_name = models.CharField(max_length=70)
    classification = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'test_all_lecture'


class TestNewLecture(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)

    class Meta:
        managed = False
        db_table = 'test_new_lecture'


class NewUserInfo(models.Model):
    last_update_time = models.CharField(max_length=45, blank=True, null=True)
    register_time = models.CharField(max_length=45, blank=True, null=True)
    student_id = models.CharField(primary_key=True, max_length=10)
    password = models.CharField(max_length=100)
    year = models.IntegerField()
    major = models.CharField(max_length=45)
    major_status = models.CharField(max_length=10)
    name = models.CharField(max_length=45)
    book = models.CharField(max_length=45)
    eng = models.CharField(max_length=45)
    mypage_json = models.JSONField(blank=True, null=True)
    result_json = models.JSONField(blank=True, null=True)
    en_result_json = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'new_user_info'

# ---------------------------------------------------------------------------

class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

class VisitorCount(models.Model):
    visit_date = models.CharField(primary_key=True, max_length=45)
    visit_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'visitor_count'

class MajorDepartment(models.Model):
    major = models.CharField(primary_key=True, max_length=45)
    department = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'major_department'


class AllLecture(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)
    subject_name = models.CharField(max_length=70)
    classification = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.FloatField()

    class Meta:
        managed = False
        db_table = 'all_lecture'


class NewLecture(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)

    class Meta:
        managed = False
        db_table = 'new_lecture'


class Standard(models.Model):
    index = models.IntegerField(primary_key=True)
    user_year = models.IntegerField()
    user_dep = models.CharField(max_length=50)
    sum_score = models.IntegerField()
    major_essential = models.IntegerField()
    major_selection = models.IntegerField()
    core_essential = models.IntegerField()
    core_selection = models.IntegerField()
    basic = models.IntegerField()
    ce_list = models.CharField(max_length=100)
    cs_list = models.CharField(max_length=100)
    b_list = models.CharField(max_length=100)
    sum_eng = models.IntegerField()
    pro = models.IntegerField(blank=True, null=True)
    bsm = models.IntegerField(blank=True, null=True)
    eng_major = models.IntegerField(blank=True, null=True)
    build_sel_num = models.IntegerField(blank=True, null=True)
    pro_ess_list = models.CharField(max_length=100, blank=True, null=True)
    bsm_ess_list = models.CharField(max_length=100, blank=True, null=True)
    bsm_sel_list = models.CharField(max_length=100, blank=True, null=True)
    build_start = models.CharField(max_length=10, blank=True, null=True)
    build_sel_list = models.CharField(max_length=100, blank=True, null=True)
    build_end = models.CharField(max_length=10, blank=True, null=True)
    eng_major_list = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'standard'


class SubjectGroup(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)
    group_num = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'subject_group'


class UserGrade(models.Model):
    student_id = models.CharField(max_length=10)
    major = models.CharField(max_length=45, blank=True, null=True)
    year = models.CharField(max_length=10)
    semester = models.CharField(max_length=45)
    subject_num = models.CharField(max_length=10)
    subject_name = models.CharField(max_length=70)
    classification = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.FloatField()
    index = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'user_grade'


class UserInfo(models.Model):
    student_id = models.CharField(primary_key=True, max_length=10)
    year = models.IntegerField()
    major = models.CharField(max_length=45)
    name = models.CharField(max_length=45)
    book = models.CharField(max_length=45)
    eng = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'user_info'