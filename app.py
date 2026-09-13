import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="드롱기 라 스페셜리스타 에스프레소 추출 예측기",
    page_icon="☕",
    layout="wide"
)

# Initialize session state for Bean DB if not exists
if "bean_db" not in st.session_state:
    st.session_state.bean_db = pd.DataFrame([
        {"Bean Name": "기본 블렌드 (Default Medium)", "Roast": "중배전", "Grind": 1, "Dial": 22, "Dose": 18.3, "Note": "기본 레퍼런스 원두"},
        {"Bean Name": "싱글 오리진 에티오피아 (Light)", "Roast": "약배전", "Grind": 2, "Dial": 18, "Dose": 15.3, "Note": "산미 위주 약배전"},
        {"Bean Name": "다크 로스트 블렌드 (Dark)", "Roast": "강배전", "Grind": 1, "Dial": 20, "Dose": 17.2, "Note": "묵직한 바디감"}
    ])

st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.markdown("바스켓 물리적 특성, 2D 도징 선형성, 그리고 원두별 캘리브레이션을 통합한 스마트 추출 시뮬레이터입니다.")

# Sidebar for Navigation & Active Bean Selection
st.sidebar.header("⚙️ 원두 및 세팅 컨트롤러")

# Active Bean Selection
bean_names = st.session_state.bean_db["Bean Name"].tolist()
selected_bean_name = st.sidebar.selectbox("현재 활성 원두 선택 (Active Bean)", bean_names)

# Get active bean details
active_bean = st.session_state.bean_db[st.session_state.bean_db["Bean Name"] == selected_bean_name].iloc[0]

st.sidebar.markdown(f"**[선택된 원두 정보]**\n- 배전도: `{active_bean['Roast']}`\n- 기준 분쇄도: `{active_bean['Grind']}단`\n- 기준 다이얼: `{active_bean['Dial']}클릭`\n- 실측 도징량: `{active_bean['Dose']}g`")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 타겟 추출 세팅")
target_grind = st.sidebar.slider("타겟 분쇄도 (단)", 1, 10, int(active_bean['Grind']))
target_dial = st.sidebar.slider("타겟 다이얼 레벨 (클릭)", 10, 25, int(active_bean['Dial']))

# Extraction Mode
extraction_mode = st.sidebar.radio("추출 모드 선택", ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"])

# Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 동적 추출 예측기", "🫘 원두 프로파일 DB 관리", "📐 2D 도징 계산 모델 설명"])

with tab1:
    st.header("동적 도징 & 압력/유속 예측 대시보드")
    
    # Corrected Dynamic Dosing Logic based on Active Bean Baseline
    base_dose = float(active_bean['Dose'])
    base_dial = float(active_bean['Dial'])
    base_grind = int(active_bean['Grind'])
    
    grind_diff = target_grind - base_grind
    dial_ratio = target_dial / base_dial if base_dial > 0 else 1.0
    
    # Proportional scaling anchored on the selected active bean baseline
    calculated_dose = round((base_dose + grind_diff * 1.0) * dial_ratio, 2)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("선택된 활성 원두", selected_bean_name)
    col2.metric("2D 모델 예측 도징량", f"{calculated_dose} g")
    col3.metric("적용 모드", extraction_mode)
    
    st.markdown("---")
    st.subheader("☕ 바스켓 4종 특성별 예측 결과")
    
    # Pressure offset for Coffee Mode
    pressure_offset = -1.5 if "자동 커피모드" in extraction_mode else 0.0
    
    baskets_data = []
    
   # 1. 순정 비가압 (30mm) - 깊은 바스켓, 여유 공간 큼
    p_pure = round(max(3.0, min(9.5, ((calculated_dose - 15.3) * 2.0 + 6.0) + pressure_offset)), 1)
    f_pure = round(max(2.5, 5.5 - (calculated_dose - 15.3) * 1.5), 1)
    baskets_data.append({"바스켓 구분": "데롱기 순정 비가압", "깊이": "30.0mm", "예측 도징량": f"{calculated_dose}g", "예측 압력": f"{p_pure} bar", "예측 피크 유속": f"{f_pure} g/s"})

    # 2. 사제 일반 비가압 (22mm) - 얕아서 쉽게 압이 참
    p_third = round(max(3.0, min(9.0, ((calculated_dose - 15.3) * 1.5 + 5.0) + pressure_offset)), 1)
    f_third = round(max(2.8, 6.0 - (calculated_dose - 15.3) * 1.5), 1)
    baskets_data.append({"바스켓 구분": "사제 일반 비가압", "깊이": "22.0mm", "예측 도징량": f"{calculated_dose}g", "예측 압력": f"{p_third} bar", "예측 피크 유속": f"{f_third} g/s"})

    # 3. IMS (26.5mm) - 정밀 바스켓, 안정적인 흐름 (기본 베이스 압력 상향 조정)
    p_ims = round(max(4.0, min(9.8, ((calculated_dose - 18.3) * 1.8 + 7.2) + pressure_offset)), 1)
    f_ims = round(max(2.2, 4.8 - (calculated_dose - 18.3) * 1.2), 1)
    baskets_data.append({"바스켓 구분": "IMS (DL2TH26E)", "깊이": "26.5mm", "예측 도징량": f"{calculated_dose}g", "예측 압력": f"{p_ims} bar", "예측 피크 유속": f"{f_ims} g/s"})

    # 4. iKafe 고추출 (25mm) - 고추출 구조 특유의 저항감 반영
    p_ikafe = round(max(3.5, min(9.5, ((calculated_dose - 17.2) * 1.6 + 6.8) + pressure_offset)), 1)
    f_ikafe = round(max(2.4, 4.5 - (calculated_dose - 17.2) * 1.2), 1)
    baskets_data.append({"바스켓 구분": "iKafe 고추출", "깊이": "25.0mm", "예측 도징량": f"{calculated_dose}g", "예측 압력": f"{p_ikafe} bar", "예측 피크 유속": f"{f_ikafe} g/s"})

    df_baskets = pd.DataFrame(baskets_data)
    st.dataframe(df_baskets, use_container_width=True)

with tab2:
    st.header("🫘 원두 프로파일 & 캘리브레이션 DB 관리")
    st.markdown("새로운 원두를 추가하거나 기존 원두의 기준 실측값(분쇄도, 다이얼, 도징량)을 관리할 수 있습니다.")
    
    st.dataframe(st.session_state.bean_db, use_container_width=True)
    
    st.subheader("➕ 신규 원두 프로파일 등록")
    with st.form("new_bean_form"):
        new_name = st.text_input("원두 프로파일 명 (Bean Name)")
        new_roast = st.selectbox("배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"])
        new_grind = st.number_input("기준 분쇄도 (단)", min_value=1, max_value=10, value=1)
        new_dial = st.number_input("기준 다이얼 (클릭)", min_value=10, max_value=25, value=20)
        new_dose = st.number_input("실측 도징량 (g)", min_value=10.0, max_value=25.0, value=18.0, step=0.1)
        new_note = st.text_input("비고 및 노트")
        
        submitted = st.form_submit_button("원두 등록하기")
        if submitted and new_name:
            new_row = {"Bean Name": new_name, "Roast": new_roast, "Grind": new_grind, "Dial": new_dial, "Dose": new_dose, "Note": new_note}
            st.session_state.bean_db = pd.concat([st.session_state.bean_db, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"새로운 원두 '{new_name}'이(가) 성공적으로 등록되었습니다!")
            st.rerun()

with tab3:
    st.header("📐 모델 물리적 특징 및 안내")
    st.markdown("""
    - **기준값 앵커 연동:** 선택된 활성 원두의 기준 분쇄도, 다이얼, 실측 도징량을 정확한 기준점으로 삼아 타겟 세팅에 따른 증감 비율을 계산합니다.
    - **자동 커피모드 오프셋:** 자동 모드 진입 시 펌프 압력 거동을 반영하여 수동 대비 약 1.5 bar 낮아지는 점을 자동 계산합니다.
    """)