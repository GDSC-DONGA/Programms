# GDSC DAU 포인트 시스템(Python Ver. 3.10.0)  
- **code/Lookup.py : 멤버 포인트 조회 시스템**
  - 학번 입력 후 해당하는 학번의 합계, 평균을 출력, 현재 분포를 차트로 시각화
- **PointManager.py : 포인트 setting 시스템**  
  - FireBase RealTime DataBase의 /admin 데이터를 Tabular 형태로 데이터 Read 
  - 해당하는 학생의 포인트 항목 수정 후 자동으로 갱신되는 합계, 평균 확인
  - save시 자동으로 DB에 Write


관련 패키지는 `env` 폴더 참고바람.

사용하기 앞서 `firebase RealTimeDataBase`를 이용하는 프로그램인 점 유의.
빌드 담당자는 key파일이 존재해야함. (업로드 된 code파일은 key 파일 제외 후 업로드 됨)


# DB Tree structure

학번
- 이름
- 합계
- 평균  
  
admin
- 포인트 항목 1
- 포인트 항목 2
- 포인트 항목 n
- 이름
- 학번
- 평균

## Pre SetUp
1. PyCharm-Virtual Environments 생성
2. 프로젝트 터미널에서 `pip install -r requirements.txt`
3. FireBase RealTimeDataBase <key>.json 파일 다운로드 후 코드 적용

## contributor
GDSC DAU 1st Core Members
- 이승민(Lead)
- 박정현
- 이준원
- 민지훈
- 임가겸
- 조영훈


## LICENSE
MIT License

Copyright (c) 2023 GDSC DAU

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## concat 
email. jhparkinglot@gmail.com
github. jhparkland
