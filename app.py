import streamlit as st
import pandas as pd
import itertools
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, Font

st.set_page_config(layout="wide")
st.title("大会運営システム：リーグ対戦表＆スコアシート生成")

st.sidebar.header("設定")
total_pairs = st.sidebar.number_input("総ペア数", min_value=2, max_value=100, value=13, step=1)
num_leagues = st.sidebar.number_input("リーグ数", min_value=1, max_value=26, value=4, step=1)

# 左カラムにペア情報入力
left, right = st.columns([1, 2])
with left:
    st.write("### ペア情報入力（所属＋名前）")
    pair_info = []
    for i in range(total_pairs):
        team = st.text_input(f"所属 {i+1}", key=f"team_{i}")
        name1 = st.text_input(f"選手1の名前 {i+1}", key=f"name1_{i}")
        name2 = st.text_input(f"選手2の名前 {i+1}", key=f"name2_{i}")
        label = f"{team}：{name1}・{name2}" if team or name1 or name2 else f"ペア{i+1}"
        pair_info.append(label)

# ペアをリーグに割り当てる関数
def assign_pairs_to_leagues(pairs, num_leagues):
    base = len(pairs) // num_leagues
    remainder = len(pairs) % num_leagues

    leagues = []
    index = 0
    for i in range(num_leagues):
        league_size = base + (1 if i < remainder else 0)
        leagues.append(pairs[index:index+league_size])
        index += league_size

    return leagues

with right:
    st.write("### リーグ対戦表の生成")
    league_assignments = assign_pairs_to_leagues(pair_info, num_leagues)
    league_matchup_dfs = {}

    # 各リーグの対戦表を表示
    for i, pair_labels in enumerate(league_assignments):
        league_name = chr(ord('A') + i)
        combos = list(itertools.combinations(pair_labels, 2))
        df = pd.DataFrame(combos, columns=["ペア1", "ペア2"])
        league_matchup_dfs[league_name] = df

        st.subheader(f"リーグ {league_name}（{len(df)+1}ペア）")
        st.dataframe(df)

    # リーグ順位の入力
    st.write("### リーグ順位の入力")
    pair_rankings = {}

    for i, league in enumerate(league_assignments):
        league_name = chr(ord('A') + i)
        st.subheader(f"{league_name}リーグ 順位入力")
        rankings = {}
        for pair in league:
            rank = st.selectbox(f"{pair} の順位", options=list(range(1, len(league)+1)), key=f"{pair}_rank")
            rankings[pair] = rank
        pair_rankings[league_name] = rankings

    # トーナメント出場形式の選択
    st.write("### トーナメント出場形式の選択")
    tournament_mode = st.radio("トーナメント出場形式を選択", ["各リーグ1位", "各リーグ1・2位", "手動選択"])

    selected_pairs = []

    if tournament_mode == "各リーグ1位":
        for league_name, rankings in pair_rankings.items():
            top_pair = min(rankings, key=rankings.get)
            selected_pairs.append(f"{top_pair}（{league_name}1位）")
    elif tournament_mode == "各リーグ1・2位":
        for league_name, rankings in pair_rankings.items():
            sorted_pairs = sorted(rankings.items(), key=lambda x: x[1])
            selected_pairs.extend([f"{sorted_pairs[0][0]}（{league_name}1位）", f"{sorted_pairs[1][0]}（{league_name}2位）"])
    elif tournament_mode == "手動選択":
        st.write("### トーナメント出場ペアを選択（手動）")
        all_pairs = [pair for league in league_assignments for pair in league]
        selected_pairs = st.multiselect("出場ペアを選んでください", all_pairs)

    st.write("### トーナメント出場ペア一覧")
    for p in selected_pairs:
        st.markdown(f"- {p}")

    # 書式設定
    center = Alignment(horizontal="center", vertical="center")
    border = Border(left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
    bold = Font(bold=True)

    # リーグ対戦表Excel出力
    st.write("### リーグ対戦表のExcel出力（書式付き）")
    if st.button("リーグ対戦表をExcel出力"):
        wb = Workbook()
        ws = wb.active
        ws.title = "全リーグまとめ"

        current_row = 1
        for i, league in enumerate(league_assignments):
            league_name = chr(ord('A') + i)

            # 見出し行
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
            cell = ws.cell(row=current_row, column=1, value=f"{league_name}リーグ")
            cell.alignment = center
            cell.font = Font(bold=True, size=14)
            current_row += 1

            # ヘッダー
            headers = ["No", "ペア名", "チーム名"] + [str(j+1) for j in range(len(league))] + ["順位"]
            for col, header in enumerate(headers, start=1):
                c = ws.cell(row=current_row, column=col, value=header)
                c.alignment = center
                c.font = bold
                c.border = border
            current_row += 1

            # データ行
            for idx, pair in enumerate(league, start=1):
                name_team = pair.split("：") if "：" in pair else [pair, ""]
                row = [idx, name_team[1] if len(name_team) > 1 else "", name_team[0]]
                for j in range(1, len(league)+1):
                    row.append("×" if idx == j else "")
                row.append("")  # 順位欄

                for col, val in enumerate(row, start=1):
                    cell = ws.cell(row=current_row, column=col, value=val)
                    cell.alignment = center
                    cell.border = border
                current_row += 1

            # スペース空け
            current_row += 1

        # 列幅調整
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 18

        # 出力
        excel_data = BytesIO()
        wb.save(excel_data)
        st.download_button(label="リーグ対戦表（書式付き）をダウンロード",
                           data=excel_data.getvalue(),
                           file_name="league_tables.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
