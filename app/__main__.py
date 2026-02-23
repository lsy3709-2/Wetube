"""
WeTube 실행 진입점 – python -m app 으로 실행할 때 사용합니다.

기능:
  - app 패키지를 '실행 가능한 모듈'로 만듭니다.
  - __init__.py 에서 생성한 app 인스턴스를 가져와 개발 서버를 기동합니다.
  - 터미널에서 'flask run' 대신 'python -m app' 으로 서버를 띄울 수 있습니다.
"""

# ----- app 인스턴스 로드 -----
# 기능: __init__.py 의 create_app() 으로 만든 Flask 앱 객체.
#       이 객체에 run() 을 호출해 개발 서버를 시작합니다.
from app import app

# ----- 직접 실행 시에만 서버 기동 -----
# 기능: 이 파일을 'python -m app' 또는 'python app/__main__.py' 로 실행했을 때만 실행됩니다.
#       다른 모듈에서 'from app import app' 으로 불러올 때는 실행되지 않습니다.
if __name__ == "__main__":
    # 기능: 사용자에게 등록된 라우트와 포트 충돌 주의 안내를 출력합니다.
    print("등록된 라우트: / /auth/login /auth/register /auth/profile /studio ...")
    print("중요: 5000 포트를 쓰는 다른 프로그램(기존 Flask 등)이 있으면 먼저 종료하세요.")
    print("      그렇지 않으면 /studio/ 에서 404가 납니다.")

    # 기능: Flask 개발 서버 기동.
    #       debug=True: 에러 시 디버그 페이지, use_reloader 기본 True → 코드 변경 시 자동 재시작
    app.run(debug=True, host="127.0.0.1", port=5000)
