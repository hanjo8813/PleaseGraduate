# 파이썬 라이브러리
from sejong_univ_auth import auth, ClassicSession
# 모델 참조
from ..models import *

import requests
import re
from bs4 import BeautifulSoup as bs
from bs4.element import PageElement

def get_user_info(id, pw):
    # 세종 포털 로그인 요청
    login_res = requests.post(
            url='https://portal.sejong.ac.kr/jsp/login/login_action.jsp', 
            data={
                'mainLogin': 'Y',
                'rtUrl': 'https://classic.sejong.ac.kr/classic/index.do',
                'id': id,
                'password': pw,
                'chkNos': 'on'
            },
            headers={
                'Referer' : 'https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp'
            },
            timeout=10,
        )
    
    # 세종 포털 사이트 오류
    if login_res.status_code != 200:
        return "err_server"

    # 쿠키에서 ssotoken 여부 확인
    cookie = login_res.headers.get('Set-Cookie', '')
    match = re.search(r'ssotoken=([^;]+)', cookie)

    # 로그인 오류 (ID/PW 틀림)
    if not match:
        return "err_auth"

    # ssotoken 추출
    ssotoken = match.group(1)

    # ssotoken으로 대휴칼 고전독서인증현황 페이지 요청
    classic_res = requests.get(
            url='https://classic.sejong.ac.kr/classic/reading/status.do', 
            headers={
                'Cookie' : 'ssotoken=' + ssotoken
            },
            timeout=10,
        )

    # 세종 포털 사이트 오류
    if classic_res.status_code != 200:
        return "err_server"

    soup = bs(classic_res.text, 'html.parser')

    # 사용자 정보 추출
    major = soup.find('th', text='학과명').find_next('td').get_text().strip()
    name = soup.find('th', text='이름').find_next('td').get_text().strip()
    status = soup.find('th', text='사용자 상태').find_next('td').get_text().strip()
    
    # 상태별로 book 설정
    if status == "대체이수" :
        book = "고특통과"
    else :
        # 고전독서 
        book = ""
        table = soup.find_all('table', class_='b-board-table')[1]
        rows = table.find_all('tr')[1:-1]
        for row in rows:
            cells = row.find_all('td')
            book_string = cells[0].get_text().strip()
            book += book_string.replace("권", "")

    context = {
        "name" : name,
        "major" : major,
        "book" : book
    }
    return context