import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
from datetime import datetime
import os
import json

class JaydenProApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jayden Coffee Roasters - 프로 납품 관리")
        self.root.geometry("600x750")
        
        # 데이터 저장 파일 경로
        self.db_path = os.path.expanduser("~/Desktop/jayden_data.json")
        self.load_data()
        self.current_items = []

        # --- UI 설정 ---
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        # 1. 거래처 및 품목 관리 (저장 기능)
        tk.Label(main_frame, text="[ 1. 거래처 선택 ]", font=("Arial", 11, "bold")).pack(anchor="w")
        self.client_cb = ttk.Combobox(main_frame, values=self.data['clients'])
        self.client_cb.pack(fill="x", pady=5)
        
        # 2. 품목 선택 및 수량
        tk.Label(main_frame, text="[ 2. 품목 및 수량 입력 ]", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        item_frame = tk.Frame(main_frame)
        item_frame.pack(fill="x")
        
        self.item_cb = ttk.Combobox(item_frame, values=list(self.data['products'].keys()), width=20)
        self.item_cb.pack(side="left", padx=2)
        self.item_cb.bind("<<ComboboxSelected>>", self.auto_fill_price)

        self.price_ent = tk.Entry(item_frame, width=10) # 단가
        self.price_ent.pack(side="left", padx=2)
        
        self.qty_ent = tk.Entry(item_frame, width=5) # 수량
        self.qty_ent.pack(side="left", padx=2)

        # 3. 세금 설정 (포함/별도)
        self.tax_var = tk.StringVar(value="별도")
        tax_frame = tk.Frame(main_frame)
        tax_frame.pack(pady=10)
        tk.Radiobutton(tax_frame, text="VAT 별도", variable=self.tax_var, value="별도").pack(side="left")
        tk.Radiobutton(tax_frame, text="VAT 포함", variable=self.tax_var, value="포함").pack(side="left")

        # 버튼 영역
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="품목 추가", command=self.add_to_list, bg="#d1e7ff").pack(side="left", padx=5)
        tk.Button(btn_frame, text="새 거래처/품목 저장", command=self.save_new_info, bg="#fff3cd").pack(side="left", padx=5)

        # 4. 현재 입력 리스트
        self.tree = ttk.Treeview(main_frame, columns=("품목", "단가", "수량", "공급가", "세액"), show="headings", height=8)
        self.tree.heading("품목", text="품목명")
        self.tree.heading("단가", text="단가")
        self.tree.heading("수량", text="수량")
        self.tree.heading("공급가", text="공급가액")
        self.tree.heading("세액", text="세액")
        self.tree.column("품목", width=150)
        for col in ["단가", "수량", "공급가", "세액"]: self.tree.column(col, width=80)
        self.tree.pack(fill="both", pady=10)

        # 5. 하단 버튼
        tk.Button(main_frame, text="엑셀 거래명세서 발행", command=self.export_excel, 
                  height=2, bg="#4CAF50", fg="black", font=("Arial", 12, "bold")).pack(fill="x", pady=10)

    def load_data(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {"clients": [], "products": {}}

    def save_data(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def auto_fill_price(self, event):
        item = self.item_cb.get()
        if item in self.data['products']:
            self.price_ent.delete(0, tk.END)
            self.price_ent.insert(0, self.data['products'][item])

    def save_new_info(self):
        client = self.client_cb.get()
        item = self.item_cb.get()
        price = self.price_ent.get()
        
        if client and client not in self.data['clients']:
            self.data['clients'].append(client)
        if item and price:
            self.data['products'][item] = int(price)
        
        self.save_data()
        self.client_cb['values'] = self.data['clients']
        self.item_cb['values'] = list(self.data['products'].keys())
        messagebox.showinfo("저장 완료", "거래처 및 품목 정보가 저장되었습니다.")

    def add_to_list(self):
        try:
            name = self.item_cb.get()
            unit_price = int(self.price_ent.get())
            qty = int(self.qty_ent.get())
            
            if self.tax_var.get() == "별도":
                supply_value = unit_price * qty
                tax = int(supply_value * 0.1)
            else: # 포함일 경우 (역산)
                total = unit_price * qty
                supply_value = int(total / 1.1)
                tax = total - supply_value

            self.current_items.append([name, unit_price, qty
