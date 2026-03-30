import streamlit as st
import datetime
import pandas as pd
import os
import json
import base64
import streamlit.components.v1 as components

# ==========================================
# 1. 공급자 정보 및 데이터 로드 
# ==========================================
st.set_page_config(page_title="Jayden Coffee 시스템", layout="wide")

HISTORY_FILE = "jayden_sales_history.csv"
CLIENTS_FILE = "jayden_clients.json"
SEAL_IMAGE_PATH = "stamp.png" 

PROVIDER = {
    "상호": "제이든 커피 로스터스 (Jayden Coffee Roasters)",
    "등록번호": "409-41-27363",
    "대표자": "이재용",
    "주소": "경기도 하남시 덕풍북로6번길 122, 1층(덕풍동)",
    "TEL": "02-442-0168",
    "계좌": "국민은행 810101-04-162168 (예금주: 이재용)"
}

def load_clients():
    if not os.path.exists(CLIENTS_FILE): return {}
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_clients(data):
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜", "연월", "거래처", "품목", "수량(kg)", "매출액(원)"])
    df = pd.read_csv(HISTORY_FILE)
    df["날짜"] = pd.to_datetime(df["날짜"], format="%Y-%m-%d", errors='coerce').dt.date
    return df.dropna(subset=["날짜"])

clients = load_clients()

# ==========================================
# 2. 강력한 CSS (인쇄 설정 유지)
# ==========================================
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    else:
        st.warning(f"📁 '{path}' 파일을 찾을 수 없습니다. 도장 없이 발행됩니다.")
        return ""

seal_base64 = get_base64_image(SEAL_IMAGE_PATH)

COMMON_STYLE = f"""
<style>
/* 1. 화면용 스타일 */
.report-box {{ 
    border: 2px solid #000; padding: 30px; background: white; 
    color: black !important; font-family: 'Malgun Gothic', sans-serif; 
    margin-bottom: 20px;
}}
.info-container {{ width: 100%; table-layout: fixed; border-collapse: collapse; border: none; margin-bottom: 10px; }}
.biz-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
.biz-table td {{ border: 1px solid #000; padding: 6px; text-align: center; font-size: 11px; height: 28px; color: black; }}
.title-td {{ background: #f2f2f2 !important; font-weight: bold; width: 30%; }}
.content-td {{ width: 70%; text-align: left !important; padding-left: 10px !important; position: relative; }}

.item-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; table-layout: fixed; }}
.item-table th, .item-table td {{ border: 1px solid #000; padding: 8px; text-align: center; font-size: 12px; color: black; }}
.item-table th {{ background: #f2f2f2; }}

.footer-info {{ font-size: 15px; font-weight: bold; margin-top: 20px; border-top: 2px solid #000; padding-top: 10px; color: black; }}

/* 도장 배치 스타일 */
.stamp-image {{
    position: absolute;
    right: 15px; 
    top: -8px; 
    width: 45px; 
    height: 45px;
    opacity: 0.95; 
}}

/* 인쇄용 강력한 스타일 */
@media print {{
    div[data-testid="stToolbar"], header, footer, [data-testid="stSidebar"], [role="tablist"], .hide-on-print, .stButton {{
        display: none !important;
    }}
    body {{ background: white !important; }}
    * {{ -webkit-print-color-adjust: exact !important; color-adjust: exact !important; }}
    .main .block-container {{ padding: 0 !important; margin: 0 !important; }}
    
    .report-box {{ 
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        border: 2px solid #000 !important;
        margin: 0 !important;
        padding: 20px !important;
        z-index: 9999;
        background: white !important;
        visibility: visible !important;
    }}
}}
</style>
"""
st.markdown(COMMON_STYLE, unsafe_allow_html=True)

st.markdown('<div class="hide-on-print"><h1 style="text-align:center;">☕ Jayden Coffee Roasters</h1></div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🧾 명세서 발행", "📊 내역 조회/분석", "⚙️ 관리"])

# ==========================================
# 탭 1: 명세서 발행
# ==========================================
with tab1:
    selected_name = st.selectbox("거래처 선택", ["선택하세요"] + list(clients.keys()), key="main_sel")
    if selected_name != "선택하세요":
        c = clients[selected_name]
        
        # --- [신규 기능] 과거 거래내역 불러오기 ---
        df_history = load_history()
        client_history = df_history[df_history["거래처"] == selected_name]
        past_dates = ["새로 작성하기"] + sorted(client_history["날짜"].astype(str).unique().tolist(), reverse=True)
        
        st.write("---")
        load_date = st.selectbox("🔄 과거 거래내역 불러오기 (동일한 주문을 빠르게 복사합니다)", past_dates, key="load_past_date")
        
        loaded_qtys = {}
        if load_date != "새로 작성하기":
            day_data = client_history[client_history["날짜"].astype(str) == load_date]
            for _, r in day_data.iterrows():
                loaded_qtys[r["품목"]] = int(r["수량(kg)"])
        # ------------------------------------------

        col_d, col_v, col_h = st.columns([2, 3, 1])
        with col_d: target_date = st.date_input("발행 일자", value=datetime.date.today())
        with col_v: vat_mode = st.radio("부가세 설정", ["포함", "없음", "별도"], horizontal=True)
        with col_h: hide_prices = st.checkbox("금액 숨기기(납품서)")

        orders = {}
        st.write("---")
        price_data = c.get("prices", {})
        if not price_data: st.warning("원두를 먼저 등록해주세요.")
        else:
            cols = st.columns(3)
            for i, item in enumerate(price_data.keys()):
                def_val = loaded_qtys.get(item, 0)
                orders[item] = cols[i%3].number_input(f"{item} (kg)", min_value=0, step=1, value=def_val, key=f"ord_{item}_{load_date}")

        if st.button("문서 생성 및 매출 저장", type="primary", use_container_width=True):
            t_qty, t_total, t_supply, t_vat = 0, 0, 0, 0
            items_list = []
            save_records = []
            
            for item, qty in orders.items():
                if qty > 0:
                    base_p = price_data[item]
                    if vat_mode == "포함":
                        total = base_p * qty; supply = int(total / 1.1); vat = total - supply; disp_p = int(base_p / 1.1)
                    elif vat_mode == "없음":
                        supply = base_p * qty; vat = 0; total = supply; disp_p = base_p
                    else: # 별도
                        supply = base_p * qty; vat = int(supply * 0.1); total = supply + vat; disp_p = base_p
                    
                    t_qty += qty; t_supply += supply; t_vat += vat; t_total += total
                    items_list.append({"품목": item, "수량": qty, "단가": disp_p, "공급가액": supply, "세액": int(vat), "총액": total})
                    save_records.append({"날짜": str(target_date), "연월": target_date.strftime("%Y-%m"), "거래처": selected_name, "품목": item, "수량(kg)": qty, "매출액(원)": int(total)})

            if items_list:
                header_title = '납 품 서' if hide_prices else '거 래 명 세 서'
                
                cols_count = 6 if not hide_prices else 2
                col_width_style = f"width: {int(100/cols_count)}%;"
                table_header = f"<thead><tr><th style='{col_width_style}'>품목</th><th style='{col_width_style}'>수량</th>" + (f"<th style='{col_width_style}'>단가</th><th style='{col_width_style}'>공급가액</th><th style='{col_width_style}'>세액</th><th style='{col_width_style}'>총액</th>" if not hide_prices else "") + "</tr></thead>"
                
                rows_html = "".join([f"<tr><td>{x['품목']}</td><td>{x['수량']}</td>" + (f"<td>{x['단가']:,}</td><td>{x['공급가액']:,}</td><td>{x['세액']:,}</td><td>{x['총액']:,}</td>" if not hide_prices else "") + "</tr>" for x in items_list])
                footer_row = f"<tr style='background:#f2f2f2; font-weight:bold;'><td>합계</td><td>{t_qty}</td>" + (f"<td>-</td><td>{t_supply:,}</td><td>{int(t_vat):,}</td><td>{int(t_total):,}</td>" if not hide_prices else "") + "</tr>"
                
                stamp_tag = f'<img src="data:image/png;base64,{seal_base64}" class="stamp-image" alt="직인">' if seal_base64 else ''

                report_content = f"""
                <div class="report-box">
                    <h1 style="text-align:center; letter-spacing:15px; margin-bottom:20px;">{header_title}</h1>
                    <table class="info-container">
                        <tr>
                            <td style="width:49%; vertical-align:top;">
                                <table class="biz-table">
                                    <tr><td colspan="2" class="title-td">공급받는 자</td></tr>
                                    <tr><td class="title-td">상호</td><td class="content-td">{selected_name} 귀하</td></tr>
                                    <tr><td class="title-td">등록번호</td><td class="content-td">{c.get('등록번호','')}</td></tr>
                                    <tr><td class="title-td">주소</td><td class="content-td" style="font-size:9px;">{c.get('주소','')}</td></tr>
                                    <tr><td class="title-td">대표자</td><td class="content-td">{c.get('대표자','')}</td></tr>
                                </table>
                            </td>
                            <td style="width:2%;"></td>
                            <td style="width:49%; vertical-align:top;">
                                <table class="biz-table">
                                    <tr><td colspan="2" class="title-td">공 급 자</td></tr>
                                    <tr><td class="title-td">상호</td><td class="content-td">{PROVIDER['상호']}</td></tr>
                                    <tr><td class="title-td">등록번호</td><td class="content-td">{PROVIDER['등록번호']}</td></tr>
                                    <tr><td class="title-td">주소</td><td class="content-td" style="font-size:9px;">{PROVIDER['주소']}</td></tr>
                                    <tr><td class="title-td">대표자</td><td class="content-td">{PROVIDER['대표자']} (인) {stamp_tag}</td></tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    <p style="text-align:right; font-size:11px; margin: 10px 0;">발행일: {target_date}</p>
                    <table class="item-table">
                        {table_header}
                        <tbody>{rows_html}{footer_row}</tbody>
                    </table>
                    <div class="footer-info">{"합계 금액: " + format(int(t_total), ',') + "원 ("+vat_mode+")<br>입금계좌: " + PROVIDER['계좌'] if not hide_prices else ""}</div>
                </div>
                """
                st.markdown(report_content, unsafe_allow_html=True)
                
                st.write("")
                components.html(f"""
                <div style="text-align:center;">
                    <button onclick="window.parent.print()" style="width:100%;height:50px;background-color:#FF4B4B;color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        🖨️ 프린트하기 (Cmd + P)
                    </button>
                </div>
                """, height=70)
                
                full_standalone_html = f"<html><head><meta charset='utf-8'>{COMMON_STYLE}</head><body style='background:white;'>{report_content}</body></html>"
                st.download_button(
                    label="📁 혹시 인쇄가 이상하면 이 파일을 저장해서 여세요 (HTML)",
                    data=full_standalone_html,
                    file_name=f"명세서_{selected_name}_{target_date}.html",
                    mime="text/html",
                    use_container_width=True
                )

                df_old = load_history()
                pd.concat([df_old, pd.DataFrame(save_records)], ignore_index=True).to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
                st.success(f"✅ 매출 장부에 기록되었습니다.")

# ==========================================
# 탭 2: 내역 조회
# ==========================================
with tab2:
    df = load_history()
    if not df.empty:
        st.subheader("📊 기간별 매출 및 거래처 분석")
        dr = st.date_input("조회 기간 설정", [datetime.date.today().replace(day=1), datetime.date.today()])
        
        if len(dr) == 2:
            df_f = df[(df["날짜"] >= dr[0]) & (df["날짜"] <= dr[1])].copy()
            
            # 1. 전체 기간 총 매출 요약
            st.markdown(f"""<div style="background:#f0f2f6;padding:20px;border-radius:15px;text-align:center;border:1px solid #ddd; margin-bottom:20px;">
                <h2 style="margin:0; color:#333;">📅 {dr[0]} ~ {dr[1]} 총 매출 합계</h2>
                <h1 style="color:#FF4B4B; margin:10px 0;">{df_f['매출액(원)'].sum():,} 원 / {df_f['수량(kg)'].sum():,} kg</h1>
            </div>""", unsafe_allow_html=True)
            
            # 2. 거래처별 x 월별 매출 피벗 테이블 (한눈에 보기)
            st.subheader("🏢 거래처별 · 월별 매출 현황 (한눈에 보기)")
            if not df_f.empty:
                # 월별 피벗 테이블 생성
                pivot_df = df_f.pivot_table(index="거래처", columns="연월", values="매출액(원)", aggfunc="sum", fill_value=0)
                pivot_df["총합계"] = pivot_df.sum(axis=1) # 우측 끝에 거래처별 총합 추가
                pivot_df = pivot_df.sort_values("총합계", ascending=False)
                
                # 하단에 '월별 총 판매 금액' 행 추가
                pivot_df.loc["[전체 월별 총계]"] = pivot_df.sum(axis=0)
                
                st.dataframe(pivot_df.style.format("{:,}"), use_container_width=True)
            
            st.write("---")
            
            # 3. 상세 내역 조회
            col_left, col_right = st.columns([2, 3])
            
            with col_left:
                st.write("🏢 **조회 기간 내 거래처별 합산 (수량 포함)**")
                stat = df_f.groupby("거래처")[["수량(kg)", "매출액(원)"]].sum().sort_values("매출액(원)", ascending=False)
                st.dataframe(stat.style.format("{:,}"), use_container_width=True)
                
                sel_c = st.selectbox("상세 내역을 볼 거래처 선택", ["전체보기"] + list(stat.index))

            with col_right:
                st.write(f"📝 **{sel_c} 상세 내역**")
                v_df = df_f if sel_c == "전체보기" else df_f[df_f["거래처"] == sel_c]
                
                if not v_df.empty:
                    if sel_c != "전체보기":
                        st.info(f"📍 {sel_c} 합계 - {v_df['수량(kg)'].sum():,}kg / {v_df['매출액(원)'].sum():,}원")
                    
                    for idx, row in v_df.sort_index(ascending=False).iterrows():
                        c = st.columns([3, 5, 2, 1])
                        c[0].write(row['날짜']); c[1].write(f"**{row['거래처']}**|{row['품목']}({row['수량(kg)']}kg)"); c[2].write(f"{row['매출액(원)']:,}원")
                        if c[3].button("🗑️", key=f"del_{idx}"):
                            df_full = pd.read_csv(HISTORY_FILE)
                            df_full.drop(idx).to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig"); st.rerun()
                else:
                    st.warning("내역이 없습니다.")
    else: st.info("기록된 거래 데이터가 없습니다.")

# ==========================================
# 탭 3: 관리
# ==========================================
with tab3:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🏢 거래처 정보 관리")
        mode = st.radio("작업", ["새로 등록", "기존 수정"], horizontal=True)
        t_n = st.selectbox("수정할 거래처", list(clients.keys())) if mode == "기존 수정" else ""
        curr = clients.get(t_n, {"등록번호":"", "대표자":"", "주소":"", "TEL":""})
        with st.form("client_form"):
            n = st.text_input("상호", value=t_n if mode == "기존 수정" else "")
            r = st.text_input("사업자번호", value=curr.get("등록번호",""))
            p = st.text_input("대표자", value=curr.get("대표자",""))
            a = st.text_input("주소", value=curr.get("주소",""))
            if st.form_submit_button("저장"):
                if n:
                    pr = clients.get(t_n, {}).get("prices", {}) if mode == "기존 수정" else {}
                    clients[n] = {"등록번호": r, "대표자": p, "주소": a, "prices": pr}
                    if mode == "기존 수정" and t_n != n: del clients[t_n]
                    save_clients(clients); st.rerun()

    with col_r:
        st.subheader("☕ 원두 단가 관리")
        bt = st.selectbox("거래처 선택", ["선택"] + list(clients.keys()))
        if bt != "선택":
            if "en_edit" not in st.session_state: st.session_state.en_edit = ""; st.session_state.ep_edit = 0; st.session_state.on_edit = ""
            en = st.text_input("원두명", value=st.session_state.en_edit)
            ep = st.number_input("단가", min_value=0, step=500, value=st.session_state.ep_edit)
            if st.button("💾 저장/수정"):
                if en:
                    if st.session_state.on_edit and st.session_state.on_edit != en: del clients[bt]["prices"][st.session_state.on_edit]
                    clients[bt]["prices"][en] = int(ep); save_clients(clients)
                    st.session_state.en_edit = ""; st.session_state.ep_edit = 0; st.session_state.on_edit = ""; st.rerun()
            for item, price in clients[bt]["prices"].items():
                bc = st.columns([4, 2, 1, 1])
                bc[0].write(item); bc[1].write(f"{price:,}원")
                if bc[2].button("✏️", key=f"e_{bt}_{item}"):
                    st.session_state.en_edit = item; st.session_state.ep_edit = price; st.session_state.on_edit = item; st.rerun()
                if bc[3].button("🗑️", key=f"d_{bt}_{item}"): del clients[bt]["prices"][item]; save_clients(clients); st.rerun()
