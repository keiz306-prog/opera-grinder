import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# 페이지 기본 설정
st.set_page_config(
    page_title="드롱기 라 스페셜리스타 오페라 에스프레소 추출 예측기",
    page_icon="☕",
    layout="wide"
)

DB_FILE_PATH = "beans_db.json"

# --- 세션 스테이트 및 JSON DB 로드/저장 안전 장치 ---
def init_session_state():
    if os.path.exists(DB_FILE_PATH):
        try:
            with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                if "global_anchors" in saved_data:
                    st.session_state.global_anchors = saved_data["global_anchors"]
                if "global_anchor_bean_name" in saved_data:
                    st.session_state.global_anchor_bean_name = saved_data["global_anchor_bean_name"]
                if "bean_db" in saved_data:
                    st.session_state.bean_db = saved_data["bean_db"]
                if "maverick_bean_db" in saved_data:
                    st.session_state.maverick_bean_db = saved_data["maverick_bean_db"]
        except Exception:
            pass

    # 전역 앵커 기본값 세팅
    if "global_anchors" not in st.session_state or not st.session_state.global_anchors:
        st.session_state.global_anchors = [
            [10.5, 11.3],
            [11.0, 12.4],
            [20.0, 17.8],
            [0.0, 0.0]
        ]
        
    if "global_anchor_bean_name" not in st.session_state:
        st.session_state.global_anchor_bean_name = "콜롬비아 안티구아"

    # 오페라 원두 DB 기본값
    if "bean_db" not in st.session_state or not st.session_state.bean_db:
        st.session_state.bean_db = {
            "기본 블렌드 (Default Medium)": {
                "roast": "강배전 (Dark)",
                "roast_date": str(datetime.now().date()),
                "base_grind": 1.0,
                "base_dial": 20.0,
                "base_dose": 17.8,
                "base_pressure": 11.5,
                "base_dial_2": 0.0,
                "base_dose_2": 0.0,
                "base_pressure_2": 0.0
            }
        }

    # 매버릭 핸드밀 원두 DB 기본값 (다중 포인트 3세트 필드 확장)
    if "maverick_bean_db" not in st.session_state or not st.session_state.maverick_bean_db:
        st.session_state.maverick_bean_db = {
            "과테말라 와이칸 (Wykan)": {
                "roast": "약배전 (Light)",
                "processing": "워시드 (Washed)",
                "roast_date": str(datetime.now().date()),
                "ref_click": 77.0,
                "ref_pressure": 11.0,
                "target_dose": 16.0,
                "ref_click_2": 75.0,
                "ref_pressure_2": 12.0,
                "target_dose_2": 14.0,
                "ref_click_3": 73.0,
                "ref_pressure_3": 14.0,
                "target_dose_3": 12.0
            },
            "에티오피아 예가체프 내추럴": {
                "roast": "약배전 (Light)",
                "processing": "내추럴 (Natural)",
                "roast_date": str(datetime.now().date()),
                "ref_click": 77.0,
                "ref_pressure": 10.5,
                "target_dose": 18.0,
                "ref_click_2": 0.0,
                "ref_pressure_2": 0.0,
                "target_dose_2": 0.0,
                "ref_click_3": 0.0,
                "ref_pressure_3": 0.0,
                "target_dose_3": 0.0
            }
        }

def save_data():
    data_to_save = {
        "global_anchors": st.session_state.global_anchors,
        "global_anchor_bean_name": st.session_state.global_anchor_bean_name,
        "bean_db": st.session_state.bean_db,
        "maverick_bean_db": st.session_state.maverick_bean_db
    }
    with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# 초기화 실행
init_session_state()

# --- 전역 앵커 및 원두 개별 포인트 반영 계산 로직 (오페라용) ---
def calculate_bean_dose(target_dial, bean_info):
    custom_anchors = [list(st.session_state.global_anchors[0]), list(st.session_state.global_anchors[1]), list(st.session_state.global_anchors[2]), list(st.session_state.global_anchors[3])]
    
    d2 = float(bean_info.get("base_dial_2", 0.0))
    g2 = float(bean_info.get("base_dose_2", 0.0))
    if d2 > 0.0 and g2 > 0.0:
        custom_anchors.append([d2, g2])

    valid_anchors = [a for a in custom_anchors if len(a) == 2 and a[0] > 0.0 and a[1] > 0.0]
    if not valid_anchors:
        valid_anchors = [[10.5, 11.3], [11.0, 12.4], [20.0, 17.8]]
        
    sorted_pts = sorted(valid_anchors, key=lambda x: x[0])
    
    if target_dial <= sorted_pts[0][0]:
        val = sorted_pts[0][1] if len(sorted_pts) == 1 else sorted_pts[0][1] + (target_dial - sorted_pts[0][0]) * ((sorted_pts[1][1] - sorted_pts[0][1]) / (sorted_pts[1][0] - sorted_pts[0][0]))
    elif target_dial >= sorted_pts[-1][0]:
        val = sorted_pts[-1][1] if len(sorted_pts) == 1 else sorted_pts[-1][1] + (target_dial - sorted_pts[-1][0]) * ((sorted_pts[-1][1] - sorted_pts[-2][1]) / (sorted_pts[-1][0] - sorted_pts[-2][0]))
    else:
        val = sorted_pts[0][1]
        for i in range(len(sorted_pts) - 1):
            x1, y1 = sorted_pts[i]
            x2, y2 = sorted_pts[i+1]
            if x1 <= target_dial <= x2:
                val = y1 + (target_dial - x1) * ((y2 - y1) / (x2 - x1))
                break
    return val

# --- 매버릭 핸드밀 다중 포인트 동적 도징 및 압력 보간 계산 함수 ---
def calculate_maverick_dynamics(target_click, mav_info):
    # 등록된 최대 3개의 실측 포인트 수집 ([클릭, 압력, 도징량])
    points = []
    
    c1 = float(mav_info.get("ref_click", 77.0))
    p1 = float(mav_info.get("ref_pressure", 11.0))
    d1 = float(mav_info.get("target_dose", 16.0))
    if c1 > 0 and p1 > 0 and d1 > 0:
        points.append([c1, p1, d1])
        
    c2 = float(mav_info.get("ref_click_2", 0.0))
    p2 = float(mav_info.get("ref_pressure_2", 0.0))
    d2 = float(mav_info.get("target_dose_2", 0.0))
    if c2 > 0 and p2 > 0 and d2 > 0:
        points.append([c2, p2, d2])
        
    c3 = float(mav_info.get("ref_click_3", 0.0))
    p3 = float(mav_info.get("ref_pressure_3", 0.0))
    d3 = float(mav_info.get("target_dose_3", 0.0))
    if c3 > 0 and p3 > 0 and d3 > 0:
        points.append([c3, p3, d3])
        
    # 유효 포인트가 없거나 1개뿐일 경우 기본값 처리
    if not points:
        return d1, p1
        
    # 클릭 수 기준 오름차순 정렬 (보간 정확도를 위해)
    sorted_pts = sorted(points, key=lambda x: x[0])
    
    # 보간 수행 함수 정의 (클릭 값에 따른 도징량 및 압력 선형 보간)
    def interpolate_value(idx):
        if len(sorted_pts) == 1:
            return sorted_pts[0][idx]
            
        if target_click <= sorted_pts[0][0]:
            x0, y0 = sorted_pts[0][0], sorted_pts[0][idx]
            x1, y1 = sorted_pts[1][0], sorted_pts[1][idx]
            slope = (y1 - y0) / (x1 - x0) if x1 != x0 else 0
            return y0 + (target_click - x0) * slope
            
        elif target_click >= sorted_pts[-1][0]:
            x0, y0 = sorted_pts[-2][0], sorted_pts[-2][idx]
            x1, y1 = sorted_pts[-1][0], sorted_pts[-1][idx]
            slope = (y1 - y0) / (x1 - x0) if x1 != x0 else 0
            return y1 + (target_click - x1) * slope
            
        else:
            for i in range(len(sorted_pts) - 1):
                x0, y0 = sorted_pts[i][0], sorted_pts[i][idx]
                x1, y1 = sorted_pts[i+1][0], sorted_pts[i+1][idx]
                if x0 <= target_click <= x1:
                    slope = (y1 - y0) / (x1 - x0) if x1 != x0 else 0
                    return y0 + (target_click - x0) * slope
            return sorted_pts[0][idx]

    interpolated_dose = interpolate_value(2) # 2번 인덱스가 도징량
    interpolated_press = interpolate_value(1) # 1번 인덱스가 압력
    
    return round(interpolated_dose, 1), round(interpolated_press, 1)

# --- 사이드바 (오페라 모드) ---
st.sidebar.markdown("### ⚙️ 원두 및 세팅 컨트롤러")
bean_list = list(st.session_state.bean_db.keys())
active_bean = st.sidebar.selectbox("현재 활성 원두 선택 (Active Bean)", bean_list)

bean_info = st.session_state.bean_db[active_bean]
st.sidebar.markdown(f"**[선택된 원두 정보]**")
st.sidebar.markdown(f"- 배전도: {bean_info['roast']}")
st.sidebar.markdown(f"- 로스팅 날짜: {bean_info.get('roast_date', '미지정')}")
st.sidebar.markdown(f"- 기준 분쇄도: {bean_info['base_grind']}단")
st.sidebar.markdown(f"- 기준 다이얼 1: {bean_info['base_dial']}클릭 / 도징 1: {bean_info['base_dose']}g")
if float(bean_info.get('base_dial_2', 0.0)) > 0.0:
    st.sidebar.markdown(f"- 기준 다이얼 2: {bean_info['base_dial_2']}클릭 / 도징 2: {bean_info.get('base_dose_2', 0.0)}g")
st.sidebar.markdown(f"- 실측 피크 압력 1: {bean_info.get('base_pressure', 11.5)} bar")
if float(bean_info.get('base_pressure_2', 0.0)) > 0.0:
    st.sidebar.markdown(f"- 실측 피크 압력 2: {bean_info.get('base_pressure_2', 0.0)} bar")

active_anchors = [a for a in st.session_state.global_anchors if len(a) == 2 and a[0] > 0.0 and a[1] > 0.0]
st.sidebar.markdown(f"- 공통 앵커 포인트: **총 {len(active_anchors)}개 작동 중**")

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
st.caption("타임모어 실측 캘리브레이션 및 매버릭 핸드밀 다중 포인트(고분쇄 저도징) 보간 모델이 적용된 시뮬레이터입니다.")

# --- 탭 구조 재배치 ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 동적 추출 예측기", 
    "🫘 매버릭 핸드밀 (약배전 모드)", 
    "🫘 오페라 원두 DB 관리", 
    "🫘 핸드밀 원두 DB 관리",
    "🎯 글로벌 앵커값 설정",
    "📐 2D 도징 계산 모델 설명"
])

# ==========================================
# 1번 탭: 동적 추출 예측기
# ==========================================
with tab1:
    st.subheader("동적 도징 & 압력/유속 예측 대시보드")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.markdown("**선택된 활성 원두**")
        st.markdown(f"### {active_bean}")
    with col_a2:
        interpolated_dose = calculate_bean_dose(target_dial, bean_info)
        grind_diff = target_grind - bean_info.get('base_grind', 1.0)
        calculated_dose = round(interpolated_dose - (grind_diff * 0.3), 1)
        calculated_dose = max(5.0, calculated_dose)

        st.markdown("**2D 모델 예측 도징량**")
        st.markdown(f"### {calculated_dose} g")
    with col_a3:
        st.markdown("**적용 모드**")
        st.markdown(f"### {extraction_mode}")

    raw_base_press = float(bean_info.get('base_pressure', 11.5))
    p2 = float(bean_info.get('base_pressure_2', 0.0))
    d2_val = float(bean_info.get('base_dial_2', 0.0))
    
    if p2 > 0.0 and d2_val > 0.0:
        d1_val = float(bean_info.get('base_dial', 20.0))
        p1_val = raw_base_press
        if abs(d2_val - d1_val) > 0.1:
            raw_base_press = p1_val + (target_dial - d1_val) * ((p2 - p1_val) / (d2_val - d1_val))
        else:
            raw_base_press = p1_val

    dial_diff = target_dial - float(bean_info.get('base_dial', 20.0))
    base_pressure_calc = raw_base_press - (grind_diff * 1.2) - (dial_diff * 0.15)
    dose_ratio = calculated_dose / max(float(bean_info['base_dose']), 5.0)
    adjusted_pressure = base_pressure_calc * (dose_ratio ** 0.8)

    if "자동" in extraction_mode:
        adjusted_pressure -= 1.5
    
    estimated_peak_pressure = round(max(4.0, min(16.0, adjusted_pressure)), 1)
    single_peak_pressure = round(min(16.0, estimated_peak_pressure + 2.8), 1)

    st.markdown("---")
    st.subheader("☕ 바스켓 5종 특성별 실측 캘리브레이션 예측 결과")
    
    if estimated_peak_pressure >= 13.0:
        st.warning(f"🔥 **[고압 실험 구간 ({estimated_peak_pressure} bar)]**: 13~14바 이상 고저항 셋팅입니다.")
    elif estimated_peak_pressure >= 10.0:
        st.info(f"🟡 **[준고압 / 고저항 구간 ({estimated_peak_pressure} bar)]**: 안정권보다 높은 저항을 주는 세팅입니다.")
    else:
        st.success(f"🟢 **[표준 추출 구간 ({estimated_peak_pressure} bar)]**: 밸런스가 안정적인 표준 압력 영역입니다.")

    base_flow = round(3.2 * (float(bean_info['base_dose']) / max(calculated_dose, 5.0)), 2)

    basket_data = {
        "바스켓 구분": [
            "★ 순정 싱글 비가압", 
            "순정 더블 비가압 (기준)", 
            "사제 일반 비가압", 
            "IMS [DL2TH26E]", 
            "iKafe 고추출"
        ],
        "높이 (Height)": ["19.0mm", "30.0mm", "22.0mm", "26.0mm", "25.0mm"],
        "도징량": [f"{calculated_dose} g"] * 5,
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
# 2번 탭: 매버릭 핸드밀 (약배전 모드)
# ==========================================
with tab2:
    st.subheader("🛠️ Maverick Handmill Multi-Point Calibrator (Dry Filter Baseline)")
    st.caption("고분쇄 저도징(예: 77클릭/11bar/16g ➔ 75클릭/12bar/14g ➔ 73클릭/14bar/12g) 다중 실측 포인트를 반영한 동적 시뮬레이터입니다.")
    
    mav_bean_list = list(st.session_state.maverick_bean_db.keys())
    selected_mav_bean = st.selectbox("핸드밀 활성 원두 선택", mav_bean_list, key="mav_select")
    mav_info = st.session_state.maverick_bean_db[selected_mav_bean]
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("### 🎛️ 추출 세팅 컨트롤")
        maverick_clicks = st.slider("핸드밀 분쇄도 (클릭 수)", min_value=50, max_value=85, value=int(mav_info.get('ref_click', 77.0)), step=1, key="mav_clicks_slider")
        
        # 다중 포인트 보간 로직 적용으로 추천 도징량 자동 계산
        interpolated_mav_dose, interpolated_mav_press = calculate_maverick_dynamics(float(maverick_clicks), mav_info)
        
        manual_dose = st.number_input(
            "타겟 도징량 (g) [다중 포인트 보간 연동값]", 
            min_value=8.0, 
            max_value=25.0, 
            value=interpolated_mav_dose, 
            step=0.1,
            key=f"dose_input_{selected_mav_bean}"
        )
        
    with col_m2:
        st.markdown("### 🫘 선택된 원두 물리 파라미터 & 등록 포인트")
        st.info(
            f"**원두명:** {selected_mav_bean}\n\n"
            f"**배전도:** {mav_info['roast']} | **가공:** {mav_info['processing']}\n\n"
            f"**포인트 1:** {mav_info.get('ref_click', 77)}클릭 / {mav_info.get('ref_pressure', 11)}bar / {mav_info.get('target_dose', 16)}g\n\n"
            f"**포인트 2:** {mav_info.get('ref_click_2', 0)}클릭 / {mav_info.get('ref_pressure_2', 0)}bar / {mav_info.get('target_dose_2', 0)}g\n\n"
            f"**포인트 3:** {mav_info.get('ref_click_3', 0)}클릭 / {mav_info.get('ref_pressure_3', 0)}bar / {mav_info.get('target_dose_3', 0)}g"
        )

    st.markdown("---")
    st.subheader(f"☕ 현재 원두 세팅 ({selected_mav_bean} / {maverick_clicks}클릭 / {manual_dose}g) 기준 5종 바스켓별 동적 예측 시뮬레이션")
    
    mav_estimated_peak = interpolated_mav_press
    mav_single_peak = round(min(16.0, mav_estimated_peak + 2.5), 1)
    mav_base_flow = round(3.2 * (manual_dose / 16.0), 2)

    mav_basket_data = {
        "바스켓 구분": [
            "사제 일반 비가압 (기준)", 
            "순정 더블 비가압", 
            "★ 순정 싱글 비가압", 
            "IMS [DL2TH26E]", 
            "iKafe 고추출"
        ],
        "바스켓 높이": ["22.0mm", "30.0mm", "19.0mm", "26.0mm", "25.0mm"],
        "도징량 (동적 연동)": [f"{manual_dose} g"] * 5,
        "예측 피크 압력": [
            f"{mav_estimated_peak} bar", 
            f"{max(4.0, round(mav_estimated_peak + 2.5, 1))} bar", 
            f"{mav_single_peak} bar", 
            f"{max(3.0, round(mav_estimated_peak - 2.0, 1))} bar", 
            f"{max(2.5, round(mav_estimated_peak - 2.5, 1))} bar"
        ],
        "예측 평균 유속": [
            f"{mav_base_flow} g/s", 
            f"{round(mav_base_flow * 0.85, 2)} g/s", 
            f"{round(mav_base_flow * 0.65, 2)} g/s", 
            f"{round(mav_base_flow * 1.18, 2)} g/s", 
            f"{round(mav_base_flow * 1.3, 2)} g/s"
        ],
        "고분쇄 저도징 연동 반응": [
            "다중 포인트 보간으로 도징량과 압력이 유기적으로 반영됨",
            "도징량이 줄어들어 고분쇄(가늘게)에서도 과압 및 채널링 방지",
            "좁고 깊은 테이퍼 구조로 클린컵 극대화 세팅",
            "고유속 바스켓 특성 반영",
            "밝은 산미와 균형 잡힌 추출 유도"
        ]
    }
    st.dataframe(pd.DataFrame(mav_basket_data), use_container_width=True)

# ==========================================
# 3번 탭: 오페라 원두 DB 관리
# ==========================================
with tab3:
    st.subheader("🫘 오페라 원두 프로파일 DB 관리")
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.markdown("#### 오페라 원두 추가 / 수정")
        with st.form("opera_bean_form"):
            new_name = st.text_input("원두명 (Key)")
            new_roast = st.selectbox("배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"])
            new_roast_date = st.date_input("로스팅 날짜", value=datetime.now())
            
            st.markdown("---")
            st.markdown("**[포인트 1 (기본 기준)]**")
            new_grind = 1.0 
            new_dial = st.number_input("기준 다이얼 1 (클릭)", 1.0, 30.0, 20.0, 0.5)
            new_dose = st.number_input("실측 도징량 1 (g)", 10.0, 25.0, 17.8, 0.1)
            new_press = st.number_input("실측 피크 압력 1 (bar)", 1.0, 16.0, 11.5, 0.1)

            st.markdown("---")
            st.markdown("**[포인트 2 (선택 사항 - 미입력 시 0)]**")
            new_dial_2 = st.number_input("기준 다이얼 2 (클릭)", 0.0, 30.0, 0.0, 0.5)
            new_dose_2 = st.number_input("실측 도징량 2 (g)", 0.0, 25.0, 0.0, 0.1)
            new_press_2 = st.number_input("실측 피크 압력 2 (bar)", 0.0, 16.0, 0.0, 0.1)
            
            submitted_opera = st.form_submit_button("오페라 원두 저장/업데이트")
            
            if submitted_opera and new_name:
                st.session_state.bean_db[new_name] = {
                    "roast": new_roast,
                    "roast_date": str(new_roast_date),
                    "base_grind": new_grind,
                    "base_dial": new_dial,
                    "base_dose": new_dose,
                    "base_pressure": new_press,
                    "base_dial_2": new_dial_2,
                    "base_dose_2": new_dose_2,
                    "base_pressure_2": new_press_2
                }
                save_data()
                st.success(f"'{new_name}' 오페라 원두가 저장되었습니다!")
                st.rerun()

    with col_db2:
        st.markdown("#### 등록된 오페라 원두 목록 및 삭제")
        opera_df = pd.DataFrame.from_dict(st.session_state.bean_db, orient='index')
        display_cols = [c for c in ["roast", "roast_date", "base_dial", "base_dose", "base_pressure", "base_dial_2", "base_dose_2", "base_pressure_2"] if c in opera_df.columns]
        st.dataframe(opera_df[display_cols].rename(columns={
            "roast": "배전도",
            "roast_date": "로스팅 날짜",
            "base_dial": "다이얼1",
            "base_dose": "도징1(g)",
            "base_pressure": "압력1(bar)",
            "base_dial_2": "다이얼2",
            "base_dose_2": "도징2(g)",
            "base_pressure_2": "압력2(bar)"
        }), use_container_width=True)
        
        del_opera_target = st.selectbox("삭제할 오페라 원두 선택", list(st.session_state.bean_db.keys()), key="del_op")
        if st.button("선택한 오페라 원두 삭제"):
            if len(st.session_state.bean_db) > 1:
                del st.session_state.bean_db[del_opera_target]
                save_data()
                st.success(f"'{del_opera_target}' 원두가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("최소 1개의 원두는 남아있어야 합니다.")

# ==========================================
# 4번 탭: 매버릭 핸드밀 원두 DB 관리 (3세트 다중 포인트 지원)
# ==========================================
with tab4:
    st.subheader("🫘 매버릭 핸드밀 원두 프로파일 DB 관리 (총 3세트 다중 포인트)")
    st.caption("고분쇄 저도징 세팅(예: 77클릭/11bar/16g, 75클릭/12bar/14g, 73클릭/14bar/12g)을 입력하여 정밀 보간을 수행하세요. 2·3세트는 값이 없을 경우 0으로 두시면 됩니다.")
    
    col_mav1, col_mav2 = st.columns(2)
    
    with col_mav1:
        st.markdown("#### 핸드밀 원두 추가 / 수정")
        with st.form("mav_bean_form"):
            mav_name = st.text_input("핸드밀 원두명 (Key)")
            mav_roast = st.selectbox("핸드밀 배전도", ["약배전 (Light)", "중배전 (Medium)", "강배전 (Dark)"], key="mav_roast_box")
            mav_proc = st.text_input("가공 방식", "워시드 / 내추럴 / 무산소")
            mav_roast_date = st.date_input("로스팅 날짜", value=datetime.now(), key="mav_date")
            
            st.markdown("---")
            st.markdown("**[포인트 1 (필수 기준 세트)]**")
            mav_ref_click = st.number_input("실측 클릭 1", 50.0, 90.0, 77.0, 1.0)
            mav_ref_press = st.number_input("실측 피크 압력 1 (bar)", 1.0, 16.0, 11.0, 0.1)
            mav_dose = st.number_input("실측 도징량 1 (g)", 8.0, 25.0, 16.0, 0.1)
            
            st.markdown("---")
            st.markdown("**[포인트 2 (선택 사항 - 미입력 시 0)]**")
            mav_ref_click_2 = st.number_input("실측 클릭 2 (클릭)", 0.0, 90.0, 75.0, 1.0)
            mav_ref_press_2 = st.number_input("실측 피크 압력 2 (bar)", 0.0, 16.0, 12.0, 0.1)
            mav_dose_2 = st.number_input("실측 도징량 2 (g)", 0.0, 25.0, 14.0, 0.1)

            st.markdown("---")
            st.markdown("**[포인트 3 (선택 사항 - 미입력 시 0)]**")
            mav_ref_click_3 = st.number_input("실측 클릭 3 (클릭)", 0.0, 90.0, 73.0, 1.0)
            mav_ref_press_3 = st.number_input("실측 피크 압력 3 (bar)", 0.0, 16.0, 14.0, 0.1)
            mav_dose_3 = st.number_input("실측 도징량 3 (g)", 0.0, 25.0, 12.0, 0.1)
            
            submitted_mav = st.form_submit_button("핸드밀 원두 저장/업데이트")
            
            if submitted_mav and mav_name:
                st.session_state.maverick_bean_db[mav_name] = {
                    "roast": mav_roast,
                    "processing": mav_proc,
                    "roast_date": str(mav_roast_date),
                    "ref_click": mav_ref_click,
                    "ref_pressure": mav_ref_press,
                    "target_dose": mav_dose,
                    "ref_click_2": mav_ref_click_2,
                    "ref_pressure_2": mav_ref_press_2,
                    "target_dose_2": mav_dose_2,
                    "ref_click_3": mav_ref_click_3,
                    "ref_pressure_3": mav_ref_press_3,
                    "target_dose_3": mav_dose_3
                }
                save_data()
                st.success(f"'{mav_name}' 핸드밀 원두가 저장되었습니다!")
                st.rerun()

    with col_mav2:
        st.markdown("#### 등록된 핸드밀 원두 목록")
        mav_df = pd.DataFrame.from_dict(st.session_state.maverick_bean_db, orient='index')
        st.dataframe(mav_df.rename(columns={
            "roast": "배전도",
            "processing": "가공 방식",
            "roast_date": "로스팅 날짜",
            "ref_click": "클릭1",
            "ref_pressure": "압력1",
            "target_dose": "도징1",
            "ref_click_2": "클릭2",
            "ref_pressure_2": "압력2",
            "target_dose_2": "도징2",
            "ref_click_3": "클릭3",
            "ref_pressure_3": "압력3",
            "target_dose_3": "도징3"
        }), use_container_width=True)
        
        del_mav_target = st.selectbox("삭제할 핸드밀 원두 선택", list(st.session_state.maverick_bean_db.keys()), key="del_mav")
        if st.button("선택한 핸드밀 원두 삭제"):
            if len(st.session_state.maverick_bean_db) > 1:
                del st.session_state.maverick_bean_db[del_mav_target]
                save_data()
                st.success(f"'{del_mav_target}' 핸드밀 원두가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("최소 1개의 원두는 남아있어야 합니다.")

# ==========================================
# 5번 탭: 글로벌 앵커값 설정
# ==========================================
with tab5:
    st.subheader("🎯 기계 공통 4포인트 글로벌 앵커값 설정")
    st.caption("모든 오페라 원두 계산의 뼈대가 되는 공통 앵커값을 전역적으로 조정합니다.")
    
    col_t5_1, col_t5_2 = st.columns([1.2, 1.0])
    
    with col_t5_1:
        st.markdown("#### ✍️ 글로벌 앵커 큰 틀 입력 및 저장")
        with st.form("global_anchor_setting_form"):
            g_bean_name = st.text_input(
                "기준 원두 이름", 
                value=st.session_state.global_anchor_bean_name
            )
            st.markdown("---")
            
            new_global_anchors = []
            for i in range(4):
                curr_data = st.session_state.global_anchors[i] if i < len(st.session_state.global_anchors) else [0.0, 0.0]
                curr_d = float(curr_data[0]) if len(curr_data) > 0 else 0.0
                curr_g = float(curr_data[1]) if len(curr_data) > 1 else 0.0
                
                c1, c2 = st.columns(2)
                with c1:
                    d_val = st.number_input(f"글로벌 앵커 {i+1} - 다이얼(클릭)", min_value=0.0, max_value=30.0, value=curr_d, step=0.5, key=f"g_anchor_d_{i}")
                with c2:
                    g_val = st.number_input(f"글로벌 앵커 {i+1} - 도징량(g)", min_value=0.0, max_value=25.0, value=curr_g, step=0.1, key=f"g_anchor_g_{i}")
                
                new_global_anchors.append([d_val, g_val])
                
            submitted_g_anchors = st.form_submit_button("글로벌 앵커 큰 틀 저장 반영")
            
            if submitted_g_anchors:
                st.session_state.global_anchor_bean_name = g_bean_name
                st.session_state.global_anchors = new_global_anchors
                save_data()
                st.success("글로벌 앵커 설정이 성공적으로 업데이트되었습니다!")
                st.rerun()

    with col_t5_2:
        st.markdown("#### 📊 현재 적용 중인 글로벌 앵커 큰 틀 표")
        
        anchor_table_data = []
        common_name = st.session_state.global_anchor_bean_name
        
        for idx, anc in enumerate(st.session_state.global_anchors):
            d_v = float(anc[0]) if len(anc) > 0 else 0.0
            g_v = float(anc[1]) if len(anc) > 1 else 0.0
            
            if d_v > 0.0 and g_v > 0.0:
                status_str = f"포인트 {idx+1} 활성"
                val_str = f"{d_v} 클릭 / {g_v} g"
            else:
                status_str = f"포인트 {idx+1} 미사용"
                val_str = "미설정 (0)"
                
            anchor_table_data.append({
                "구분": status_str,
                "글로벌값": val_str
            })
            
        st.markdown(f"**📌 적용 기준 원두:** `{common_name}`")
        st.dataframe(pd.DataFrame(anchor_table_data), use_container_width=True)
        st.info("💡 이 앵커값들은 모든 오페라 원두 계산에 공통 적용되는 뼈대 역할을 합니다.")

# ==========================================
# 6번 탭: 2D 도징 계산 모델 설명
# ==========================================
with tab6:
    st.subheader("📐 2D 도징 계산 모델 및 다중 포인트 보간 설명")
    st.markdown("""
    - **매버릭 핸드밀 다중 포인트 보간:** `클릭 수`, `실측 피크 압력`, `실측 도징량` 세트를 최대 3개까지 입력받아 고분쇄 저도징 세팅 시의 동적 흐름을 완벽하게 계산합니다.
    - **유연한 데이터 적용:** 추가 세트(2·3세트)는 입력하지 않거나 0으로 두면 기본 포인트 1만 작동하며, 입력된 값 사이 구간은 선형 보간을 통해 매끄럽게 연결됩니다.
    - **오페라 & 핸드밀 분리 관리:** 오페라 원두 DB와 매버릭 핸드밀 DB가 각각 최적의 물리 모델에 맞춰 독자적으로 작동합니다.
    """)