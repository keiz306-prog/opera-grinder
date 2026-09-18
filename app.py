import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기",
    page_icon="☕",
    layout="wide"
)

# 1. 세션 스테이트 초기화
if "bean_db" not in st.session_state:
    st.session_state.bean_db = {
        "기본 블렌드 (Default Medium)": {
            "roast": "강배전 (Dark)",
            "base_grind": 1.0,
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
st.sidebar.markdown(f"- 실측 기준 도징량: {bean_info['base_dose']}g")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ 타겟 추출 세팅")

target_grind = st.sidebar.slider("타겟 분쇄도 (단 - 숫자가 클수록 굵음)", 1.0, 10.0, 1.0, step=0.5)
target_dial = st.sidebar.slider("타겟 다이얼 레벨 (클릭)", 1.0, 30.0, 10.5, step=0.5)

extraction_mode = st.sidebar.radio(
    "추출 모드 선택",
    ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"]
)

# --- 메인 헤더 ---
st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.caption("원두 추가/삭제 DB 관리 UI 복구 완료(v3.4) 버전입니다.")

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
    with col_a2:
        # [다이얼 전용 순수 도징량 계산]
        if target_dial <= 11.0:
            calculated_dose = round(12.4 + (target_dial - 11.0) * 2.2, 1)
        else:
            calculated_dose = round(12.4 + (target_dial - 11.0) * 0.6, 1)

        calculated_dose = max(5.0, calculated_dose)

        st.markdown("**2샷 토출 모드 실제 예측 도징량**")
        st.markdown(f"### {calculated_dose} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    # --- 기본더블 피크 압력 산출 ---
    base_pressure_calc = 15.5 - (target_grind * 1.2) - (target_dial * 0.1)
    dose_ratio = calculated_dose / bean_info['base_dose']
    adjusted_pressure = base_pressure_calc * (dose_ratio ** 1.0)

    if "자동" in extraction_mode:
        adjusted_pressure -= 1.5
    
    estimated_peak_pressure = round(max(4.0, min(16.0, adjusted_pressure)), 1)

    # --- [싱글 바스켓 실측 압력 캘리브레이션] ---
    single_peak_press = round(10.5 + (calculated_dose - 11.3) * 0.909, 1)
    single_end_press = round(10.0 + (calculated_dose - 11.3) * 0.455, 1)

    if "자동" in extraction_mode:
        single_peak_press -= 1.5
        single_end_press -= 1.5

    st.markdown("---")
    st.subheader("☕ 바스켓 5종 특성별 예측 결과 (동일 도징량 적용)")
    
    if single_peak_press >= 13.0:
        st.warning(f"🔥 **[고압 실험 구간 (싱글 피크 {single_peak_press} bar)]**: 고저항 셋팅입니다.")
    elif single_peak_press >= 10.0:
        st.info(f"🟡 **[준고압 / 고저항 구간 (싱글 피크 {single_peak_press} bar)]**: 안정권 레벨")
    else:
        st.success(f"🟢 **[표준 추출 구간 (싱글 피크 {single_peak_press} bar)]**: 표준 영역입니다.")

    basket_data = {
        "바스켓 구분": [
            "★ 순정 싱글 비가압", 
            "순정 더블 비가압", 
            "사제 일반 비가압", 
            "IMS [DL2TH26E]", 
            "iKafe 고추출"
        ],
        "높이 (Height)": ["19.0mm", "30.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "예측 도징량": [
            f"{calculated_dose} g",
            f"{calculated_dose} g",
            f"{calculated_dose} g",
            f"{calculated_dose} g",
            f"{calculated_dose} g"
        ],
        "예측 피크 압력 (종료 압력)": [
            f"{single_peak_press} bar ({single_end_press} bar)", 
            f"{estimated_peak_pressure} bar", 
            f"{max(3.0, round(estimated_peak_pressure - 3.0, 1))} bar", 
            f"{max(2.5, round(estimated_peak_pressure - 5.0, 1))} bar", 
            f"{max(2.0, round(estimated_peak_pressure - 5.5, 1))} bar"
        ],
        "예측 평균 유속": [
            f"{round(1.6 * (bean_info['base_dose'] / max(calculated_dose, 5.0)), 1)} g/s",
            f"{round(3.7 * (bean_info['base_dose'] / max(calculated_dose, 5.0)), 1)} g/s", 
            f"{round(4.4 * (bean_info['base_dose'] / max(calculated_dose, 5.0)), 1)} g/s", 
            f"{round(5.2 * (bean_info['base_dose'] / max(calculated_dose, 5.0)), 1)} g/s", 
            f"{round(5.7 * (bean_info['base_dose'] / max(calculated_dose, 5.0)), 1)} g/s"
        ]
    }
    st.dataframe(pd.DataFrame(basket_data), use_container_width=True)

# 2번 탭
with tab2:
    st.subheader("🛠️ Maverick Handmill Single Dosing Calibrator")
    mav_bean_list = list(st.session_state.maverick_bean_db.keys())
    selected_mav_bean = st.selectbox("핸드밀 활성 원두 선택", mav_bean_list, key="mav_select")
    mav_info = st.session_state.maverick_bean_db[selected_mav_bean]
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        manual_dose = st.number_input("타겟 도징량 (g)", 10.0, 25.0, mav_info.get('target_dose', 18.0), 0.1)
        maverick_clicks = st.number_input("핸드밀 분쇄도 (클릭 수)", 1, 50, 15, 1)
    with col_m2:
        st.info(f"**원두명:** {selected_mav_bean}\n\n**배전도:** {mav_info['roast']}\n\n**가공 방식:** {mav_info['processing']}")

# 3번 탭: 원두 프로파일 DB 관리 (추가/삭제 UI 완전 복구)
with tab3:
    st.subheader("🫘 원두 프로파일 DB 관리")
    
    # 1. 현재 등록된 DB 목록 출력
    st.markdown("##### 📋 현재 등록된 원두 목록")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.bean_db, orient='index'), use_container_width=True)
    
    st.markdown("---")
    
    col_db1, col_db2 = st.columns(2)
    
    # 2. 신규 원두 추가 UI
    with col_db1:
        st.markdown("##### ➕ 신규 원두 프로파일 추가")
        with st.form("add_bean_form", clear_on_submit=True):
            new_bean_name = st.text_input("원두 이름", placeholder="예: 과테말라 안티구아")
            new_roast = st.selectbox("배전도", ["약배전 (Light)", "중약배전 (Medium-Light)", "중배전 (Medium)", "중강배전 (Medium-Dark)", "강배전 (Dark)"])
            new_base_grind = st.number_input("기준 분쇄도 (단)", 1.0, 10.0, 1.0, 0.5)
            new_base_dial = st.number_input("기준 다이얼 (클릭)", 1.0, 30.0, 20.0, 0.5)
            new_base_dose = st.number_input("실측 기준 도징량 (g)", 5.0, 30.0, 17.8, 0.1)
            
            submit_btn = st.form_submit_button("➕ 새로운 원두 추가")
            if submit_btn:
                if new_bean_name.strip() != "":
                    st.session_state.bean_db[new_bean_name.strip()] = {
                        "roast": new_roast,
                        "base_grind": new_base_grind,
                        "base_dial": new_base_dial,
                        "base_dose": new_base_dose
                    }
                    st.success(f"'{new_bean_name}' 원두가 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("원두 이름을 입력해주세요.")

    # 3. 기존 원두 삭제 UI
    with col_db2:
        st.markdown("##### 🗑️ 원두 프로파일 삭제")
        if len(st.session_state.bean_db) > 1:
            delete_target = st.selectbox("삭제할 원두 선택", list(st.session_state.bean_db.keys()), key="del_select")
            if st.button("🗑️ 선택한 원두 삭제", type="primary"):
                del st.session_state.bean_db[delete_target]
                st.success(f"'{delete_target}' 원두가 삭제되었습니다.")
                st.rerun()
        else:
            st.warning("최소 1개의 원두 프로파일은 유지되어야 하므로 삭제할 수 없습니다.")

# 4번 탭
with tab4:
    st.subheader("📐 2D 도징 계산 모델 설명")
    st.markdown("- 원두 프로파일 DB 관리 탭에서 자유롭게 원두 등록/삭제가 가능하며, 선택된 원두를 기준으로 동적 예측이 수행됩니다.")