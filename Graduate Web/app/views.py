# 데이터프레임
import pandas as pd
import numpy as np
# 장고 관련 참조
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
# 모델 참조
from .models import TestTable
from .models import GraduateScore

# 이 함수가 호출되면 -> index.html을 렌더링한다.
def r_index(request):
    return render(request, "index.html")

def r_dbcheck(request):
    # model의 test_table 테이블을 변수에 저장
    tt = TestTable.objects.all()
    # 그리고 함수가 불려서 페이지를 렌더링할때 그 변수를 해당 페이지에 넘김
    return render(request, "dbcheck.html", {"t_h":tt})

def f_upload(request):
    # 만약 post 형식으로 제출됐는데 file이 있다면.
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        # 일단 미디어 폴더에 저장.
        fs = FileSystemStorage()
        fs.save(uploaded_file.name , uploaded_file)
        # 그 파일을 compare 렌더링하는 함수로 넘긴다.
        return r_compare(request, uploaded_file.name)
    # file이 없다면.
    else:
        return HttpResponse('업로드 실패')

def r_upload(request):
    return render(request, "upload.html")

def r_compare(request, file_name):
    # 메시지를 html로 넘긴다.
    messages.info(request, '업로드 성공. app/uploaded_media 폴더 확인!!')

    # 이수학점 기준 모델 불러오기
    gs = GraduateScore.objects.all()
    gs_sum = gs[0].sum_score

    # dataframe 작업
    root = './app/uploaded_media/' + file_name
    data = pd.read_excel(root, index_col=None)
    data.to_csv('csvfile.csv', encoding='utf-8')
    data_sum = data['학점'].sum()
    
    return render(request, "compare.html", {"gs_sum":gs_sum , "data_sum":data_sum })


def f_test(request):
    gs = GraduateScore.objects.all()
    gs_sum = gs[0].sum

    data = pd.read_excel('./app/uploaded_media/기이수성적.xls', index_col=None)
    data.to_csv('csvfile.csv', encoding='utf-8')
    data_sum = data['학점'].sum()

    print(gs_sum)
    print(data_sum)
    return HttpResponse('테스트 완료, 터미널 확인')






'''
#excel to csv to dataframe
data = pd.read_excel('./app/media_down/기이수성적.xls', index_col=None)
data.to_csv('csvfile.csv', encoding='utf-8')
#user의 기이수 과목 항목별 나누기
#전공필수(Major Required)
MR = data[data['이수구분'].isin(['전필'])]
MR.reset_index(inplace=True,drop=True)
#전공선택(Major Choice)
MC = data[data['이수구분'].isin(['전선'])]
MC.reset_index(inplace=True,drop=True)
#교양필수(중핵필수)(Elective Required)
ER = data[data['이수구분'].isin(['교필'])]
ER.reset_index(inplace=True,drop=True)
#기초교양(Elective Basic)
EB = data[data['이수구분'].isin(['기교'])]
EB.reset_index(inplace=True,drop=True)
#교양선택(중핵필수선택)(Elective Choice)
EC = data[data['이수구분'].isin(['교선1','교선2','교선3'])]
EC.reset_index(inplace=True,drop=True)
#각 항목 이수 학점
mr_sum = MR['학점'].sum()
mc_sum = MC['학점'].sum()
ec_sum = EC['학점'].sum()
eb_sum = EB['학점'].sum()
er_sum = ER['학점'].sum()
total_sum = mr_sum + mc_sum + ec_sum + eb_sum + er_sum

#항목별 최소 이수 학점
total_credit_pass_16 = pd.DataFrame({'이수구분':['전필','전선','교필','기교','교선','전체'], 
                               '최소학점':[37,35,15,15,15,130]}, columns=['이수구분','최소학점'])
#전공필수 중 인증제도 과목
MR_subject_pass_16 = [['C프로그래밍및실습',9912],['고급C프로그래밍및실습',9913]]
#교양필수 과목
ER_subject_pass_16 = [['English for Professional Purposes 1',9063],['English for Professional Purposes 2',9064],
                     ['English Writing 1', 9065], ['Esglish Writing 2', 9066], ['문제해결을위한글쓰기와발표', 9067],
                     ['세종사회봉사1',8364],['서양철학:쟁점과토론',9068],['신입생세미나1',8360],['취업역량개발론',9030]]
#기초교양 과목
EB_subject_pass_16 = [['전산개론-I',8377],['미적분학및연습1',2647],
                     ['공업수학1', 304], ['일반물리학및실험1', 2647], ['통계학개론', 3353]]
#교양선택 중 필수 과목
EC_subject_pass_16 = [['세계사인간과문명',9489],['고급프로그래밍입문-P',9790],
                     ['정보사회의사이버윤리', 6279], ['Technical Writing 기초', 9936]]
#교양선택 영역 5가지
EC_category_pass_16 = ['사상과역사','사회와문화','융합과창업','자연과과학기술','세계와지구촌']

#이수학점 기준 통과 여부
total_credit_result = pd.DataFrame({'이수구분':['전필','전선','교필','기교','교선','전체'],
                                    '최소학점':[37,35,15,15,15,130],
                                    '이수학점':[mr_sum, mc_sum, er_sum, eb_sum, ec_sum, total_sum],
                                    '통과여부':[mr_sum>=37,mc_sum>=35,er_sum>=15,eb_sum>=15,ec_sum>=15,total_sum>=130]},
                                   columns=['이수구분','최소학점','이수학점','통과여부'])
total_credit_result
#전공필수 중 필수 과목 체크
MR_subject_tmp_16 = MR_subject_pass_16
MR_subject_rest_16 = []
for i in range(len(MR_subject_tmp_16)):
    for j in range(MR.shape[0]):
        if MR_subject_pass_16[i][1] == (MR['학수번호'][j]):
            MR_subject_tmp_16[i][1] = 0
            n=n-1
MR_subject_tmp_16
for i in range(len(MR_subject_tmp_16)):
    if MR_subject_tmp_16[i][1] != 0:
        MR_subject_rest_16 = MR_subject_tmp_16[i][0]
MR_subject_rest_16#결과값, NULL값이면 PASS

#교양필수(중핵필수) 과목 체크
ER_subject_tmp_16 = ER_subject_pass_16
ER_subject_rest_16 = []
for i in range(len(ER_subject_tmp_16)):
    for j in range(ER.shape[0]):
        if ER_subject_pass_16[i][1] == (ER['학수번호'][j]):
            ER_subject_tmp_16[i][1] = 0
for i in range(len(ER_subject_tmp_16)):
    if ER_subject_tmp_16[i][1] != 0:
        ER_subject_rest_16.append(ER_subject_tmp_16[i][0])
ER_subject_rest_16#결과값, NULL값이면 PASS


#기초교양 과목 체크
EB_subject_tmp_16 = EB_subject_pass_16
EB_subject_rest_16 = []
for i in range(len(EB_subject_tmp_16)):
    for j in range(EB.shape[0]):
        if EB_subject_pass_16[i][1] == (EB['학수번호'][j]):
            EB_subject_tmp_16[i][1] = 0
for i in range(len(EB_subject_tmp_16)):
    if EB_subject_tmp_16[i][1] != 0:
        EB_subject_rest_16.append(EB_subject_tmp_16[i][0])
EB_subject_rest_16#결과값, NULL값이면 PASS


#교양선택(중핵필수선택) 과목 체크
EC_subject_tmp_16 = EC_subject_pass_16
EC_subject_rest_16 = []
for i in range(len(EC_subject_tmp_16)):
    for j in range(EC.shape[0]):
        if EC_subject_pass_16[i][1] == (EC['학수번호'][j]):
            EC_subject_tmp_16[i][1] = 0
for i in range(len(EC_subject_tmp_16)):
    if EC_subject_tmp_16[i][1] != 0:
        EC_subject_rest_16.append(EC_subject_tmp_16[i][0])
EC_subject_rest_16#결과값, NULL값이면 PASS


#교양선택(중핵필수선택) 선택 영역 체크
EC_category_tmp_16 = EC_category_pass_16
EC_category_rest_16 = []
n = len(EC_category_tmp_16)
for i in range(len(EC_category_tmp_16)):
    for j in range(EC.shape[0]):
        if EC_category_pass_16[i] == (EC['선택영역'][j]):
            print("1")
            EC_category_tmp_16[i] = 0
for i in range(len(EC_category_tmp_16)):
    if EC_category_tmp_16[i] != 0:
        EC_category_rest_16.append(EC_category_tmp_16[i])
EC_category_rest_16#결과값, NULL값이면 PASS

#결과값 데이터프레임 형식으로 유지
MR_df = pd.DataFrame({'전필':MR_subject_rest_16})
ER_df = pd.DataFrame({'교필':ER_subject_rest_16})
EB_df = pd.DataFrame({'기교':EB_subject_rest_16})
EC_df = pd.DataFrame({'교선':EC_subject_rest_16})
CA_df = pd.DataFrame({'영역':EC_category_rest_16})

#결과값 Merge
result = pd.concat([total_credit_result,MR_df,ER_df,EB_df,EC_df,CA_df],axis=1)
result.fillna(0)
'''