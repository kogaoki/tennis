import streamlit as st
import pandas as pd
import itertools
import requests
from io import BytesIO
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Side, Font
import fitz

st.set_page_config(layout="wide")
st.title("大会運営システム：リーグ対戦表＆スコアシート生成")

st.sidebar.header("設定")
total_pairs = st.sidebar.number_input("総ペア数", min_value=2, max_value=100, value=13, step=1)
pairs_per_league = st.sidebar.selectbox("1リーグに入れるペア数", options=[2, 3, 4, 5], index=2)
court_count = st.sidebar.number_input("使用コート数（進行表用）", min_value=1, max_value=10, value=2, step=1)

base_league_count = total_pairs // pairs_per_league
remainder = total_pairs % pairs_per_league

st.sidebar.markdown(f"**→ {base_league_count}リーグ + {remainder}ペア余り**")

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

league_assignments = []
for i in range(base_league_count):
    league_size = pairs_per_league + (1 if chr(ord('A') + i) in extra_league_targets else 0)
    league_name = chr(ord('A') + i)
    league_assignments.append([f"{league_name}{j+1}" for j in range(league_size)])

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

st.write("### リーグ対戦表の生成")
league_matchup_dfs = {}
league_tables_raw = {}
match_schedule = []

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

        for match in combos:
            match_schedule.append({"リーグ": league_name, "ペア1": match[0], "ペア2": match[1]})

    except Exception as e:
        st.error(f"{league_name}リーグの対戦表生成中にエラーが発生しました: {e}")
        continue

st.session_state["match_schedule"] = match_schedule
st.session_state["league_pair_data"] = league_pair_data

if st.button("スコアシートPDFを出力"):
    try:
        github_url = "https://raw.githubusercontent.com/kogaoki/tennis/main/scoresheet.pdf"
        response = requests.get(github_url)
        pdf_template = fitz.open(stream=response.content, filetype="pdf")
        output_pdf = fitz.open()

        coords = {
            "no1": (92, 181), "team1": (213, 181), "p1_1": (187, 214), "p1_2": (187, 250),
            "no2": (361, 180), "team2": (477, 180), "p2_1": (453, 214), "p2_2": (452, 250)
        }

        def get_info(code):
            for league_df in st.session_state["league_pair_data"].values():
                row = league_df[league_df["ペア番号"] == code]
                if not row.empty:
                    team = row.iloc[0]["所属"]
                    p1 = row.iloc[0]["選手1"]
                    p2 = row.iloc[0]["選手2"]
                    return team, p1, p2
            return "", "", ""

        for idx, match in enumerate(st.session_state["match_schedule"]):
            output_pdf.insert_pdf(pdf_template, from_page=0, to_page=0)
            page = output_pdf[-1]

            team1, p1_1, p1_2 = get_info(match["ペア1"])
            team2, p2_1, p2_2 = get_info(match["ペア2"])

            page.insert_text(coords["no1"], match["ペア1"], fontsize=12)
            page.insert_text(coords["team1"], team1, fontsize=12)
            page.insert_text(coords["p1_1"], p1_1, fontsize=12)
            if p1_2:
                page.insert_text(coords["p1_2"], p1_2, fontsize=12)

            page.insert_text(coords["no2"], match["ペア2"], fontsize=12)
            page.insert_text(coords["team2"], team2, fontsize=12)
            page.insert_text(coords["p2_1"], p2_1, fontsize=12)
            if p2_2:
                page.insert_text(coords["p2_2"], p2_2, fontsize=12)

        pdf_bytes = output_pdf.write()
        st.download_button("PDFスコアシートをダウンロード", pdf_bytes, file_name="score_sheets.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"PDF出力中にエラーが発生しました: {e}")
