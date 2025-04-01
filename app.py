import pandas as pd
from itertools import combinations
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO

# ----------------------------
# ① 入力設定
# ----------------------------

# 例として、リーグ名 "A" で4ペアのリーグ戦を考える
league_name = "A"         # リーグ名
num_pairs = 4             # ペア数（4ペアなら、試合数は4C2 = 6試合）

# 各ペアのラベルを生成（例："A1", "A2", "A3", "A4"）
pairs = [f"{league_name}{i+1}" for i in range(num_pairs)]

# ----------------------------
# ② リーグ対戦カードの生成
# ----------------------------
# 全組み合わせ（昇順で）
match_list = []
for match_num, (p1, p2) in enumerate(combinations(pairs, 2), start=1):
    match_list.append({
        "試合番号": match_num,
        "対戦カード": f"{p1} vs {p2}"
    })

# リーグ対戦表（データフレーム）として出力
df_league_match = pd.DataFrame(match_list)
print("【リーグ対戦カード一覧】")
print(df_league_match)

# ----------------------------
# ③ スコアシートのExcel出力
# ----------------------------
# 各試合ごとにスコアシートのテンプレートを生成
# ※ここではシンプルなフォーマット例として作成

# Excelブック作成
wb = Workbook()
# デフォルトシートは削除
default_sheet = wb.active
wb.remove(default_sheet)

# 書式設定用スタイル
bold = Font(bold=True)
center = Alignment(horizontal="center", vertical="center")
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# 各試合ごとにシートを作成
for match in match_list:
    sheet_title = f"試合{match['試合番号']}"
    ws = wb.create_sheet(title=sheet_title)
    
    # ヘッダー部分
    ws.merge_cells("A1:F1")
    ws["A1"] = f"【リーグ {league_name}】 スコアシート"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = center
    
    # 試合番号
    ws["A3"] = "試合番号"
    ws["B3"] = match["試合番号"]
    ws["A3"].font = bold
    ws["B3"].alignment = center
    
    # 対戦カード
    ws["A4"] = "対戦カード"
    ws["B4"] = match["対戦カード"]
    ws["A4"].font = bold
    ws["B4"].alignment = center
    
    # 以下、スコア記入欄（シンプルな例）
    ws["A6"] = "勝者"
    ws["A7"] = "備考"
    ws["A6"].font = bold
    ws["A7"].font = bold
    
    # セルに枠線を引く（例としてA3～B7）
    for row in range(3, 8):
        for col in ['A','B']:
            ws[f"{col}{row}"].border = thin_border

# Excelファイルとして保存（またはBytesIO経由でダウンロード可能）
output_path = "ScoreSheets.xlsx"
wb.save(output_path)
print(f"スコアシートExcelファイルを保存しました: {output_path}")