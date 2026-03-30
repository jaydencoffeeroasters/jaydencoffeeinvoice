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
