import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기",
    page_icon="☕",
    layout="wide"
)

# 1. 세션 스테이트 초기화 (기존 롤백 구조 유지)
if "bean_db" not in st.session_state:
    st.session_state.bean_db = {
        "기본 블렌드 (Default Medium)": {
            "roast": "강배전 (Dark)",
            "base_grind": 1,
            "base_dial": 20.0,
            "base_dose": 17.8
        }
    }

if "maverick_bean_db" not in st.session_state:
    st.session_state.maverick_bean_db = {
        "에티오피아 예가체프 내추럴": {
            "roast": "약배전 (Light)",
            "processing": "내추럴 (Natural)",
            "target_dose": 18.0
        }
    }

# --- 사이드바 ---
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

target_dial = st.sidebar.slider(
    "타겟 다이얼 레벨 (0.5단위 조절)", 
    min_value=1.0, 
    max_value=25.0, 
    value=20.0,
    step=0.5
)

extraction_mode = st.sidebar.radio(
    "추출 모드 선택",
    ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"]
)

# --- 메인 헤더 ---
st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.caption("v4.0 Update - 더블 바스켓 완전 롤백 및 오늘 자 싱글 바스켓 실측 데이터(10.5/11.0클릭) 독립 보정")

# --- 탭 구조 ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 동적 추출 예측기", 
    "🫘 매버릭 핸드밀 (약배전 모드)", 
    "🫘 원두 프로파일 DB 관리", 
    "📐 2D 도징 계산 모델 설명"
])

# 1번 탭: 동적 추출 예측기
with tab1:
    st.subheader("동적 도징 & 압력/유속 예측 대시보드")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.markdown("**선택된 활성 원두**")
        st.markdown(f"### {active_bean}")
        
    grind_diff = target_grind - bean_info['base_grind']

    # ==========================================
    # [독립 연산식 1] 더블 바스켓 도징 및 압력 (롤백 원본 유지)
    # ==========================================
    # 기준: 1단 20클릭 ➔ 17.8g / 11.5 bar ➔ 10.0 bar 감쇄
    calculated_dose_double = round(max(1.0, bean_info['base_dose'] + (target_dial - bean_info['base_dial']) * 0.644 - (grind_diff * 0.5)), 1)
    
    base_pressure_double = 11.5 - (grind_diff * 1.2) - ((bean_info['base_dial'] - target_dial) * 0.4)
    if "자동" in extraction_mode:
        base_pressure_double -= 1.5
    estimated_peak_double = round(max(3.0, min(16.0, base_pressure_double)), 1)
    estimated_end_double = round(max(2.0, estimated_peak_double - 1.5), 1)
    flow_double = round(3.2 * (bean_info['base_dose'] / max(calculated_dose_double, 5.0)), 1)

    # ==========================================
    # [독립 연산식 2] 싱글 바스켓 신규 실측 앵커 적용
    # ==========================================
    # 오늘 자 실측 포인트: 10.5클릭(11.0g) / 11.0클릭(12.0g)
    single_dose_base = 11.0 + (target_dial - 10.5) * 2.0  # 10.5~11.0 구간 기울기 반영
    calculated_dose_single = round(max(0.5, single_dose_base - (grind_diff * 0.5)), 1)
    
    # 싱글 압력/유속 모델
    single_peak_base = 10.5 + (target_dial - 10.5) * 2.0
    if "자동" in extraction_mode:
        single_peak_base -= 1.5
    estimated_peak_single = round(max(2.0, min(15.0, single_peak_base - (grind_diff * 1.3))), 1)
    flow_single = round(max(0.3, 1.2 - (target_dial - 10.5) * 0.8), 2)
    est_time_single = int(round(42.9 / max(flow_single, 0.1)))

    with col_a2:
        st.markdown("**그라인더 예측 토출량 (더블 기준)**")
        st.markdown(f"### {calculated_dose_double} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    st.markdown("---")
    st.subheader("☕ 바스켓 5종 특성별 실측 캘리브레이션 예측 결과")

    basket_data = {
        "바스켓 구분": [
            "★ 순정 싱글 비가압 (신규 실측)", 
            "순정 더블 비가압 (기준 롤백)", 
            "사제 일반 비가압", 
            "IMS [DL2TH26E]", 
            "iKafe 고추출"
        ],
        "높이 (Height)": ["19.0mm", "30.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "예측 도징량": [
            f"{calculated_dose_single} g",
            f"{calculated_dose_double} g",
            f"{calculated_dose_double} g",
            f"{calculated_dose_double} g",
            f"{calculated_dose_double} g"
        ],
        "예측 압력 프로파일": [
            f"{estimated_peak_single} bar", 
            f"{estimated_peak_double} bar ➔ {estimated_end_double} bar", 
            f"{max(3.0, round(estimated_peak_double - 3.0, 1))} bar", 
            f"{max(2.5, round(estimated_peak_double - 5.0, 1))} bar", 
            f"{max(2.0, round(estimated_peak_double - 5.5, 1))} bar"
        ],
        "예측 평균 유속": [
            f"{flow_single} g/s", 
            f"{flow_double} g/s", 
            f"{round(flow_double * 1.19, 1)} g/s", 
            f"{round(flow_double * 1.41, 1)} g/s", 
            f"{round(flow_double * 1.53, 1)} g/s"
        ],
        "예측 추출 시간 (약 43g 기준)": [
            f"{est_time_single} 초",
            f"{int(43 / max(flow_double, 0.1))} 초",
            f"{int(43 / max(flow_double * 1.19, 0.1))} 초",
            f"{int(43 / max(flow_double * 1.41, 0.1))} 초",
            f"{int(43 / max(flow_double * 1.53, 0.1))} 초"
        ]
    }
    st.dataframe(pd.DataFrame(basket_data), use_container_width=True)

# 2번 탭: 매버릭 핸드밀 (약배전 모드)
with tab2:
    st.subheader("🛠️ Maverick Handmill Single Dosing Calibrator")
    mav_bean_list = list(st.session_state.maverick_bean_db.keys())
    selected_mav_bean = st.selectbox("핸드밀 활성 원두 선택", mav_bean_list, key="mav_select")
    mav_info = st.session_state.maverick_bean_db[selected_mav_bean]
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("### 🎛️ 수동 세팅")
        manual_dose = st.number_input("타겟 도징량 (g)", min_value=5.0, max_value=25.0, value=mav_info.get('target_dose', 18.0), step=0.1)
        maverick_clicks = st.number_input("핸드밀 분쇄도 (클릭 수)", min_value=1, max_value=50, value=15, step=1)
    with col_m2:
        st.markdown("### 🫘 원두 정보")
        st.info(f"**원두명:** {selected_mav_bean}\n\n**배전도:** {mav_info['roast']}\n\n**가공 방식:** {mav_info['processing']}")

# 3번 탭: DB 관리
with tab3:
    st.subheader("🫘 원두 프로파일 DB 관리")
    st.markdown("### 오페라 원두 목록")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.bean_db, orient='index'), use_container_width=True)

# 4번 탭: 모델 설명
with tab4:
    st.subheader("📐 모델 연산 구조 설명")
    st.markdown("""
    - **더블 바스켓:** 롤백된 기존 안정화 수식 적용 (1단 20클릭 기준 17.8g / 11.5➔10.0 bar)
    - **싱글 바스켓:** 오늘 측정된 10.5클릭(11.0g) 및 11.0클릭(12.0g)을 독립 앵커로 설정하여 간섭 제거
    """)