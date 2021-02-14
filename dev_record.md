# 개발일지

## SejongGraduateHellper 프로젝트를 AWS 서버에 배포하기.

- [협업때 쓰던 commit 규칙](/commit_rule.md)

## 개발/업데이트 기록

> 02/15
- 수강신청 기간이라 사용 못하도록 수정
- `총 방문자 수` : 512 / `총 검사 횟수` : 416 / `실사용자 수` : 260

> 02/14
- 기준 추가 후 재배포
- 추천 머신러닝 부분 수정

> 02/12
- 전자정보통신공학과 기준 추가
- 공학인증 기준 DB 구조 변경 + 알고리즘 보완
- 머신러닝 추천시, 참고 데이터를 같은 학과로만 구성하도록 변경
- `총 방문자 수` : 266 / `총 검사 횟수` : 260 / `실사용자 수` : 102

> 02/11
- uis에서 특정 ip의 다수의 우회 로그인 감지시 당일 해당 ip 차단함을 알게됨
- 따라서 일단 보완점으로 재검사하는 사용자는 크롤링하지 않도록 방식 변경
- 보안 취약점 보완 , https 적용

> 02/10
- 장고 secret key , DB 정보 git hub 노출 관련 피드백 수정

> 02/09
- version 1.0으로 첫 배포
- 150회 이상의 검사로 uis의 우회 로그인 차단
- index 페이지에 공지 후 사이트 이용 차단 후 점검
- `총 방문자 수` : 152 / `총 검사 횟수` : 156

> 01/31
- ID/PW 틀릴 시 예외처리 
- 해당 학과-학번의 기준이 없을 시 예외처리
- 크롤링 함수 병합 및 개발-배포 분리
- 사용자 정보를 더이상 세션에 담지 않고 DB에 저장
- 엑셀 파일 다운 -> DF화 -> DB에 저장 -> 엑셀 삭제 방식으로 변경

> 01/30
- 기존의 excel 파일 다운로드 방식을 변경
- user_info/user_grade 테이블 생성

> 01/18
- wsgi 패키지 설치
- nginx 설치 후 static 경로 설정
- 로컬 기준 경로 코드를 ubuntu 기준 추가
- 개발자 모드가 아닌 항시 배포상태 성공

> 01/17
- MySQL 설치 및 http-port 생성 후 연동.
- 크롬/크롬드라이버 설치
- Django settings 변경
- 개발자 모드(runserver)로 client 테스트.. 실패..

> 01/16
- AWS EC2 서버 생성
- 기본 패키지 설정
- python/pip 설치
- 가상환경(virtual-env)내에 py라이브러리 설치
- ubuntu에 git clone, 연동


## 설치한 라이브러리 목록

- `pip install django`
- `pip install mysqlclient`
- `pip install pandas`
- `pip install xlrd`
- `pip install selenium`
- `pip install beautifulsoup4`
- `pip install surprise`
- `pip install django-pandas`
- `pip install pylint-django` (vs코드용)


## 참고 사이트 

- [HTTPS 개념](https://webactually.com/2018/11/16/http%EC%97%90%EC%84%9C-https%EB%A1%9C-%EC%A0%84%ED%99%98%ED%95%98%EA%B8%B0-%EC%9C%84%ED%95%9C-%EC%99%84%EB%B2%BD-%EA%B0%80%EC%9D%B4%EB%93%9C/)
- [AWS -> ACM + 로드밸런서 + Route53 HTTPS 적용](https://jootc.com/p/202004053362)
- [AWS mysql 설치](https://ndb796.tistory.com/314)
- [AWS-Django 연동](https://nerogarret.tistory.com/47)
- [AWS-Django 연동2](https://nachwon.github.io/django-deploy-3-nginx/)
- [ubuntu vim 사용](https://jhnyang.tistory.com/54)
- [ubuntu 크롬 드라이버](https://dvpzeekke.tistory.com/1)
- [ubuntu 파일 권한 변경 chmod](https://withcoding.com/103)
- [Django 세션 settings](https://ndjman7.github.io/django/2019/12/21/Django%EC%97%90%EC%84%9C-%EC%84%B8%EC%85%98-%EC%9C%A0%EC%A7%80%EC%8B%9C%EA%B0%84-%EC%84%A4%EC%A0%95%ED%95%98%EA%B8%B0.html)
- [Django 세션DB 클리어](http://www.iorchard.net/docs/pvdi2/django_clearsessions.html)
