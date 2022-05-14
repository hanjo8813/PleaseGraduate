# 파이썬 라이브러리
from sejong_univ_auth import auth, ClassicSession
# 모델 참조
from ..models import *


def get_user_info(id, pw):
    res = auth(id=id, password=pw, methods=ClassicSession)

    # 대휴칼 사이트 오류
    if res.status_code != 200:
        return "err_server"

    # 로그인 오류 (ID/PW 틀림 or 가입불가 재학생)
    if not res.is_auth:
        return "err_auth"

    # 사용자 정보
    name = res.body["name"]
    major = res.body["major"]

    # 고전독서 인증현황
    status = res.body["status"]
    if status == "대체이수" :
        book = "고특통과"
    else :
        read_certification = res.body["read_certification"]
        book = ""
        for num in read_certification.values() :
            book += num.replace(" 권", "")

    context = {
        "name" : name,
        "major" : major,
        "book" : book
    }
    return context