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

# ペア情報入力（スプレッドシート形式）
st.write("### ペア情報入力（所属・選手1・選手2）")
def generate_empty_pair_df(n):
    return pd.DataFrame({
        "所属": ["" for _ in range(n)],
        "選手1": ["" for _ in range(n)],
        "選手2": ["" for _ in range(n)]
    })

if "pair_df" not in st.session_state or len(st.session_state.pair_df) != total_pairs:
    st.session_state.pair_df = generate_empty_pair_df(total_pairs)

edited_df = st.data_editor(st.session_state.pair_df, num_rows="dynamic")
st.session_state.pair_df = edited_df.copy()

# ラベル生成（チーム：選手1・選手2）
pair_info = []
for _, row in edited_df.iterrows():
    team = row["所属"]
    name1 = row["選手1"]
    name2 = row["選手2"]
    label = f"{team}：{name1}・{name2}" if team or name1 or name2 else "未入力ペア"
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

st.write("### リーグ対戦表の生成")
league_assignments = assign_pairs_to_leagues(pair_info, num_leagues)
league_matchup_dfs = {}
league_tables_raw = {}  # 対戦表の元データ保持用

# 各リーグの対戦表を表示（見た目：Excel準拠）
for i, league in enumerate(league_assignments):
    league_name = chr(ord('A') + i)
    st.subheader(f"{league_name}リーグ 対戦表プレビュー")

    headers = ["No", "ペア名", "チーム名"] + [str(j+1) for j in range(len(league))] + ["順位"]
    table_data = []
    for idx, pair in enumerate(league, start=1):
        if isinstance(pair, str) and "：" in pair:
            team, players = pair.split("：", 1)
        else:
            team, players = pair, ""
        row = [idx, players, team]
        for j in range(1, len(league)+1):
            row.append("×" if idx == j else "")
        row.append("")  # 順位欄
        table_data.append(row)

    df_table = pd.DataFrame(table_data, columns=headers)
    st.dataframe(df_table, use_container_width=True)
    league_tables_raw[league_name] = df_table.copy()

    # 対戦組み合わせも従来通り保持
    combos = list(itertools.combinations(league, 2))
    df_matches = pd.DataFrame(combos, columns=["ペア1", "ペア2"])
    league_matchup_dfs[league_name] = df_matches

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
