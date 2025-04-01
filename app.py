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
court_count = st.sidebar.number_input("使用コート数（進行表用）", min_value=1, max_value=10, value=2, step=1)

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
    with st.container():
        try:
            edited = st.data_editor(
                df,
                column_config={"ペア番号": st.column_config.TextColumn(disabled=True)},
                use_container_width=True
            )
            league_pair_data[league_name] = edited
        except Exception as e:
            st.error(f"{league_name}リーグの入力中にエラーが発生しました: {e}")
            continue

# 対戦表作成・表示
st.write("### リーグ対戦表の生成")
league_matchup_dfs = {}
league_tables_raw = {}

for league_name, df in league_pair_data.items():
    if df.empty:
        continue

    try:
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
            while len(row) < len(headers):
                row.append("")
            table_data.append(row)

        df_table = pd.DataFrame(table_data, columns=headers)

        st.dataframe(df_table, use_container_width=True)
        league_tables_raw[league_name] = df_table

        combos = list(itertools.combinations(pair_labels, 2))
        df_matches = pd.DataFrame(combos, columns=["ペア1", "ペア2"])
        league_matchup_dfs[league_name] = df_matches

    except Exception as e:
        st.error(f"{league_name}リーグの対戦表生成中にエラーが発生しました: {e}")
        continue

# トーナメント条件分岐の追加
st.write("### 決勝方式の選択")
final_mode = st.radio("決勝の形式を選択", ["トーナメント", "リーグ戦"])
rank_limit = st.number_input("各リーグから何位まで出場するか", min_value=1, max_value=5, value=1, step=1)

# トーナメント構成の生成
qualified_pairs = []
for league_name, df in league_pair_data.items():
    for i in range(min(rank_limit, len(df))):
        pair_label = df["ペア番号"].iloc[i]
        qualified_pairs.append(f"{pair_label}（{league_name}{i+1}位）")

st.write("### 決勝進出ペア一覧")
for p in qualified_pairs:
    st.markdown(f"- {p}")

# 仮のトーナメント表またはリーグ戦表示（シンプルなテキスト）
if final_mode == "トーナメント":
    st.write("### トーナメント表（仮）")
    st.markdown("組み合わせは自動生成予定。準決勝、決勝など表示可能。")
    for i in range(0, len(qualified_pairs), 2):
        if i+1 < len(qualified_pairs):
            st.write(f"{qualified_pairs[i]} vs {qualified_pairs[i+1]}")
        else:
            st.write(f"{qualified_pairs[i]}（シード）")
else:
    st.write("### 決勝リーグ戦（仮）")
    if len(qualified_pairs) >= 2:
        st.dataframe(pd.DataFrame(itertools.combinations(qualified_pairs, 2), columns=["ペア1", "ペア2"]))
    else:
        st.info("対戦ペアが2組以上必要です。")
