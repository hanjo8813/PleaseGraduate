<div align='center'>
    <h3> 사이트 version 2.0 베타 테스트 중... </h3>
</div>

<br>

# Please Graduate

 ![pg](https://img.shields.io/badge/version-2.0_beta-a3374f) 

## 관련 링크

<table >
    <tr>
        <td width="600" align='center'>사이트 링크 <br> https://www.please-graduate.com/</td>
        <td width="600" align='center'><a href="/dev_record.md">개발일지 / 업데이트 기록</a></td>
       <td width="600" align='center'>구버전(ver 1.0) 내용</td>
    </tr>
</table>

<br>

## 💻 프로젝트 소개

![python-bg](https://img.shields.io/badge/Python-v3.9-blue?logo=Python) ![django-bg](https://img.shields.io/badge/Django-v3.1.4-44b78b?logo=Django)

![image](https://user-images.githubusercontent.com/71180414/125630704-4954ae10-8c76-4530-9c87-28d4c383e951.png)

<div align='center'>
   <h3>세종대학교 졸업요건 검사 및 강의 추천 서비스 'Please Graduate'</h3>
</div>

### 구현 계기
- 세종대학교의 졸업요건은 기준 학점도 채워야하지만, **7가지 영역**을 모두 만족해야 해서 매우 복잡합니다.
- 학교에서 제공되는 **수강편람**은 가독성이 떨어지기 때문에 재학생들이 졸업요건을 알기 쉽지 않습니다.
- 매년 개편되는 수강편람 때문에 **학과**와 **학번**별로 모든 졸업요건이 상이합니다.
- 졸업 필수과목의 과목명이나 학점이 변경되는 경우가 많아 혼란을 야기합니다.
- 복수/연계 전공을 신청한다면 졸업 요건이 변경됩니다.


<details>
  <summary><b>졸업요건 영역 설명</b></summary>
   <br>

~~상당히 복잡합니다~~
|영역|만족조건|
|---|---|
|전공필수 |전필 기준학점을 만족하면 통과, 학점 초과시 전선 학점으로 인정|
|전공선택 |전선 기준학점을 만족하면 통과|
|교양필수 |교필 기준학점을 만족, 필수과목을 모두 이수하면 통과|
|교양선택 |교선 기준학점을 만족, 필수과목을 모두 이수, 선택영역 3가지 이상 이수하면 통과|
|기초교양 |기교 기준학점을 만족, 필수과목을 모두 이수하면 통과|
|영어인증 |5가지 어학인증 기준점수를 만족 or Intensive English 과목을 이수하면 통과|
|고전독서 인증|4가지 영역이 있고, 각 영역 기준 권수를 만족 or 고전특강 과목을 이수하면 통과|

</details>

<br>

## 🔎 사용 방법

<br>

<details>
<summary><b>학생인증 및 회원가입</b></summary>
<br>

| ![MmC8ZKFJcE](https://user-images.githubusercontent.com/71180414/125654054-8b6f5d95-e801-454d-8cec-c36198984260.gif)|
|:--:|
|**학생인증 및 회원가입**|

- Please Graduate는 학생인증을 해야만 회원가입이 가능합니다.
- 세종대학교 포털의 ID/PW를 입력받아 세종 고전독서인증센터 사이트에 로그인 후, 사용자 정보를 크롤링하여 인증합니다.
- 회원가입 시엔 전공 상태(복수/연계) 및 영어 인증(어학시험 점수) 정보를 입력합니다.

</details>

<br>

<details>
<summary><b>마이페이지</b></summary>
<br>

| ![Vxx8J9ntrT](https://user-images.githubusercontent.com/71180414/125667129-8ecbb718-a595-4720-b22c-52b341d0b25b.gif)|
|:--:|
|**마이페이지**|

- 회원가입 때 기입한 정보를 모두 나타내며 각 정보는 수정이 가능합니다.
- 단 기본 사용자 정보(이름,학과,학번)와 고전독서현황은 고전독서인증센터 크롤링을 통해 업데이트합니다.
- 비밀번호 변경 및 회원탈퇴 기능을 제공합니다.

</details>

<br>

<details>
<summary><b>기이수과목 엑셀파일 업로드</b></summary>
<br>

| ![P3UfxHZuQU](https://user-images.githubusercontent.com/71180414/125672964-5cd57bf5-603b-4cd1-9b78-913e14e14b90.gif)|
|:--:|
|**기이수과목 엑셀파일 업로드**|

- 검사를 위해선 세종대학교 학사정보시스템에서 기이수성적 엑셀파일을 다운로드 받아 업로드해야합니다.
- 서버에서는 http request에서 파일을 추출해 업로드된 엑셀파일의 형식을 검사 후, 필요 정보만을 데이터베이스에 저장합니다.

</details>

<br>

<details>
<summary><b>기이수과목 커스텀</b></summary>
<br>

| ![7nqKHF6kAj](https://user-images.githubusercontent.com/71180414/125675959-7ca223d0-6c9b-420a-884f-77e462b4efd6.gif)|
|:--:|
|**기이수과목 커스텀**|

- 사용자의 기이수과목을 편집할 수 있는 기능입니다.
- 미래 수강 계획을 짤 수 있도록 수강 예정인 과목을 미리 추가해 졸업요건을 검사해볼 수 있습니다.
- 사용자는 추가하고 싶은 과목을 학수번호로 검색한 후, 해당 과목의 이수구분을 선택하여 추가합니다.
- 검색 기능엔 AJAX를 도입하여 결과 화면이 새로고침되지 않도록 구현하였습니다.

</details>

<br>

<details>
<summary><b>졸업요건 검사</b></summary>
<br>

|![FvomDdcev0](https://user-images.githubusercontent.com/71180414/125678163-86c1e95d-6cd6-48d8-bb0e-55e2d0761393.gif) |
|:--:|
|**영역별 달성도 그래프**|

- 영역별 달성도를 시각화하여 사용자가 부족한 영역과 학점을 바로 보여줍니다.
- TIP 툴팁을 클릭하면 통과 기준을 알려줍니다.

<br>

|![69GuMvJJRp](https://user-images.githubusercontent.com/71180414/125679373-47784fd9-4431-4510-a1f0-fef535875fca.gif) |
|:--:|
|**검사 및 과목 추천**|

- Recommend 버튼을 누르면 각 영역의 세부 정보를 확인할 수 있습니다.
- 필수과목이 있는 영역에선 필수과목을 검사하여 부족한 과목을 추천합니다.
- 필수과목 없이 기준 학점만 만족하면 되는 영역에선 다른 사용자의 데이터를 참조해 과목을 추천합니다.
- 
</details>

