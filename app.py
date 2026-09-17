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

# 0.5단위 미세 조절 및 최소값 1.0 확장 적용
target_dial = st.sidebar.slider(
    "타겟 다이얼 레벨 (0.5단위 조절, 최소 1.0)", 
    min_value=1.0, 
    max_value=25.0, 
    value=float(bean_info['base_dial']), 
    step=0.5
)

extraction_mode = st.sidebar.radio(
    "추출 모드 선택",
    ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"]
)

# --- 메인 헤더 ---
st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.caption("타임모어 실측 캘리브레이션(v2.7) - 순정 싱글 비가압(7.8g / 10bar / 41.7g 수율) 앵커 연동 및 0.5단위 슬라이더 적용")

# --- 탭 구조 ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 동적 추출 예측기", 
    "🫘 매버릭 핸드밀 (약배전 모드)", 
    "🫘 원두 프로파일 DB 관리", 
    "📐 2D 도징 계산 모델 설명"
])

# 1번 탭: 동적 추출 예측기 (오페라)
with tab1:
    st.subheader("동적 도징 & 압력/유속 예측 대시보드 (v2.7 - 싱글 비가압 및 0.5단 저도징 프로필 반영)")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.markdown("**선택된 활성 원두**")
        st.markdown(f"### {active_bean}")
    with col_a2:
        grind_diff = target_grind - bean_info['base_grind']
        
        # 더블 바스켓 예측 도징량 계산
        calculated_dose_double = round((bean_info['base_dose'] - (grind_diff * 0.5)) * (target_dial / bean_info['base_dial']), 1)
        
        # 순정 싱글 비가압 바스켓 실측 앵커 연산 (레벨 10 = 실측 7.8g 기준)
        calculated_dose_single = round(7.8 * (target_dial / 10.0) - (grind_diff * 0.25), 1)
        calculated_dose_single = max(0.5, calculated_dose_single)
        
        st.markdown("**2D 모델 예측 도징량**")
        st.markdown(f"### 더블: {calculated_dose_double} g | 싱글: {calculated_dose_single} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    # --- 압력 산출 로직 ---
    # 1. 더블 바스켓 기본 압력
    base_pressure_calc = 15.5 - (target_grind * 1.2) - (target_dial * 0.1)
    dose_ratio_double = calculated_dose_double / max(bean_info['base_dose'], 1.0)
    adjusted_pressure_double = base_pressure_calc * (dose_ratio_double ** 1.0)
    if "자동" in extraction_mode:
        adjusted_pressure_double -= 1.5
    estimated_peak_pressure_double = round(max(3.0, min(16.0, adjusted_pressure_double)), 1)

    # 2. 순정 싱글 비가압 바스켓 전용 압력 (레벨 10 / 분쇄도 1에서 10.0 bar 실측 앵커 적용)
    single_base_pressure = 10.0 - ((target_grind - 1) * 1.5) + ((target_dial - 10.0) * 0.4)
    if "자동" in extraction_mode:
        single_base_pressure -= 1.5
    estimated_peak_pressure_single = round(max(2.0, min(15.0, single_base_pressure)), 1)

    st.markdown("---")
    st.subheader("☕ 바스켓 5종 특성별 실측 캘리브레이션 예측 결과")
    
    if estimated_peak_pressure_double >= 13.0:
        st.warning(f"🔥 **[더블 고압 실험 구간 ({estimated_peak_pressure_double} bar)]**: 13~14바 이상 고저항 세팅입니다.")
    elif estimated_peak_pressure_double >= 10.0:
        st.info(f"🟡 **[더블 준고압 / 고저항 구간 ({estimated_peak_pressure_double} bar)]**: 안정권보다 높은 저항 세팅입니다.")
    else:
        st.success(f"🟢 **[더블 표준 추출 구간 ({estimated_peak_pressure_double} bar)]**: 밸런스가 안정적인 압력 영역입니다.")

    # 유속 산출 (더블 및 싱글 실측치 기반)
    double_flow_base = round(3.2 * (bean_info['base_dose'] / max(calculated_dose_double, 5.0)), 1)
    # 싱글 실측: 레벨 10(7.8g)에서 41.7g / 48s ≈ 0.87 g/s
    single_flow_rate = round(0.87 * (7.8 / max(calculated_dose_single, 1.0)), 1)

    basket_data = {
        "바스켓 구분": [
            "드롱기 순정 더블 비가압", 
            "드롱기 순정 싱글 비가압 ⭐[신규]", 
            "사제 일반 비가압", 
            "IMS [DL2TH26E]", 
            "iKafe 고추출"
        ],
        "높이 (Height)": ["30.0mm", "19.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "예측 도징량": [
            f"{calculated_dose_double} g", 
            f"{calculated_dose_single} g", 
            f"{calculated_dose_double} g", 
            f"{calculated_dose_double} g", 
            f"{calculated_dose_double} g"
        ],
        "예측 피크 압력": [
            f"{estimated_peak_pressure_double} bar", 
            f"{estimated_peak_pressure_single} bar", 
            f"{max(3.0, round(estimated_peak_pressure_double - 3.0, 1))} bar", 
            f"{max(2.5, round(estimated_peak_pressure_double - 5.0, 1))} bar", 
            f"{max(2.0, round(estimated_peak_pressure_double - 5.5, 1))} bar"
        ],
        "예측 평균 유속": [
            f"{double_flow_base} g/s", 
            f"{single_flow_rate} g/s", 
            f"{round(double_flow_base * 1.19, 1)} g/s", 
            f"{round(double_flow_base * 1.41, 1)} g/s", 
            f"{round(double_flow_base * 1.53, 1)} g/s"
        ],
        "특징 및 추출 팁": [
            "더블 샷 표준 스윗스팟 (22.5 다이얼 권장)",
            "2샷 모드 적용 시 퍽의 물 흡수량 감소로 약 40~42g 추출 (11.0~11.5 다이얼 권장)",
            "유속이 빠르고 깔끔한 뉘앙스",
            "넓은 타공 면적으로 산미 표현 우수 및 고수율",
            "초고수율 / 클린컵 추출 특성"
        ]
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
        manual_dose = st.number_input("타겟 도징량 (g)", min_value=5.0, max_value=25.0, value=mav_info.get('target_dose', 18.0), step=0.1)
        maverick_clicks = st.number_input("핸드밀 분쇄도 (클릭 수)", min_value=1, max_value=50, value=15, step=1)
        
    with col_m2:
        st.markdown("### 🫘 선택된 원두 정보")
        st.info(f"**원두명:** {selected_mav_bean}\n\n**배전도:** {mav_info['roast']}\n\n**가공 방식:** {mav_info['processing']}")

    st.markdown("---")
    st.markdown("### 📈 핸드밀 4포인트 측정 결과 맵 (추후 계산식 연동 예정)")
    st.info("타임모어 4개 포인트 데이터 기반 매버릭 핸드밀 전용 예측 맵과 그래프가 이곳에 연동될 예정입니다.")

# 3번 탭: 원두 프로파일 DB 관리
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
            new_dial = st.number_input("기준 다이얼 (클릭/레벨)", 1.0, 30.0, 20.0, 0.5)
            new_dose = st.number_input("실측 도징량 (g)", 5.0, 25.0, 17.8, 0.1)
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
            mav_dose = st.number_input("기준 도징량 (g)", 5.0, 25.0, 18.0, 0.1)
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
                st.success(f"'{del_mav_target}' 원두가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("최소 1개의 원두는 남아있어야 합니다.")

# 4번 탭: 2D 도징 계산 모델 설명
with tab4:
    st.subheader("📐 2D 도징 계산 모델 설명 (v2.7 Update)")
    st.markdown("""
    - **0.5단위 미세 도징 슬라이더 지원:** 다이얼 레벨 최소값을 1.0까지 낮추고 0.5단위 조절을 지원하여 저도징 세팅 편의성을 향상했습니다.
    - **드롱기 순정 싱글 비가압 바스켓 프로필 연동:** 
      - **실측 앵커 포인트:** 분쇄도 1단 / 도징 레벨 10 / 실측 무게 **7.8g** / 피크 압력 **10 bar** / 48초 간 **41.7g** 추출
      - **수분 보유량 물리 보정:** 적은 원두량(7.8g)으로 인해 퍽 내부 수분 흡수량이 감소하여 2샷 모드 적용 시 잔으로 떨어지는 실제 추출량이 ~41.7g으로 증가하는 수리학적 특성을 연산 모델에 통합했습니다.
    - **분쇄도 편차 계수:** 분쇄도가 굵어질수록 공극 증가 및 밀도 변화를 반영하여 도징량이 유기적으로 보정됩니다.
    - **도징-압력 정방향 연동:** 도징량이 줄어들면 퍽의 저항이 감소하여 피크 압력도 비례해서 낮아지도록 물리적 인과관계를 유지합니다.
    - **고압 실험 구간 연동 (13~14바+):** 1단 부근의 고저항 구간에서 13~14바 이상의 고압 피크가 16바 스케일 내에서 정상 반영됩니다.
    """)