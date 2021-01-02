# 파이썬 라이브러리
from collections import defaultdict
# 데이터프레임
import pandas as pd
import numpy as np
# 장고 관련 참조
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
# 모델 참조
from .models import TestTable, AllLecture, IndCombi, SubjectGroup, GraduateScore, Basic, CoreEssential, CoreSelection

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

#-------------------------------------------------------------------------------------

def make_group(list_):
    group_list = []
    for s_num in list_:
        sg = SubjectGroup.objects.filter(subject_num = s_num)
        if sg.exists():
            group_list.append(sg[0].group_num)
    return group_list

def make_lack(my_list, list_, group_):
    my_lack = []
    for s_num in my_list:
        # 사용자가 들은게 학수번호 리스트에 존재.
        if s_num in list_:
            list_.pop(s_num)
        # 존재 X -> 사용자가 재수강했을경우 고려
        else:
            # 사용자가 들은걸 그룹번호로 매핑
            sg = SubjectGroup.objects.filter(subject_num = s_num)
            # 매핑이 애초에 안된다면 -> 단일과목이라는것
            if sg.exists() == 0:
                my_lack.append(s_num)
            # 매핑이 됐을 경우
            else:
                # 그룹번호 리스트에 존재한다면 -> 들은것
                if sg[0].group_num in group_:
                    list_.pop(s_num)
                else:
                    my_lack.append(s_num)
                    
                
    return my_lack

def f_test(request):
    # 셀레니움으로 넘어올 학과 - 입학년도
    p_major = '디지털콘텐츠'
    p_year = 16
    
    # 파이썬 변수를 가지고 ind로 매핑
    ic_row = IndCombi.objects.get(major = p_major, year=p_year)
    p_ind = ic_row.ind      # 매핑된 ind
    print(p_ind)

#-------------------------------------------------------------------------------------
    # db에서 ind 를 가지고 모든 비교 기준 뽑아내기
    # 1. 이수학점 수치 기준
    gs_row = GraduateScore.objects.get(ind = p_ind)
    num_ss = gs_row.sum_score           # sum_score
    num_me = gs_row.major_essential     # major_essential
    num_ms = gs_row.major_selection     # major_selection
    num_ce = gs_row.core_essential      # core_essential   
    num_cs = gs_row.core_selection      # core_selection
    num_b = gs_row.basic                # basic
    print(num_ss, num_me, num_ms, num_ce, num_cs, num_b)

    # 2. 중필(교필) 필수과목 리스트 and 그룹번호로 바꾼 리스트
    # ind로 필수과목 추출.
    ce_row = CoreEssential.objects.get(ind = p_ind)
    list_ce = [int(s) for s in ce_row.subject_num_list.split(',')]
    dic_ce = defaultdict(int)
    
    

    '''
    # 필수과목에 해당하는 그룹번호 리스트 만들기 / make_group 함수 위에 있음
    group_ce = make_group(list_ce)
    print("중필")
    print(list_ce)
    print(group_ce)

    # 3. 중선(교선1) 필수과목
    cs_row = CoreSelection.objects.get(ind = p_ind)
    list_cs = [int(s) for s in cs_row.subject_num_list.split(',')]
    group_cs = make_group(list_cs)
    print("중선")
    print(list_cs)
    print(group_cs)
    
    # 4. 기교 필수과목 
    b_row = Basic.objects.get(ind = p_ind)
    list_b = [int(s) for s in b_row.subject_num_list.split(',')]
    group_b = make_group(list_b)
    print("기교")
    print(list_b)
    print(group_b)

#-------------------------------------------------------------------------------------
    # 입력받은 엑셀 파일 dataframe으로 변환
    data = pd.read_excel('./app/uploaded_media/기이수성적2.xls', index_col=None)
    data.to_csv('csvfile.csv', encoding='utf-8')
    # 논패과목 삭제
    for i in range(data.shape[0]):
        if data['등급'][i]=='NP':
            data = data.drop(data.index[i])
    data.reset_index(inplace=True, drop=True)

    # 이수 구분마다 df 생성
    # 전필
    df_me = data[data['이수구분'].isin(['전필'])]
    df_me.reset_index(inplace=True,drop=True)
    my_num_me = df_me['학점'].sum()
    # 전선
    df_ms = data[data['이수구분'].isin(['전선'])]
    df_ms.reset_index(inplace=True,drop=True)
    my_num_ms = df_ms['학점'].sum()
    # 중필(교필)
    df_ce = data[data['이수구분'].isin(['교필'])]
    df_ce.reset_index(inplace=True,drop=True)
    my_num_ce = df_ce['학점'].sum()                     # 사용자의 중필학점 총합
    my_list_ce = sorted(df_ce['학수번호'].tolist())     # 사용자의 중필 학수번호 리스트
    # 중선(교선)
    df_cs = data[data['이수구분'].isin(['교선1'])]
    df_cs.reset_index(inplace=True,drop=True)
    my_num_cs = df_cs['학점'].sum()
    my_list_cs = sorted(df_cs['학수번호'].tolist())
    # 기교
    df_b = data[data['이수구분'].isin(['기교'])]
    df_b.reset_index(inplace=True,drop=True)
    my_num_b = df_b['학점'].sum()
    my_list_b = sorted(df_b['학수번호'].tolist())
    # 사용자의 총 학점
    my_num_ss = my_num_me+my_num_ms+my_num_ce+my_num_cs+my_num_b
#-------------------------------------------------------------------------------------
    # 검사 단계

    # 1. 총 학점 비교
    print('총 학점')
    if num_ss <= my_num_ss :
        print('총 학점 기준을 만족했습니다.')
    else:
        print(num_ss-my_num_ss,'학점이 부족합니다.')

    # 2. 전필 검사
    print('전필')
    remain = 0
    if num_me <= my_num_me :
        print('전필 학점 기준을 만족했습니다.')
        if num_me < my_num_me:
            remain = my_num_me - num_me
    else:
        print(num_me-my_num_me, '학점이 부족합니다.')

    # 3. 전선 검사
    print('전선')
    if num_ms <= my_num_ms :
        print('전선 학점 기준을 만족했습니다.')
    else:
        if num_ms <= my_num_ms + remain:
            print('전선 학점이 부족했지만 전필에서 ', remain, '학점이 남아 기준을 만족했습니다.')
        else:
            print(num_ms-my_num_ms,'학점이 부족합니다.')

    # 4. 중필 검사
    # 학점 검사는 필요없지만 일단 넣음
    print('중필')
    if num_ce <= my_num_ce :
        print('총 학점 기준을 만족했습니다.')
    else:
        print(num_ce-my_num_ce,'학점이 부족합니다.')
    
    # 내가 부족한 중필과목 리스트 
    my_lack_ce = make_lack(my_list_ce, list_ce, group_ce)


    print(my_lack_ce)
    if not my_lack_ce :
        print('모든 필수과목을 이수했습니다.')
    else:
        # 학수번호를 매핑해서 정보 쿼리셋 저장
        lack_lec = AllLecture.objects.none()
        for s_num in my_lack_ce:
            temp = AllLecture.objects.filter(subject_num = s_num)
            lack_lec = lack_lec.union(temp)
        # 저장된 쿼리셋을 순회해서 정보 출력
        for row in lack_lec:
            print(row.subject_num)
    
   

            
            
        

    

'''
    return HttpResponse('테스트 완료, 터미널 확인')





'''
#excel to csv to dataframe
data = pd.read_excel('/Users/hon99oo/Desktop/21CS/RawGrade.xls', index_col=None)
#논패과목 삭제
for i in range(data.shape[0]):
    if data['등급'][i]=='NP':
        data = data.drop(data.index[i])
data.reset_index(inplace=True, drop=True)
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


# # 2016 졸업기준 DATAFRAME
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


# 졸업여부 확인 Algorithm
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