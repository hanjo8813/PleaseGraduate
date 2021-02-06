# SGH_for_AWS

## SejongGraduateHellper 프로젝트를 AWS 서버에 배포하기.
> 될 때까지 한다.......

- 사이트 링크 : http://ec2-3-34-126-50.ap-northeast-2.compute.amazonaws.com
- [원래 repo](https://github.com/hon99oo/SejongGraduateHellper)
- [사용하던 Commit 규칙, 설정 등](/commit_rule.md)


## 업데이트 기록
> 01/16
- AWS EC2 서버 생성
- 기본 패키지 설정
- python/pip 설치
- 가상환경(virtual-env)내에 py라이브러리 설치
- ubuntu에 git clone, 연동

> 01/17
- MySQL 설치 및 http-port 생성 후 연동.
- 크롬/크롬드라이버 설치
- Django settings 변경
- 개발자 모드(runserver)로 client 테스트.. 실패..

> 01/18
- wsgi 패키지 설치
- nginx 설치 후 static 경로 설정
- 로컬 기준 경로 코드를 ubuntu 기준 추가
- 개발자 모드가 아닌 항시 배포상태 성공

> 01/30
- 기존의 excel 파일 다운로드 방식을 변경
- user_info/user_grade 테이블 생성

> 01/31
- ID/PW 틀릴 시 예외처리 
- 해당 학과-학번의 기준이 없을 시 예외처리
- 크롤링 함수 병합 및 개발-배포 분리
- 사용자 정보를 더이상 세션에 담지 않고 DB에 저장
- 엑셀 파일 다운 -> DF화 -> DB에 저장 -> 엑셀 삭제 방식으로 변경


## 참고 사이트 

- [AWS mysql 설치](https://ndb796.tistory.com/314)
- [AWS-Django 연동](https://nerogarret.tistory.com/47)
- [AWS-Django 연동2](https://nachwon.github.io/django-deploy-3-nginx/)
- [ubuntu vim 사용](https://jhnyang.tistory.com/54)
- [ubuntu 크롬 드라이버](https://dvpzeekke.tistory.com/1)
- [ubuntu 파일 권한 변경 chmod](https://withcoding.com/103)
- [Django 세션 settings](https://ndjman7.github.io/django/2019/12/21/Django%EC%97%90%EC%84%9C-%EC%84%B8%EC%85%98-%EC%9C%A0%EC%A7%80%EC%8B%9C%EA%B0%84-%EC%84%A4%EC%A0%95%ED%95%98%EA%B8%B0.html)
- [Django 세션DB 클리어](http://www.iorchard.net/docs/pvdi2/django_clearsessions.html)

