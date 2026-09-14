import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기",
    page_icon="☕",
    layout="wide"
)

# 1. 세션 스테이트 초기화 (오페라 원두 DB & 매버릭 핸드밀 원두 DB)
if "bean_db" not in st.session_state:
    st.session_state.bean_db = {
        "기본 블렌드 (Default Medium)": {
            "roast": "강배전 (Dark)",
            "base_grind": 1,
            "base_dial": 20,
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

# --- 사이드바 (오페라 모드) ---
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

# --- 메인 헤더 ---
st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.caption("타임모어 실측 캘리브레이션(v2.4) 및 원두 DB 관리(수정/삭제)가 통합된 스마트 시뮬레이터입니다.")

# --- 탭 구조 ---
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
        grind_diff = target_grind - bean_info['base_grind']
        calculated_dose = round((bean_info['base_dose'] - (grind_diff * 0.5)) * (target_dial / bean_info['base_dial']), 1)
        st.markdown("**2D 모델 예측 도징량**")
        st.markdown(f"### {calculated_dose} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    st.markdown("---")
    st.subheader("☕ 바스켓 4종 특성별 실측 캘리브레이션 예측 결과 (v2.4)")
    
    basket_data = {
        "바스켓 구분": ["드롱기 순정 비가압", "사제 일반 비가압", "IMS [DL2TH26E]", "iKafe 고추출"],
        "높이 (Height)": ["30.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "예측 도징량": [f"{calculated_dose} g"] * 4,
        "예측 피크 압력": ["12.2 bar", "9.2 bar", "6.9 bar", "6.0 bar"],
        "예측 평균 유속": ["3.2 g/s", "3.8 g/s", "4.5 g/s", "4.9 g/s"]
    }
    st.dataframe(pd.DataFrame(basket_data), use_container_width=True)

# 2번 탭: 매버릭 핸드밀 (약배전 모드)
with tab2:
    st.subheader("🛠️ Maverick Handmill Single Dosing Calibrator")
    st.caption("오페라와 분리된 수동 싱글도징 및 클릭 수 기반 프로파일 영역입니다.")
    
    mav_bean_list = list(st.session_state.maverick_bean_db.keys())
    selected_mav_bean = st.selectbox("핸드밀 활성 원두 선택", mav_bean_list, key="mav_select")
    mav_info = st.session_state.maverick_bean_db[selected_mav_bean]
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("### 🎛️ 수동 타이핑 세팅")
        manual_dose = st.number_input("타겟 도징량 (g)", min_value=10.0, max_value=25.0, value=mav_info.get('target_dose', 18.0), step=0.1)
        maverick_clicks = st.number_input("핸드밀 분쇄도 (클릭 수)", min_value=1, max_value=50, value=15, step=1)
        
    with col_m2:
        st.markdown("### 🫘 선택된 원두 정보")
        st.info(f"**원두명:** {selected_mav_bean}\n\n**배전도:** {mav_info['roast']}\n\n**가공 방식:** {mav_info['processing']}")

    st.markdown("---")
    st.markdown("### 📈 핸드밀 4포인트 측정 결과 맵 (추후 계산식 연동 예정)")
    st.info("타임모어 4개 포인트 데이터 기반 매버릭 핸드밀 전용 예측 맵과 그래프가 이곳에 연동될 예정입니다.")

# 3번 탭: 원두 프로파일 DB 관리 (오페라 DB + 핸드밀 DB 통합)
with tab3:
    st.subheader("🫘 원두 프로파일 DB 관리")
    
    st.markdown("### 1️⃣ 오페라 원두 DB 관리")
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.markdown("#### 오페라 원두 추가 / 수정")
        with st.form("opera_bean_form"):
            new_name = st.text_input("원두명 (Key)")
            new_roast = st.selectbox("배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"])
            new_grind = st.number_input("기준 분쇄도 (단)", 1, 10, 1)
            new_dial = st.number_input("기준 다이얼 (클릭)", 10, 30, 20)
            new_dose = st.number_input("실측 도징량 (g)", 10.0, 25.0, 17.8, 0.1)
            submitted_opera = st.form_submit_button("오페라 원두 저장/업데이트")
            
            if submitted_opera and new_name:
                st.session_state.bean_db[new_name] = {
                    "roast": new_roast,
                    "base_grind": new_grind,
                    "base_dial": new_dial,
                    "base_dose": new_dose
                }
                st.success(f"'{new_name}' 오페라 원두가 저장되었습니다!")
                st.rerun()

    with col_db2:
        st.markdown("#### 등록된 오페라 원두 목록")
        st.dataframe(pd.DataFrame.from_dict(st.session_state.bean_db, orient='index'), use_container_width=True)
        
        del_opera_target = st.selectbox("삭제할 오페라 원두 선택", list(st.session_state.bean_db.keys()), key="del_op")
        if st.button("선택한 오페라 원두 삭제"):
            if len(st.session_state.bean_db) > 1:
                del st.session_state.bean_db[del_opera_target]
                st.success(f"'{del_opera_target}' 원두가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("최소 1개의 원두는 남아있어야 합니다.")

    st.markdown("---")
    st.markdown("### 2️⃣ 매버릭 핸드밀 원두 DB 관리")
    col_mav1, col_mav2 = st.columns(2)
    
    with col_mav1:
        st.markdown("#### 핸드밀 원두 추가 / 수정")
        with st.form("mav_bean_form"):
            mav_name = st.text_input("핸드밀 원두명 (Key)")
            mav_roast = st.selectbox("핸드밀 배전도", ["약배전 (Light)", "중배전 (Medium)"])
            mav_proc = st.text_input("가공 방식", "내추럴 / 워시드")
            mav_dose = st.number_input("기준 도징량 (g)", 10.0, 25.0, 18.0, 0.1)
            submitted_mav = st.form_submit_button("핸드밀 원두 저장/업데이트")
            
            if submitted_mav and mav_name:
                st.session_state.maverick_bean_db[mav_name] = {
                    "roast": mav_roast,
                    "processing": mav_proc,
                    "target_dose": mav_dose
                }
                st.success(f"'{mav_name}' 핸드밀 원두가 저장되었습니다!")
                st.rerun()

    with col_mav2:
        st.markdown("#### 등록된 핸드밀 원두 목록")
        st.dataframe(pd.DataFrame.from_dict(st.session_state.maverick_bean_db, orient='index'), use_container_width=True)
        
        del_mav_target = st.selectbox("삭제할 핸드밀 원두 선택", list(st.session_state.maverick_bean_db.keys()), key="del_mav")
        if st.button("선택한 핸드밀 원두 삭제"):
            if len(st.session_state.maverick_bean_db) > 1:
                del st.session_state.maverick_bean_db[del_mav_target]
                st.success(f"'{del_mav_target}' 핸드밀 원두가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("최소 1개의 원두는 남아있어야 합니다.")

# 4번 탭: 2D 도징 계산 모델 설명
with tab4:
    st.subheader("📐 2D 도징 계산 모델 설명")
    st.markdown("""
    - **분쇄도 편차 계수:** 분쇄도가 굵어질수록 공극 증가 및 밀도 변화를 반영하여 도징량이 유기적으로 보정됩니다.
    - **다이얼 비율 계수:** 다이얼 레벨 변화에 따른 투입 부피 변동을 반영합니다.
    - **매버릭 핸드밀 모드:** 싱글도징 특성에 맞춰 수동 타이핑 입력 및 독립된 원두 프로필 관리를 제공합니다.
    """)