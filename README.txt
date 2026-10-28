생각이 많아지면 — 움직이는 시각시

현재 공개 사이트와 동일한 코드입니다. 15px 원형 커서 포함.

파일
- index.html: 화면 구조·스타일·커서 크기
- app.js: 호버, 영역 비율, 글자 변형, 숫자 위치
- typography.js: 문구와 글자 배치 데이터
- assets/glyphs/: 생각·용기 글자 키프레임 SVG (생각_00.svg, 용기_00.svg …)
- assets/glyphs.json: 키프레임을 변형용으로 변환한 데이터 (직접 고치지 말고 아래 변환기로 생성)
- tools/build_glyphs.py: 키프레임 SVG → glyphs.json 변환기
- assets/: 폰트와 기존 이미지 자료

글자 키프레임 추가
1. 일러스트레이터에서 단계별 글자를 '윤곽선 만들기' 한 뒤 SVG로 내보내 assets/glyphs/ 에 넣습니다.
   같은 글자의 키프레임끼리 조각 수(구멍 수 포함)만 같으면 됩니다. 앵커 포인트 개수는 맞출 필요 없습니다.
2. tools/build_glyphs.py 맨 위 GLYPHS 목록에 파일을 순서대로 적습니다.
3. python3 tools/build_glyphs.py 를 실행하면 assets/glyphs.json 이 다시 만들어집니다.

기준 화면: 첫 화면 그림(1526×848 px). 이 크기의 창에서 첫 화면이 그림과 픽셀 단위로 일치합니다.
※ assets/glyphs/생각_00.svg 는 그림에서 따낸 임시 모양입니다. 윤곽선 만든 원본이 오면 교체하세요.

실행
1. ZIP을 압축 해제합니다.
2. 터미널에서 index.html이 있는 폴더로 이동합니다.
3. Python 3가 설치되어 있다면 python3 -m http.server 8000 을 실행합니다.
4. 브라우저에서 http://localhost:8000 을 엽니다.
5. 종료는 터미널에서 Control+C.

index.html을 더블클릭하면 브라우저 보안 정책 때문에 SVG 변형 데이터가 로드되지 않을 수 있습니다. 로컬 웹 서버로 열어주세요.

조작
클릭으로 시작. 생각 영역에 3초 머무르면 확장합니다. 용기 쪽으로 옮기면 흰 영역이 다시 확장합니다. R 또는 ↺로 초기화합니다.
