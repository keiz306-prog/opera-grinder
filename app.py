# version: v2.5
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기",
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
st.markdown("타임모어 실측 캘리브레이션(v2.4) 및 원두 DB 관리(수정/삭제)가 통합된 스마트 시뮬레이터입니다.")

# Sidebar for Navigation & Active Bean Selection
st.sidebar.header("⚙️ 원두 및 세팅 컨트롤러")

# Active Bean Selection (안전장치: DB가 비어있을 경우 예외 처리)
if not st.session_state.bean_db.empty:
    bean_names = st.session_state.bean_db["Bean Name"].tolist()
    selected_bean_name = st.sidebar.selectbox("현재 활성 원두 선택 (Active Bean)", bean_names)
    active_bean = st.session_state.bean_db[st.session_state.bean_db["Bean Name"] == selected_bean_name].iloc[0]

    st.sidebar.markdown(f"**[선택된 원두 정보]**\n- 배전도: `{active_bean['Roast']}`\n- 기준 분쇄도: `{active_bean['Grind']}단`\n- 기준 다이얼: `{active_bean['Dial']}클릭`\n- 실측 도징량: `{active_bean['Dose']}g`")
else:
    st.sidebar.warning("등록된 원두가 없습니다. '원두 프로파일 DB 관리' 탭에서 원두를 추가해주세요.")
    active_bean = {"Bean Name": "기본", "Roast": "중배전", "Grind": 1, "Dial": 22, "Dose": 18.0, "Note": ""}

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 타겟 추출 세팅")
target_grind = st.sidebar.slider("타겟 분쇄도 (단 - 숫자가 클수록 굵음)", 1, 10, int(active_bean['Grind']))
target_dial = st.sidebar.slider("타겟 다이얼 레벨 (클릭)", 10, 25, int(active_bean['Dial']))

# Extraction Mode
extraction_mode = st.sidebar.radio("추출 모드 선택", ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"])

# Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 동적 추출 예측기", "🫘 원두 프로파일 DB 관리", "📐 2D 도징 계산 모델 설명"])

with tab1:
    st.header("동적 도징 & 압력/유속 예측 대시보드 (v2.5)")
    
    if st.session_state.bean_db.empty:
        st.info("좌측 사이드바 또는 DB 탭에서 원두를 먼저 등록해 주세요.")
    else:
        base_dose = float(active_bean['Dose'])
        base_dial = float(active_bean['Dial'])
        base_grind = int(active_bean['Grind'])
        
        grind_diff = target_grind - base_grind  
        dial_ratio = target_dial / base_dial if base_dial > 0 else 1.0
        
        calculated_dose = round((base_dose - grind_diff * 0.5) * dial_ratio, 2)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("선택된 활성 원두", active_bean['Bean Name'])
        col2.metric("2D 모델 예측 도징량", f"{calculated_dose} g")
        col3.metric("적용 모드", extraction_mode)
        
        st.markdown("---")
        st.subheader("☕ 바스켓 4종 특성별 실측 캘리브레이션 예측 결과 (v2.4)")
        
        pressure_offset = -1.5 if "자동 커피모드" in extraction_mode else 0.0
        resistance_delta = (base_grind - target_grind) * 0.8 + (calculated_dose - base_dose) * 0.6 + (target_dial - base_dial) * 0.15
        
        base_p = 9.0 + resistance_delta + pressure_offset
        
        # 순정 순서 유지 및 피크 앵커 적용
        p_pure = round(min(12.5, max(4.0, base_p * 1.25 + 1.0)), 1)
        f_pure = round(max(0.8, 3.2 - resistance_delta * 0.3), 1)

        p_third = round(min(9.5, max(3.5, base_p * 1.0 + 0.2)), 1)
        f_third = round(max(1.2, 3.8 - resistance_delta * 0.3), 1)

        p_ims = round(min(7.5, max(2.8, base_p * 0.82 - 0.5)), 1)
        f_ims = round(max(1.7, 4.5 - resistance_delta * 0.3), 1)

        p_ikafe = round(min(6.9, max(2.5, base_p * 0.75 - 0.8)), 1)
        f_ikafe = round(max(1.9, 4.9 - resistance_delta * 0.3), 1)

        df_baskets = pd.DataFrame({
            "바스켓 구분": ["데롱기 순정 비가압", "사제 일반 비가압", "IMS [DL2TH26E]", "iKafe 고추출"],
            "높이 (Height)": ["30.0mm", "22.0mm", "26.0mm", "25.0mm"],
            "예측 도징량": [f"{calculated_dose}g", f"{calculated_dose}g", f"{calculated_dose}g", f"{calculated_dose}g"],
            "예측 피크 압력": [f"{p_pure} bar", f"{p_third} bar", f"{p_ims} bar", f"{p_ikafe} bar"],
            "예측 평균 유속": [f"{f_pure} g/s", f"{f_third} g/s", f"{f_ims} g/s", f"{f_ikafe} g/s"]
        })

        st.dataframe(df_baskets, use_container_width=True)

with tab2:
    st.header("🫘 원두 프로파일 & 캘리브레이션 DB 관리 (v2.5)")
    st.markdown("등록된 원두를 확인하고, 불필요한 프로파일을 **삭제**하거나 기존 값을 **수정**할 수 있습니다.")
    
    if st.session_state.bean_db.empty:
        st.info("현재 등록된 원두가 없습니다.")
    else:
        st.subheader("📋 현재 등록된 원두 목록")
        st.dataframe(st.session_state.bean_db, use_container_width=True)
        
        st.markdown("---")
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            st.subheader("✏️ 기존 원두 프로파일 수정")
            edit_bean_name = st.selectbox("수정할 원두 선택", st.session_state.bean_db["Bean Name"].tolist(), key="edit_select")
            target_row = st.session_state.bean_db[st.session_state.bean_db["Bean Name"] == edit_bean_name].iloc[0]
            
            with st.form("edit_bean_form"):
                e_roast = st.selectbox("배전도 변경", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"], index=["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"].index(target_row['Roast']) if target_row['Roast'] in ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"] else 1)
                e_grind = st.number_input("기준 분쇄도 변경 (단)", min_value=1, max_value=10, value=int(target_row['Grind']))
                e_dial = st.number_input("기준 다이얼 변경 (클릭)", min_value=10, max_value=25, value=int(target_row['Dial']))
                e_dose = st.number_input("실측 도징량 변경 (g)", min_value=10.0, max_value=25.0, value=float(target_row['Dose']), step=0.1)
                e_note = st.text_input("비고 및 노트 변경", value=str(target_row['Note']))
                
                update_submitted = st.form_submit_button("원두 정보 수정하기")
                if update_submitted:
                    st.session_state.bean_db.loc[st.session_state.bean_db["Bean Name"] == edit_bean_name, ["Roast", "Grind", "Dial", "Dose", "Note"]] = [e_roast, e_grind, e_dial, e_dose, e_note]
                    st.success(f"원두 '{edit_bean_name}'의 정보가 성공적으로 수정되었습니다!")
                    st.rerun()

        with col_del:
            st.subheader("🗑️ 원두 프로파일 삭제")
            del_bean_name = st.selectbox("삭제할 원두 선택", st.session_state.bean_db["Bean Name"].tolist(), key="del_select")
            
            if st.button("선택한 원두 삭제하기", type="primary"):
                st.session_state.bean_db = st.session_state.bean_db[st.session_state.bean_db["Bean Name"] != del_bean_name].reset_index(drop=True)
                st.success(f"원두 '{del_bean_name}'이(가) 삭제되었습니다!")
                st.rerun()

    st.markdown("---")
    st.subheader("➕ 신규 원두 프로파일 등록")
    with st.form("new_bean_form"):
        new_name = st.text_input("원두 프로파일 명 (Bean Name)")
        new_roast = st.selectbox("배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"])
        new_grind = st.number_input("기준 분쇄도 (단)", min_value=1, max_value=10, value=1)
        new_dial = st.number_input("기준 다이얼 (클릭)", min_value=10, max_value=25, value=20)
        new_dose = st.number_input("실측 도징량 (g)", min_value=10.0, max_value=25.0, value=18.0, step=0.1)
        new_note = st.text_input("비고 및 노트")
        
        submitted = st.form_submit_button("신규 원두 등록하기")
        if submitted and new_name:
            if new_name in st.session_state.bean_db["Bean Name"].values:
                st.error("이미 존재하는 원두 이름입니다. 다른 이름을 사용해 주세요.")
            else:
                new_row = {"Bean Name": new_name, "Roast": new_roast, "Grind": new_grind, "Dial": new_dial, "Dose": new_dose, "Note": new_note}
                st.session_state.bean_db = pd.concat([st.session_state.bean_db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"새로운 원두 '{new_name}'이(가) 성공적으로 등록되었습니다!")
                st.rerun()

with tab3:
    st.header("📐 모델 물리적 특징 및 안내 (v2.5)")
    st.markdown("""
    - **원두 프로파일 CRUD 지원 (v2.5):** 이제 탭2에서 원두별 기준 값(도징량, 분쇄도, 다이얼)을 자유롭게 수정하거나 불필요한 프로파일을 삭제할 수 있습니다.
    - **타임모어 실측 캘리브레이션 반영:** 순정 비가압(12.5 bar 피크)부터 iKafe(6.9 bar)까지 바스켓별 압력 한계치가 정밀 연동됩니다.
    """)