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

# 何ペアリーグにするか手動設定
st.sidebar.write("### 各リーグのペア数（任意）")
manual_league_sizes = {}
manual_total = 0
league_labels = [chr(ord('A') + i) for i in range(num_leagues)]
for label in league_labels:
    size = st.sidebar.number_input(f"{label}リーグ", min_value=0, max_value=total_pairs, value=0, step=1, key=f"manual_{label}")
    manual_league_sizes[label] = size
    manual_total += size

if manual_total > 0 and manual_total != total_pairs:
    st.sidebar.warning(f"合計ペア数が {total_pairs} と一致していません（現在: {manual_total}）")

# ペアをリーグに割り当てる関数（手動優先 → 自動で振り分け）
def assign_pairs_to_leagues_flexible(total_count, num_leagues, manual_sizes):
    leagues = []
    index = 0
    labels = [chr(ord('A') + i) for i in range(num_leagues)]
    remaining = total_count

    for label in labels:
        size = manual_sizes.get(label, 0)
        if size > 0:
            leagues.append(size)
            remaining -= size
        else:
            leagues.append(0)

    if remaining > 0:
        for i in range(len(leagues)):
            if leagues[i] == 0:
                leagues[i] = remaining // (leagues.count(0))
        while sum(leagues) < total_count:
            for i in range(len(leagues)):
                if sum(leagues) < total_count:
                    leagues[i] += 1
    return leagues

# 実際のリーグ分け
league_sizes = assign_pairs_to_leagues_flexible(total_pairs, num_leagues, manual_league_sizes)
league_assignments = []
pair_counter = 0
for i, size in enumerate(league_sizes):
    league_name = chr(ord('A') + i)
    league_assignments.append([f"{league_name}{j+1}" for j in range(size)])
    pair_counter += size

# 各リーグごとの選手入力
st.write("### リーグごとの選手情報入力")
league_pair_data = {}

for i, league in enumerate(league_assignments):
    league_name = chr(ord('A') + i)
    st.subheader(f"{league_name}リーグ 選手入力")
    df = pd.DataFrame({
        "ペア番号": league,
        "所属": ["" for _ in league],
        "選手1": ["" for _ in league],
        "選手2": ["" for _ in league]
    })
    edited = st.data_editor(df, column_config={"ペア番号": st.column_config.TextColumn(disabled=True)}, use_container_width=True)
    league_pair_data[league_name] = edited

# 対戦表作成・表示
st.write("### リーグ対戦表の生成")
league_matchup_dfs = {}
league_tables_raw = {}

for league_name, df in league_pair_data.items():
    st.subheader(f"{league_name}リーグ 対戦表プレビュー")
    pair_labels = df["ペア番号"]
    pair_names = [f"{row['所属']}：{row['選手1']}・{row['選手2']}" for _, row in df.iterrows()]
    label_map = dict(zip(pair_labels, pair_names))

    headers = ["No", "ペア名", "チーム名"] + [str(j+1) for j in range(len(pair_labels))] + ["順位"]
    table_data = []
    for idx, label in enumerate(pair_labels):
        name = label_map.get(label, "")
        team, players = (name.split("：", 1) if "：" in name else ("", name))
        row = [idx + 1, players, team]
        for j in range(len(pair_labels)):
            row.append("×" if j == idx else "")
        row.append("")
        table_data.append(row)

    df_table = pd.DataFrame(table_data, columns=headers)
    st.dataframe(df_table, use_container_width=True)
    league_tables_raw[league_name] = df_table

    combos = list(itertools.combinations(pair_labels, 2))
    df_matches = pd.DataFrame(combos, columns=["ペア1", "ペア2"])
    league_matchup_dfs[league_name] = df_matches

# トーナメント出場形式の選択
st.write("### トーナメント出場形式の選択")
tournament_mode = st.radio("トーナメント出場形式を選択", ["各リーグ1位", "各リーグ1・2位", "手動選択"])

selected_pairs = []

if tournament_mode == "各リーグ1位":
    for league_name, df in league_pair_data.items():
        if not df.empty:
            selected_pairs.append(f"{df['ペア番号'].iloc[0]}（{league_name}1位）")
elif tournament_mode == "各リーグ1・2位":
    for league_name, df in league_pair_data.items():
        if len(df) >= 2:
            selected_pairs.extend([
                f"{df['ペア番号'].iloc[0]}（{league_name}1位）",
                f"{df['ペア番号'].iloc[1]}（{league_name}2位）"
            ])
elif tournament_mode == "手動選択":
    st.write("### トーナメント出場ペアを選択（手動）")
    all_pairs = [row["ペア番号"] for df in league_pair_data.values() for _, row in df.iterrows()]
    selected_pairs = st.multiselect("出場ペアを選んでください", all_pairs)

st.write("### トーナメント出場ペア一覧")
for p in selected_pairs:
    st.markdown(f"- {p}")
