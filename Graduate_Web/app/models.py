from django.db import models

# DB 테이블의 구조를 파이썬 클래스로 보여주고, 수정가능

# 테스트용 테이블

class TestTable(models.Model):
    num = models.IntegerField(primary_key=True)
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

# ---------------------------------------------------------------------------

class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class SuccessTestCount(models.Model):
    index = models.IntegerField(primary_key=True)
    num_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'success_test_count'


class AllLecture(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)
    subject_name = models.CharField(max_length=70)
    classification = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'all_lecture'


class NewLecture(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)

    class Meta:
        managed = False
        db_table = 'new_lecture'


class Standard(models.Model):
    user_year = models.IntegerField(primary_key=True)
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
    build = models.IntegerField(blank=True, null=True)
    pro_acc_list = models.CharField(max_length=100, blank=True, null=True)
    bsm_ess_list = models.CharField(max_length=100, blank=True, null=True)
    bsm_sel_list = models.CharField(max_length=100, blank=True, null=True)
    build_ess_list = models.CharField(max_length=100, blank=True, null=True)
    build_sel_list = models.CharField(max_length=100, blank=True, null=True)
    engine_major_list = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'standard'
        unique_together = (('user_year', 'user_dep'),)


class SubjectGroup(models.Model):
    subject_num = models.CharField(primary_key=True, max_length=10)
    group_num = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'subject_group'


class UserGrade(models.Model):
    student_id = models.CharField(max_length=10)
    year = models.CharField(max_length=10)
    semester = models.CharField(max_length=45)
    subject_num = models.CharField(max_length=10)
    subject_name = models.CharField(max_length=70)
    classification = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()
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