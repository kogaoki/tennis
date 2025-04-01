import streamlit as st
import pandas as pd
import itertools
import math
from io import BytesIO
import xlsxwriter

st.title("大会運営システム プロトタイプ")
st.write("このアプリでは、参加ペア数を入力すると、各リーグのペア数に基づいて自動的にリーグ数を決定し、各リーグの対戦カードを生成します。")

# サイドバーで設定
st.sidebar.header("大会設定")
total_pairs = st.sidebar.number_input("参加ペア数", min_value=1, value=12, step=1)
pairs_per_league = st.sidebar.number_input("各リーグのペア数", min_value=2, value=4, step=1)

# リーグ数を自動計算（端数は最後のリーグに入れる）
num_leagues = math.ceil(total_pairs / pairs_per_league)
st.sidebar.write(f"自動決定されたリーグ数: {num_leagues}")

# リーグ名はアルファベット順（例：A, B, C, …）
league_names = [chr(ord('A') + i) for i in range(num_leagues)]

st.write("### 各リーグの対戦表")
st.write("※各リーグは、リーグ内の全ペア同士の対戦（総当たり戦）を自動生成します。")

# 各リーグごとに対戦カードを生成し表示＆ダウンロードボタンを作成
for league in league_names:
    st.write(f"#### リーグ {league}")
    # 最後のリーグの場合、余りが出るかもしれません
    if league != league_names[-1]:
        num_pairs_in_league = pairs_per_league
    else:
        remainder = total_pairs % pairs_per_league
        num_pairs_in_league = pairs_per_league if remainder == 0 else remainder

    # 例: Aリーグなら "A1", "A2", ..., "A{num_pairs_in_league}" とラベル付け
    pair_labels = [f"{league}{i+1}" for i in range(num_pairs_in_league)]
    # 全組み合わせを生成
    matches = list(itertools.combinations(pair_labels, 2))
    df_league = pd.DataFrame(matches, columns=["ペア1", "ペア2"])
    
    st.dataframe(df_league)
    
    # Excelファイルとしてダウンロードできるようにする
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df_league.to_excel(writer, sheet_name=f"League_{league}", index=False)
    writer.close()
    output.seek(0)
    
    st.download_button(
        label=f"{league}リーグ対戦表をExcelでダウンロード",
        data=output,
        file_name=f"League_{league}_match_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
