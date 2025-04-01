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
pairs_per_league = st.sidebar.selectbox("1リーグに入れるペア数", options=[2, 3, 4, 5], index=2)

base_league_count = total_pairs // pairs_per_league
remainder = total_pairs % pairs_per_league

st.sidebar.markdown(f"**→ {base_league_count}リーグ + {remainder}ペア余り**")

# 余りが出る場合、どこに追加するか選ぶ
extra_league_targets = []
if remainder > 0:
    st.sidebar.write("### 余りの振り分け先")
    options = [f"{chr(ord('A') + i)}" for i in range(base_league_count)]
    extra_league_targets = st.sidebar.multiselect(
        "追加するリーグを選択（上から順がおすすめ）",
        options,
        default=options[:remainder],
        max_selections=remainder
    )
    if len(extra_league_targets) != remainder:
        st.stop()

# リーグ構成
league_assignments = []
pair_no = 1
for i in range(base_league_count):
    league_size = pairs_per_league + (1 if chr(ord('A') + i) in extra_league_targets else 0)
    league_name = chr(ord('A') + i)
    league_assignments.append([f"{league_name}{j+1}" for j in range(league_size)])

# 各リーグのペア入力欄
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
    if df.empty:
        continue

    st.subheader(f"{league_name}リーグ 対戦表プレビュー")
    pair_labels = df["ペア番号"].tolist()
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
