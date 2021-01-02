#!/usr/bin/env python
# coding: utf-8

# In[128]:


import pandas as pd
import numpy as np


# # User 성적표 전처리

# In[129]:


#excel to csv to dataframe
data = pd.read_excel('/Users/hon99oo/Desktop/21CS/RawGrade.xls', index_col=None)
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
#논패과목 삭제
for i in range(data.shape[0]):
    if data['등급'][i]=='NP':
        data = data.drop(data.index[i])
data.reset_index(inplace=True, drop=True)
#각 항목 이수 학점
mr_sum = MR['학점'].sum()
mc_sum = MC['학점'].sum()
ec_sum = EC['학점'].sum()
eb_sum = EB['학점'].sum()
er_sum = ER['학점'].sum()
total_sum = mr_sum + mc_sum + ec_sum + eb_sum + er_sum


# # 2016 졸업기준 DATAFRAME

# In[303]:


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


# # 졸업여부 확인 Algorithm

# In[390]:


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


# # 추천과목 DB

# In[130]:


import pandas as pd
import numpy as np
import re

cs20_1 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/20_1.xlsx', index_col=None)
cs20_2 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/20_2.xlsx', index_col=None)
cs19_2 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/19_2.xlsx', index_col=None)
cs18_1 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/18_1.xlsx', index_col=None)
cs18_2 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/18_2.xlsx', index_col=None)
cs17_1 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/17_1.xlsx', index_col=None)
cs17_2 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/17_2.xls', index_col=None)
cs16_2 = pd.read_excel('/Users/hon99oo/Desktop/21CS/schedule/16_2.xlsx', index_col=None)


# In[131]:


cs = pd.concat([cs20_1,cs20_2,cs19_2,cs18_1,cs18_2,cs17_1,cs17_2,cs16_2],ignore_index=True)
cs = cs.loc[:,cs.keys()[1:10]]
for i in range(cs.shape[0]) :
    cs['학수번호'][i] = int(re.findall("\d+",str(cs['학수번호'][i]))[0])
cs = cs.drop_duplicates(['학수번호'], ignore_index=True)


# In[132]:


cs


# In[ ]:




