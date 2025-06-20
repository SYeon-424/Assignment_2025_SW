import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Bike Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("📊 기초 통계 및 전처리")

            st.markdown("### 1) '세종' 지역 결측치('-') → 0 치환")
            sejong_mask = df['지역'].str.contains('세종', na=False)
            df.loc[sejong_mask] = df.loc[sejong_mask].replace('-', 0)

            st.markdown("### 2) 숫자형 변환")
            numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            st.markdown("### 3) 데이터프레임 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            #st.text(buffer.getvalue())
            st.code(buffer.getvalue(), language='text')

            st.markdown("### 4) 요약 통계량 (`df.describe()`)")
            st.dataframe(df.describe())

            st.markdown("### 5) 전처리된 샘플 데이터")
            st.dataframe(df.head())

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("📈 Population Trend by Year")

            # '전국' 데이터만 필터링
            national_df = df[df['지역'] == '전국'].copy()

            # 연도 정렬 및 숫자형으로 변환
            national_df['연도'] = pd.to_numeric(national_df['연도'], errors='coerce')
            national_df = national_df.sort_values(by='연도')

            # 인구 추이 그래프
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(national_df['연도'], national_df['인구'], marker='o', label='Population')

            # 최근 3년 평균 출생/사망자수로 인구 예측
            recent = national_df.tail(3)
            avg_birth = recent['출생아수(명)'].mean()
            avg_death = recent['사망자수(명)'].mean()
            net_increase = avg_birth - avg_death
            last_year = national_df['연도'].max()
            last_pop = national_df[national_df['연도'] == last_year]['인구'].values[0]
            forecast_year = 2035
            forecast_pop = last_pop + (forecast_year - last_year) * net_increase

            # 예측 결과 추가
            ax.plot(forecast_year, forecast_pop, marker='x', color='red', markersize=10, label='Forecast (2035)')
            ax.axvline(x=forecast_year, linestyle='--', color='gray', alpha=0.6)

            ax.set_title("Population Trend (National, Yearly)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

            st.markdown(f"""
                - 📍 **Forecast for 2035**: {forecast_pop:,.0f}  
                - Based on average net increase: ({avg_birth:,.0f} - {avg_death:,.0f}) = {net_increase:,.0f}  
                - Last year in data: {int(last_year)}, Population: {int(last_pop):,}
            """)

        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("📊 Regional Population Change (Last 5 Years)")

            # '전국' 제외한 지역만 사용
            region_df = df[df['지역'] != '전국'].copy()

            # 연도 숫자화 및 정렬
            region_df['연도'] = pd.to_numeric(region_df['연도'], errors='coerce')
            region_df = region_df.sort_values(by=['지역', '연도'])

            # 최근 5년 기준
            latest_year = region_df['연도'].max()
            base_year = latest_year - 5

            # 기준 연도, 최신 연도별 인구만 추출
            base_df = region_df[region_df['연도'] == base_year][['지역', '인구']].rename(columns={'인구': '인구_5년전'})
            latest_df = region_df[region_df['연도'] == latest_year][['지역', '인구']].rename(columns={'인구': '인구_최근'})

            merged = pd.merge(base_df, latest_df, on='지역')
            merged['증감_천명'] = (merged['인구_최근'] - merged['인구_5년전']) / 1000
            merged['증감률(%)'] = ((merged['인구_최근'] - merged['인구_5년전']) / merged['인구_5년전']) * 100

            # 지역명 영어로 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
                '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            merged['Region'] = merged['지역'].map(region_map)

            # 내림차순 정렬
            merged_sorted = merged.sort_values(by='증감_천명', ascending=False)

            # 증감량 그래프
            fig1, ax1 = plt.subplots(figsize=(10, 7))
            sns.barplot(x='증감_천명', y='Region', data=merged_sorted, ax=ax1, palette='coolwarm')

            for i, v in enumerate(merged_sorted['증감_천명']):
                ax1.text(v + 10, i, f'{v:.1f}K', va='center')

            ax1.set_title("Population Change (Last 5 Years)", fontsize=14)
            ax1.set_xlabel("Change (Thousands)")
            ax1.set_ylabel("Region")

            st.pyplot(fig1)

            st.markdown(
                "> **Interpretation**: This chart shows the population change in thousands for each region over the past 5 years. Regions with strong urbanization trends, like Gyeonggi and Sejong, tend to show growth, while more rural regions show population decline.")

            # 변화율 그래프
            fig2, ax2 = plt.subplots(figsize=(10, 7))
            sns.barplot(x='증감률(%)', y='Region', data=merged_sorted, ax=ax2, palette='crest')

            for i, v in enumerate(merged_sorted['증감률(%)']):
                ax2.text(v + 0.2, i, f'{v:.1f}%', va='center')

            ax2.set_title("Population Growth Rate (%)", fontsize=14)
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("Region")

            st.pyplot(fig2)

            st.markdown(
                "> **Interpretation**: Some regions (e.g., Sejong) show relatively high percentage increases despite small absolute growth due to a smaller population base. Meanwhile, areas with decreasing trend (like Jeonbuk, Gyeongbuk) show negative rates.")

        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("📉 Top 100 Annual Population Changes by Region")

            # 전국 제외, 연도 정렬
            region_df = df[df['지역'] != '전국'].copy()
            region_df['연도'] = pd.to_numeric(region_df['연도'], errors='coerce')
            region_df = region_df.sort_values(by=['지역', '연도'])

            # 연도별 인구 증감(diff) 계산
            region_df['증감'] = region_df.groupby('지역')['인구'].diff()

            # 상위 100개 증감값 정렬
            top_diff = region_df.dropna(subset=['증감']).copy()
            top_diff = top_diff.sort_values(by='증감', ascending=False)
            top_100 = pd.concat([top_diff.head(50), top_diff.tail(50)]).sort_values(by='증감', ascending=False)

            # 천단위 콤마 처리
            top_100['인구'] = top_100['인구'].apply(lambda x: f"{int(x):,}")
            top_100['증감'] = top_100['증감'].apply(lambda x: f"{int(x):,}")

            # 시각 강조용 스타일링 함수 정의
            def highlight_diff(val):
                try:
                    val_num = int(val.replace(',', ''))
                    color = '#c6f1ff' if val_num > 0 else '#ffc6c6'
                except:
                    color = 'white'
                return f'background-color: {color}'

            styled_df = top_100[['연도', '지역', '인구', '증감']].style \
                .applymap(highlight_diff, subset=['증감']) \
                .set_properties(**{'text-align': 'center'}) \
                .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

            st.markdown("### Top 100 Largest Annual Population Changes")
            st.dataframe(styled_df, use_container_width=True)
            st.markdown(
                "> **Interpretation**: Blue highlights indicate population increase years, while red highlights indicate population decline. "
                "This view helps detect major demographic shifts (e.g., new city growth or population outflow)."
            )

        # 5. 시각화
        with tabs[4]:
            st.header("📊 Stacked Area Chart by Region and Year")

            # 전국 제외 데이터
            region_df = df[df['지역'] != '전국'].copy()

            # 연도 숫자형
            region_df['연도'] = pd.to_numeric(region_df['연도'], errors='coerce')

            # 지역명 영어로 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
                '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            region_df['Region'] = region_df['지역'].map(region_map)

            # 피벗 테이블 생성
            pivot_df = region_df.pivot_table(index='연도', columns='Region', values='인구', aggfunc='sum')
            pivot_df = pivot_df.fillna(0)

            # 그래프 그리기
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_df.plot.area(ax=ax, cmap='tab20')  # tab20: 많은 범주에 적절한 색상 팔레트
            ax.set_title("Population by Region (Stacked Area)", fontsize=14)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0), title='Region')
            ax.grid(True)

            st.pyplot(fig)

            st.markdown(
                "> **Interpretation**: The stacked area chart visualizes how each region contributes to the overall population across years. "
                "This allows us to see trends such as regional expansion, decline, or stability over time."
            )

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
