import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기",
    page_icon="☕",
    layout="wide"
)

# 세션 스테이트 초기화 (원두 DB 예시)
if "bean_db" not in st.session_state:
    st.session_state.bean_db = {
        "기본 블렌드 (Default Medium)": {
            "roast": "강배전 (Dark)",
            "base_grind": 1,
            "base_dial": 20,
            "base_dose": 17.8
        }
    }

# 사이드바 컨트롤러 (기본 오페라 모드용)
st.sidebar.markdown("### ⚙️ 원두 및 세팅 컨트롤러")
bean_list = list(st.session_state.bean_db.keys())
active_bean = st.sidebar.selectbox("현재 활성 원두 선택 (Active Bean)", bean_list)

bean_info = st.session_state.bean_db[active_bean]
st.sidebar.markdown(f"**[선택된 원두 정보]**")
st.sidebar.markdown(f"- 배전도: {bean_info['roast']}")
st.sidebar.markdown(f"- 기준 분쇄도: {bean_info['base_grind']}단")
st.sidebar.markdown(f"- 기준 다이얼: {bean_info['base_dial']}클릭")
st.sidebar.markdown(f"- 실측 도징량: {bean_info['base_dose']}g")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ 타겟 추출 세팅")
target_grind = st.sidebar.slider("타겟 분쇄도 (단 - 숫자가 클수록 굵음)", 1, 10, 1)
target_dial = st.sidebar.slider("타겟 다이얼 레벨 (클릭)", 10, 25, 20)
extraction_mode = st.sidebar.radio(
    "추출 모드 선택",
    ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"]
)

# 메인 헤더
st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.caption("타임모어 실측 캘리브레이션(v2.4) 및 원두 DB 관리(수정/삭제)가 통합된 스마트 시뮬레이터입니다.")

# 탭 구조 구성 (매버릭 핸드밀 탭 추가)
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 동적 추출 예측기", 
    "🫘 매버릭 핸드밀 (약배전 모드)", 
    "🫘 원두 프로파일 DB 관리", 
    "📐 2D 도징 계산 모델 설명"
])

# 1번 탭: 동적 추출 예측기 (오페라)
with tab1:
    st.subheader("동적 도징 & 압력/유속 예측 대시보드 (v2.5)")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.markdown("**선택된 활성 원두**")
        st.markdown(f"### {active_bean}")
    with col_a2:
        # 간단한 2D 도징 계산 로직 시뮬레이션
        grind_diff = target_grind - bean_info['base_grind']
        calculated_dose = round((bean_info['base_dose'] - (grind_diff * 0.5)) * (target_dial / bean_info['base_dial']), 1)
        st.markdown("**2D 모델 예측 도징량**")
        st.markdown(f"### {calculated_dose} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    st.markdown("---")
    st.subheader("☕ 바스켓 4종 특성별 실측 캘리브레이션 예측 결과 (v2.4)")
    
    # 예시 데이터프레임
    basket_data = {
        "바스켓 구분": ["드롱기 순정 비가압", "사제 일반 비가압", "IMS [DL2TH26E]", "iKafe 고추출"],
        "높이 (Height)": ["30.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "예측 도징량": [f"{calculated_dose} g"] * 4,
        "예측 피크 압력": ["12.2 bar", "9.2 bar", "6.9 bar", "6.0 bar"],
        "예측 평균 유속": ["3.2 g/s", "3.8 g/s", "4.5 g/s", "4.9 g/s"]
    }
    st.dataframe(pd.DataFrame(basket_data), use_container_width=True)

# 2번 탭: 매버릭 핸드밀 (약배전 모드 - 신규 추가)
with tab2:
    st.subheader("🛠️ 매버릭 핸드밀 싱글도징 캘리브레이터 (약배전 전용)")
    st.caption("오페라와 분리된 수동 싱글도징 및 클릭 수 기반 프로파일 영역입니다.")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("### 🎛️ 수동 타이핑 세팅")
        manual_dose = st.number_input("타겟 도징량 (g)", min_value=10.0, max_value=25.0, value=18.0, step=0.1)
        maverick_clicks = st.number_input("핸드밀 분쇄도 (클릭 수)", min_value=1, max_value=50, value=15, step=1)
        
    with col_m2:
        st.markdown("### 🫘 약배전 원두 프로필 입력")
        bean_name_m = st.text_input("원두명 (약배전)", "에티오피아 예가체프 내추럴")
        roast_note = st.text_input("로스팅 노트 / 가공 방식", "베리, 플로럴, 워시드")

    st.markdown("---")
    st.markdown("### 📈 핸드밀 4포인트 측정 결과 맵 (추후 계산식 연동 예정)")
    st.info("여기에 타임모어 4개 포인트 데이터 기반 매버릭 핸드밀 전용 예측 맵과 그래프가 연동될 예정입니다.")

# 3번 탭: 원두 프로파일 DB 관리
with tab3:
    st.subheader("🫘 원두 프로파일 DB 관리")
    st.write("현재 등록된 원두 목록을 확인하고 관리할 수 있습니다.")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.bean_db, orient='index'), use_container_width=True)

# 4번 탭: 2D 도징 계산 모델 설명
with tab4:
    st.subheader("📐 2D 도징 계산 모델 설명")
    st.markdown("""
    - **분쇄도 편차 계수:** 분쇄도가 굵어질수록 공극 증가 및 밀도 변화를 반영하여 도징량이 유기적으로 보정됩니다.
    - **다이얼 비율 계수:** 다이얼 레벨 변화에 따른 투입 부피 변동을 반영합니다.
    """)