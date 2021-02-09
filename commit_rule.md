# SejongGraduateHellper

## Commit 규칙

### 1. 파일추가
> Add 파일명_이름 ex) `Add selenium.py_안재현`  
> 세부내용은 한글로 무슨 기능을 하는 파일인지 추가.

### 2. 파일수정
> Modify 파일명_이름 ex) `Modify manage.py_안재현`    
> 세부내용은 무슨 내용 수정하였는지 추가.

### 3. 파일삭제
> Delete 파일명_이름 ex) `Delete init.py_안재현`   
> 세부내용은 무슨파일 삭제하였는지 추가.

### 4. Pull Request
> main 브랜치는 모두의 시작점이므로 병합할 때 임의로 하지 않고 팀원 전원 승락 후 병합

### 5. Branch
> 자신의 브랜치임을 표시하고, 더 이상 사용하지 않는 브랜치는 삭제한다.

<br>

## 서버 환경 세팅

### graduate_help 덤프파일 import 하기
1. MySQL에서 `create database graduate_help` 로 'graduate_help' 데이터베이스 생성후 quit
2. 압축을 푼 graduate_help.sql 파일을 원하는 위치에 가져다 놓는다.
3. 터미널 실행 후 동일한 위치로 터미널 이동 (MySQL 접속 X)
3. `mysql -u root -p graduate_help < graduate_help.sql` 명령어 실행해서 import

### Django - MySQL 연동하기
> 철자 실수로 프로젝트 세팅 폴더명이 project 가 아닌 projcet임
1. 각자 로컬에서 MySQL 실행
2. projcet > settings.py > DATABASE 파트에서 PASSWORD를 자신의 MySQL 비밀번호로 설정
3. `python manage.py inspectdb` 명령어로 연동 DB 감지 테스트.
