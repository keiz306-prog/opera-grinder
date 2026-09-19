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
        "과테말라 와이칸 (Wykan)": {
            "roast": "약배전 (Light)",
            "processing": "워시드 (Washed)",
            "target_dose": 16.0
        },
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

target_grind = st.sidebar.slider("타겟 분쇄도 (단 - 숫자가 클수록 굵음)", 1.0, 10.0, 1.0, step=0.5)
target_dial = st.sidebar.slider("타겟 다이얼 레벨 (클릭)", 1.0, 30.0, 20.0, step=0.5)

extraction_mode = st.sidebar.radio(
    "추출 모드 선택",
    ["수동 추출 (Manual - 피크 압력)", "자동 커피모드 (Coffee Mode - 약 1.5 bar 낮음)"]
)

# --- 메인 헤더 ---
st.title("☕ 드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기")
st.caption("타임모어 실측 캘리브레이션 및 매버릭 핸드밀 노-린싱(Dry) 4포인트 정밀 데이터가 통합된 시뮬레이터입니다.")

# --- 탭 구조 ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 동적 추출 예측기", 
    "🫘 매버릭 핸드밀 (약배전 모드)", 
    "🫘 원두 프로파일 DB 관리", 
    "📐 2D 도징 계산 모델 설명"
])

# ==========================================
# 1번 탭: 동적 추출 예측기 (기존 코드 100% 원본 유지)
# ==========================================
with tab1:
    st.subheader("동적 도징 & 압력/유속 예측 대시보드")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.markdown("**선택된 활성 원두**")
        st.markdown(f"### {active_bean}")
    with col_a2:
        grind_diff = target_grind - bean_info['base_grind']
        dial_diff = target_dial - bean_info['base_dial']
        
        calculated_dose = round(bean_info['base_dose'] - (grind_diff * 0.5) + (dial_diff * 0.25), 1)
        calculated_dose = max(5.0, calculated_dose)

        st.markdown("**2D 모델 예측 도징량**")
        st.markdown(f"### {calculated_dose} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    base_pressure_calc = 15.5 - (target_grind * 1.2) - (target_dial * 0.1)
    dose_ratio = calculated_dose / bean_info['base_dose']
    adjusted_pressure = base_pressure_calc * (dose_ratio ** 1.0)

    if "자동" in extraction_mode:
        adjusted_pressure -= 1.5
    
    estimated_peak_pressure = round(max(4.0, min(16.0, adjusted_pressure)), 1)
    single_peak_pressure = round(min(16.0, estimated_peak_pressure + 2.8), 1)

    st.markdown("---")
    st.subheader("☕ 바스켓 5종 특성별 실측 캘리브레이션 예측 결과")
    
    if estimated_peak_pressure >= 13.0:
        pressure_status_msg = f"🔥 **[고압 실험 구간 ({estimated_peak_pressure} bar)]**: 13~14바 이상 고저항 셋팅입니다."
        st.warning(pressure_status_msg)
    elif estimated_peak_pressure >= 10.0:
        pressure_status_msg = f"🟡 **[준고압 / 고저항 구간 ({estimated_peak_pressure} bar)]**: 안정권보다 높은 저항을 주는 세팅입니다."
        st.info(pressure_status_msg)
    else:
        pressure_status_msg = f"🟢 **[표준 추출 구간 ({estimated_peak_pressure} bar)]**: 밸런스가 안정적인 표준 압력 영역입니다."
        st.success(pressure_status_msg)

    base_flow = round(3.2 * (bean_info['base_dose'] / max(calculated_dose, 5.0)), 2)

    basket_data = {
        "바스켓 구분": [
            "★ 순정 싱글 비가압", 
            "순정 더블 비가압 (기준)", 
            "사제 일반 비가압", 
            "IMS [DL2TH26E]", 
            "iKafe 고추출"
        ],
        "높이 (Height)": ["19.0mm", "30.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "도징량": [
            f"{calculated_dose} g",
            f"{calculated_dose} g",
            f"{calculated_dose} g",
            f"{calculated_dose} g",
            f"{calculated_dose} g"
        ],
        "예측 피크 압력": [
            f"{single_peak_pressure} bar", 
            f"{estimated_peak_pressure} bar", 
            f"{max(3.0, round(estimated_peak_pressure - 3.0, 1))} bar", 
            f"{max(2.5, round(estimated_peak_pressure - 5.0, 1))} bar", 
            f"{max(2.0, round(estimated_peak_pressure - 5.5, 1))} bar"
        ],
        "예측 평균 유속": [
            f"{round(base_flow * 0.65, 2)} g/s", 
            f"{base_flow} g/s", 
            f"{round(base_flow * 1.18, 2)} g/s", 
            f"{round(base_flow * 1.40, 2)} g/s", 
            f"{round(base_flow * 1.53, 2)} g/s"
        ]
    }
    st.dataframe(pd.DataFrame(basket_data), use_container_width=True)

# ==========================================
# 2번 탭: 매버릭 핸드밀 (1번 탭과 오프셋 일치 수치 반영)
# ==========================================
with tab2:
    st.subheader("🛠️ Maverick Handmill Single Dosing Calibrator (Dry Filter Baseline)")
    st.caption("수막 현상을 유발하는 린싱(Wet) 데이터를 배제하고, 마른 필터(Dry) 기준 실측 데이터 기반으로 캘리브레이션합니다.")
    
    mav_bean_list = list(st.session_state.maverick_bean_db.keys())
    selected_mav_bean = st.selectbox("핸드밀 활성 원두 선택", mav_bean_list, key="mav_select")
    mav_info = st.session_state.maverick_bean_db[selected_mav_bean]
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("### 🎛️ 추출 세팅 컨트롤")
        manual_dose = st.number_input("타겟 도징량 (g)", min_value=10.0, max_value=25.0, value=mav_info.get('target_dose', 16.0), step=0.1)
        maverick_clicks = st.slider("핸드밀 분쇄도 (클릭 수)", min_value=50, max_value=85, value=77, step=1)
        
    with col_m2:
        st.markdown("### 🫘 선택된 원두 정보")
        st.info(f"**원두명:** {selected_mav_bean}\n\n**배전도:** {mav_info['roast']}\n\n**가공 방식:** {mav_info['processing']}\n\n**추천 조건:** 상/하단 듀얼 마른(Dry) 종이 필터")

    st.markdown("---")
    st.markdown("### 📈 매버릭 핸드밀 약배전 실측 4포인트 데이터 맵 (16.0g / Dry Filter 기준)")
    
    dry_data_df = pd.DataFrame({
        "클릭 수": ["75 클릭", "76 클릭", "77 클릭 (★ 스윗스팟 A)", "78 클릭 (★ 스윗스팟 B)"],
        "추출 시간": ["37 초", "45 초", "37 초", "34 초"],
        "추출량": ["36.8 g", "35.7 g", "36.8 g", "35.3 g"],
        "피크 압력": ["~11.0 bar", "< 11.0 bar", "11.0 bar (안정)", "10.5 ~ 11.5 bar"],
        "유속 및 저항 양상": ["고압 저항유지", "완충구간 (유속늘어짐)", "압력/유속 최적 밸런스", "시원한 물길 (선형성 최상)"],
        "향미 & 마우스필 특징": ["묵직하고 달콤한 진한 주스 질감", "약간 거친 산미 (지연 추출)", "클린컵 극대화 & 묵직한 볼륨감", "과일 향미 직관적 터짐 & 라이트함"]
    })
    st.dataframe(dry_data_df, use_container_width=True)

    st.markdown("#### 🎯 선택된 분쇄도 상태 진단")
    if maverick_clicks == 75:
        st.info("🥤 **[75클릭 - 고농도 텍스처]**: 37초 / 36.8g. 11 bar 고압이 유지되어 단맛이 강하고 진한 주스 같은 질감을 줍니다.")
    elif maverick_clicks == 76:
        st.warning("⚠️ **[76클릭 - 유속 완충 구간]**: 45초 / 35.7g. 고압이 풀어지며 어중간하게 지연 추출이 일어나는 완충 지대로, 산미가 살짝 거칠어질 수 있습니다.")
    elif maverick_clicks == 77:
        st.success("⭐ **[77클릭 - 농도 & 밸런스 스윗스팟]**: 37초 / 36.8g. 찌르는 맛이 제거되고 묵직한 볼륨감과 선명한 클린컵이 동시에 살아나는 추천 분쇄도입니다.")
    elif maverick_clicks == 78:
        st.success("⭐ **[78클릭 - 향미 & 클린컵 스윗스팟]**: 34초 / 35.3g. 압력이 부드럽게 풀리며 과일 고유의 화사한 향미와 산미가 가장 먼저 직관적으로 터지는 추천 분쇄도입니다.")
    elif maverick_clicks < 75:
        st.error("🚨 **[74클릭 이하 - 고압 다짐/초미세 분쇄 구간]**: 11~12 bar 이상 고압으로 치솟거나 퍽 저항이 극도로 커져 정체 가능성이 높습니다.")
    else:
        st.info("💡 **[79클릭 이상 - 라이트 추출]**: 30초 대 안팎으로 빠른 유속을 보여주며, 가벼운 바디감과 라이트한 향미 위주로 추출됩니다.")

    st.markdown("---")
    st.markdown(f"### 🥣 현재 핸드밀 세팅 ({maverick_clicks}클릭 / {manual_dose}g 싱글도징) 기준 5종 바스켓별 예측 시뮬레이션")
    
    click_diff = maverick_clicks - 77
    dose_factor = manual_dose / 16.0
    
    # 기준인 [사제 일반 비가압]의 실측 압력 및 유속 (11.0 bar 기준)
    base_mav_pressure = 11.0 - (click_diff * 0.4) * dose_factor
    base_mav_flow = 1.0 + (click_diff * 0.08) / dose_factor
    
    # 1번 탭의 저항 오프셋 메커니즘 수식 적용
    mav_basket_data = {
        "바스켓 구분": [
            "사제 일반 비가압 (★ 실측 기준)",
            "순정 더블 비가압",
            "★ 순정 싱글 비가압",
            "IMS [DL2TH26E]",
            "iKafe 고추출"
        ],
        "바스켓 높이": ["22.0 mm", "30.0 mm", "19.0 mm", "26.0 mm", "25.0 mm"],
        "도징량 (Single Dosing)": [
            f"{manual_dose} g", 
            f"{manual_dose} g", 
            f"{manual_dose} g", 
            f"{manual_dose} g", 
            f"{manual_dose} g"
        ],
        "예측 피크 압력": [
            f"{max(2.0, round(base_mav_pressure, 1))} bar",                              # 기준: 11.0 bar
            f"{min(16.0, round(base_mav_pressure + 3.0, 1))} bar",                       # 순정 더블: +3.0 bar (14.0 bar)
            f"{min(16.0, round(base_mav_pressure + 5.8, 1))} bar",                       # 순정 싱글: +5.8 bar (16.0 bar 제한)
            f"{max(2.0, round(base_mav_pressure - 2.0, 1))} bar",                        # IMS: -2.0 bar (9.0 bar)
            f"{max(2.0, round(base_mav_pressure - 2.5, 1))} bar"                         # iKafe: -2.5 bar (8.5 bar)
        ],
        "예측 평균 유속": [
            f"{round(base_mav_flow, 2)} g/s",                                           # 기준 1.00 g/s
            f"{round(base_mav_flow * 0.85, 2)} g/s",                                    # 순정 더블
            f"{round(base_mav_flow * 0.55, 2)} g/s",                                    # 순정 싱글
            f"{round(base_mav_flow * 1.18, 2)} g/s",                                    # IMS
            f"{round(base_mav_flow * 1.30, 2)} g/s"                                     # iKafe
        ],
        "바스켓 특성 가이드": [
            "핸드밀 약배전 실측 검증 기준 바스켓. 77~78클릭에서 최상 밸런스",
            "사제 대비 타공 면적이 좁아 동일 도징 시 저항이 +3.0 bar 높음 (14.0 bar 도달)",
            "동일 도징 투입 시 좁고 깊은 테이퍼 구조로 초고저항 발생 (79클릭 이상 권장)",
            "타공 면적이 넓어 고유속 추출. 75~76클릭으로 미세 조정 권장",
            "최고 유속 바스켓. 약배전의 밝은 산미 표현에 유리"
        ]
    }
    
    st.dataframe(pd.DataFrame(mav_basket_data), use_container_width=True)

# ==========================================
# 3번 탭: 원두 프로파일 DB 관리
# ==========================================
with tab3:
    st.subheader("🫘 원두 프로파일 DB 관리")
    
    st.markdown("### 1️⃣ 오페라 원두 DB 관리")
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.markdown("#### 오페라 원두 추가 / 수정")
        with st.form("opera_bean_form"):
            new_name = st.text_input("원두명 (Key)")
            new_roast = st.selectbox("배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"])
            new_grind = st.number_input("기준 분쇄도 (단)", 1.0, 10.0, 1.0, 0.5)
            new_dial = st.number_input("기준 다이얼 (클릭)", 1.0, 30.0, 20.0, 0.5)
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
            mav_roast = st.selectbox("핸드밀 배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"])
            mav_proc = st.text_input("가공 방식", "워시드 / 내추럴")
            mav_dose = st.number_input("기준 도징량 (g)", 10.0, 25.0, 16.0, 0.1)
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

# ==========================================
# 4번 탭: 2D 도징 계산 모델 설명
# ==========================================
with tab4:
    st.subheader("📐 2D 도징 계산 모델 및 Dry Filter 프로파일 설명")
    st.markdown("""
    - **노-린싱(Dry) 필터 기틀 확립:** 하단 종이 필터 린싱 시 발생하는 수막 흡착(Water Film Lock) 변수를 완전 배제하고, 마른 필터 기준으로 매버릭 핸드밀 약배전 영점을 재구축했습니다.
    - **매버릭 4포인트 실측 맵:** 과테말라 와이칸 16.0g 기준 75~78클릭의 비선형 유속 완충 구간(76클릭)과 농도/향미 개별 스윗스팟(77, 78클릭)을 정밀하게 연동했습니다.
    - **핸드밀 싱글 도징 물리 모델:** 핸드밀 탭은 16.0g 원두를 고정 투입하는 싱글 도징 조건을 기본으로 하므로, 모든 바스켓에 동일 도징량이 담길 때 생기는 바스켓 형태별 저항 차이(순정 더블 대비 사제 비가압의 -3.0 bar 저항 감소 등)를 정밀 계산합니다.
    """)