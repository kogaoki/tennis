import streamlit as st
import pandas as pd
import itertools

st.title("大会運営システム：リーグ対戦表＆スコアシート生成")

st.sidebar.header("設定")
total_pairs = st.sidebar.number_input("総ペア数", min_value=2, max_value=100, value=13, step=1)
num_leagues = st.sidebar.number_input("リーグ数", min_value=1, max_value=26, value=4, step=1)

# ペア情報入力
st.write("### ペア情報入力（所属＋名前）")
pair_info = []
for i in range(total_pairs):
    with st.expander(f"ペア{i+1}"):
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

st.write("### リーグ対戦表の生成")
league_assignments = assign_pairs_to_leagues(pair_info, num_leagues)
league_matchup_dfs = {}

# 各リーグごとに対戦カード（全組み合わせ）を生成
for i, pair_labels in enumerate(league_assignments):
    league_name = chr(ord('A') + i)
    combos = list(itertools.combinations(pair_labels, 2))
    df = pd.DataFrame(combos, columns=["ペア1", "ペア2"])
    league_matchup_dfs[league_name] = df

# 各リーグの対戦表を表示
for league_name, df in league_matchup_dfs.items():
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

# トーナメント出場ペア一覧表示
st.write("### トーナメント出場ペア一覧")
for p in selected_pairs:
    st.markdown(f"- {p}")

st.write("### スコアシート出力")
st.write("各対戦ごとの簡易スコアシート（Excel形式）を生成できます。")

if st.button("スコアシートExcelを生成"):
    from io import BytesIO
    import xlsxwriter

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # 各リーグごと、各対戦ごとにシートを作成
    for league_name, df in league_matchup_dfs.items():
        for idx, row in df.iterrows():
            sheet_name = f"{league_name}_{idx+1}"
            # シンプルなスコアシートテンプレート
            data = {
                "項目": ["試合番号", "ペア1", "ペア2", "勝者", "備考"],
                "内容": [f"{league_name}_{idx+1}", row["ペア1"], row["ペア2"], "", ""]
            }
            sheet_df = pd.DataFrame(data)
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    writer.save()
    processed_data = output.getvalue()
    st.download_button(label="スコアシートExcelをダウンロード", 
                       data=processed_data, 
                       file_name="score_sheets.xlsx", 
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
