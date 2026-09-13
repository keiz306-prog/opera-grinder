# version: v2.2
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
target_grind = st.sidebar.slider("타겟 분쇄도 (단 - 숫자가 클수록 굵음)", 1, 10, int(active_bean['Grind']))
target_dial = st.sidebar.slider("타겟 다이얼 레벨 (클릭)", 10, 25, int(active_bean['Dial']))

# Extraction Mode
extraction_mode = st.sidebar.radio("추출 모드 선택", ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"])

# Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 동적 추출 예측기", "🫘 원두 프로파일 DB 관리", "📐 2D 도징 계산 모델 설명"])

with tab1:
    st.header("동적 도징 & 압력/유속 예측 대시보드")
    
    base_dose = float(active_bean['Dose'])
    base_dial = float(active_bean['Dial'])
    base_grind = int(active_bean['Grind'])
    
    grind_diff = target_grind - base_grind  
    dial_ratio = target_dial / base_dial if base_dial > 0 else 1.0
    
    calculated_dose = round((base_dose - grind_diff * 0.5) * dial_ratio, 2)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("선택된 활성 원두", selected_bean_name)
    col2.metric("2D 모델 예측 도징량", f"{calculated_dose} g")
    col3.metric("적용 모드", extraction_mode)
    
    st.markdown("---")
    st.subheader("☕ 바스켓 4종 특성별 예측 결과 (v2.2 엄격한 물리 위계 보정)")
    
    pressure_offset = -1.5 if "자동 커피모드" in extraction_mode else 0.0
    resistance_delta = (base_grind - target_grind) * 0.8 + (calculated_dose - base_dose) * 0.6 + (target_dial - base_dial) * 0.15
    
    base_p = 7.0 + resistance_delta + pressure_offset
    
    # [v2.2 철저한 순서 보장: 순정(30mm) > IMS(26mm) > 사제 일반(22mm) > iKafe(25mm)]
    # 1. 데롱기 순정 비가압 (30.0mm) - 가장 깊고 저항 높음
    p_pure = round(max(3.0, min(9.8, base_p * 1.15 + 0.9)), 1)
    f_pure = round(max(1.5, 4.0 - resistance_delta * 0.4), 1)

    # 2. IMS Competition [DL2TH26E] (26.0mm) - 정밀 가공으로 탄탄한 중고압 유지
    p_ims = round(max(3.0, min(9.5, base_p * 1.08 + 0.5)), 1)
    f_ims = round(max(1.8, 4.4 - resistance_delta * 0.4), 1)

    # 3. 사제 일반 비가압 (22.0mm) - IMS보다 얕으므로 확실하게 IMS 아래로 고정
    p_third = round(max(2.5, min(9.0, base_p * 0.96 - 0.2)), 1)
    f_third = round(max(2.0, 5.0 - resistance_delta * 0.4), 1)

    # 4. iKafe 고추출 (25.0mm) - 고유 설계로 가장 원활한 유속 및 부드러운 압력
    p_ikafe = round(max(2.2, min(8.8, base_p * 0.90 - 0.6)), 1)
    f_ikafe = round(max(2.2, 5.5 - resistance_delta * 0.4), 1)

    df_baskets = pd.DataFrame({
        "바스켓 구분": ["데롱기 순정 비가압", "IMS [DL2TH26E]", "사제 일반 비가압", "iKafe 고추출"],
        "높이 (Height)": ["30.0mm", "26.0mm", "22.0mm", "25.0mm"],
        "예측 도징량": [f"{calculated_dose}g", f"{calculated_dose}g", f"{calculated_dose}g", f"{calculated_dose}g"],
        "예측 압력": [f"{p_pure} bar", f"{p_ims} bar", f"{p_third} bar", f"{p_ikafe} bar"],
        "예측 피크 유속": [f"{f_pure} g/s", f"{f_ims} g/s", f"{f_third} g/s", f"{f_ikafe} g/s"]
    })

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
    - **정방향 물리 법칙 반영:** 분쇄도를 굵게(숫자 증가) 갈면 퍽 저항이 줄어들어 압력이 낮아지고 유속이 빨라집니다.
    - **IMS 공식 스펙 반영:** 공식 [DL2TH26E Competition Filter Basket](https://www.imsfiltri.com/filters/DL2TH26E.html) 스펙(높이 26 mm)이 정확히 반영되었습니다.
    - **엄격한 압력 위계 정렬:** 순정(30mm) > IMS [DL2TH26E] (26mm) > 사제 일반 비가압(22mm) > iKafe 고추출(25mm) 순서로 압력과 유속 체계가 완벽히 고정되었습니다.
    """)