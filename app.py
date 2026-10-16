"""栄養士(AI献立ルール設計)採用 WEBテスト — Zoom面接中に候補者が入力する。
候補者: 通常URL / 面接官: ?admin=1 + パスワード(secrets の ADMIN_PW か 環境変数 INTERVIEW_ADMIN_PW)
"""
import json, os, time
from datetime import datetime
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="栄養士 WEBテスト | 富喜屋", page_icon="🍙", layout="centered")
DATA = Path(__file__).parent / "responses"
DATA.mkdir(exist_ok=True)

SECTIONS = [
    {
        "key": "q1", "title": "① 栄養価の調整",
        "intro": "ある日の昼食+おやつ(3〜5歳児)の栄養計算結果です。",
        "table": {
            "項目": ["エネルギー", "食塩相当量", "カルシウム", "鉄"],
            "目標": ["585kcal", "1.57g以下", "300mg", "2.5mg"],
            "この日の献立": ["520kcal", "2.3g", "210mg", "2.6mg"],
        },
        "menu": "ごはん / 鶏肉の照り焼き / ひじきの煮物 / 具だくさんみそ汁 / 牛乳 / おやつ:おにぎり",
        "qs": [
            ("q1_0", "この献立の栄養価について、目標値を基準に評価してください。(足りている点・多すぎる点・不足している点)", 160),
            ("q1_a", "どの料理の、どの部分を、どう直しますか? 食塩・エネルギー・カルシウムそれぞれについて、具体的に書いてください。", 220),
            ("q1_b", "直すときに、現場(調理・味・子どもの食べやすさ)の面で気をつけることは?", 120),
        ],
    },
    {
        "key": "q2", "title": "② 献立チェック",
        "intro": "ある施設(1〜5歳児クラスあり)の1週間の昼食です。次の施設ルールに違反している点を探してください。",
        "rules": [
            "魚は週1回、月曜日のみ",
            "洋風・中華の主菜を2日続けて出さない",
            "休み明け(月曜)は、生の果物・生のきのこ・もやしを使わない",
            "卵は使わない(マヨネーズを除く)",
            "主菜・副菜の主な食材を、前日と重ねない",
        ],
        "table": {
            "日": ["月(休み明け)", "火", "水", "木", "金"],
            "主菜": ["さばの塩焼き", "チキンのトマト煮(洋)", "豚肉の中華炒め(中)", "卵とじ丼の具", "鮭のムニエル"],
            "副菜": ["もやしとにんじんのナムル", "ブロッコリーのサラダ", "ミニトマトとぶどうの盛り合わせ(丸ごと)", "キャベツとにんじんの甘酢和え", "ほうれん草のおひたし"],
            "汁・果物": ["わかめのみそ汁 / 生りんご", "コンソメスープ", "春雨スープ", "豆腐のみそ汁", "けんちん汁 / みかん"],
        },
        "qs": [
            ("q2_a", "ルール違反を、見つけた順にすべて書いてください(日付・料理名・理由)。", 260),
            ("q2_b", "ルールには書かれていないが、保育園の給食として気になる点があれば、理由とあわせて書いてください。", 160),
        ],
    },
    {
        "key": "q3", "title": "③ ルールの言語化",
        "intro": "この仕事は、栄養士の「判断」を言葉にして、AIに教えることです。",
        "qs": [
            ("q3_a", "「魚を使ってよいのは月曜日だけ」という施設ルールを、AIに正しく伝わる指示文にしてください。理由、例外が起こりうる場面(祝日など)、迷ったときの扱いも含めて。", 260),
            ("q3_b", "あなたが献立を作るとき、いつも守っているルール(判断基準)を1つ、AIへの指示文として書いてください。\n\n【指示文の例】「揚げ物は、1週間に2回までにしてください。理由は、油の摂りすぎを防ぎ、調理室のコンロ・フライヤーの負担も減らすためです。ただし、行事の日は例外とします。迷ったときは、揚げ物を焼き物か蒸し物に置きかえてください。」", 260),
            ("q3_c", "AIが作った献立を見て「彩りが悪い」と感じました。AIが次回から直せるように、何と伝えますか?", 200),
        ],
    },
    {
        "key": "q4", "title": "④ 現場調理・衛生",
        "intro": "現場経験についての質問です。",
        "qs": [
            ("q4_a", "大量調理の加熱で、中心温度と時間をどう管理していますか? 具体的な数値を知っていれば書いてください。", 120),
            ("q4_b", "アレルギー対応食で、調理・配膳時の事故を防ぐために行っていることは?", 160),
            ("q4_c", "「献立としては良いが、現場の負担が大きい」と感じる料理(献立)の例を1つ、理由とあわせて教えてください。", 160),
        ],
    },
    {
        "key": "q5", "title": "⑤ AIについて",
        "intro": "正解はありません。普段のことをそのまま書いてください。",
        "qs": [
            ("q5_a", "ChatGPTなどの生成AIを使った経験を教えてください(なければ「なし」でOKです)。", 100),
            ("q5_b", "AIが出した献立に、栄養士として明らかな間違いがあったら、どう対応しますか?", 140),
        ],
    },
]


def admin_view():
    try:
        pw = st.secrets["ADMIN_PW"]
    except Exception:
        pw = os.environ.get("INTERVIEW_ADMIN_PW", "")
    st.title("面接官用:回答一覧")
    if not pw:
        st.error("パスワードが未設定です(secrets の ADMIN_PW)。")
        return
    if st.text_input("パスワード", type="password") != pw:
        return
    files = sorted(DATA.glob("*.json"), reverse=True)
    if not files:
        st.info("回答はまだありません。")
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        with st.expander(f"{d['name']}  ({d['submitted_at']})"):
            for s in SECTIONS:
                sec = d["sections"].get(s["key"], {})
                st.markdown(f"**{s['title']}**  — 所要 {sec.get('seconds', '?')}秒")
                for k, label, _ in [(q[0], q[1], q[2]) for q in s["qs"]]:
                    a = d["answers"].get(k, "")
                    st.caption(label)
                    st.text(f"{a}\n(文字数 {len(a)})")
            md = "\n".join(
                [f"# {d['name']} {d['submitted_at']}"]
                + [f"\n## {q[1]}\n{d['answers'].get(q[0], '')}" for s in SECTIONS for q in s["qs"]]
            )
            st.download_button("テキストでダウンロード", md, file_name=f"{f.stem}.md", key=f.stem)


def candidate_view():
    ss = st.session_state
    ss.setdefault("step", -1)
    ss.setdefault("answers", {})
    ss.setdefault("secs", {})
    ss.setdefault("t0", None)

    st.title("栄養士 WEBテスト")
    st.caption("株式会社富喜屋|面接官と画面を共有しながら、ご自身で入力してください。")

    if ss.step == -1:
        st.write("全5パートです(30分前後)。上手な文章でなくて大丈夫です。**考え方と理由**が知りたいので、思ったことをそのまま書いてください。")
        name = st.text_input("お名前")
        if st.button("開始する", type="primary", disabled=not name.strip()):
            ss.name = name.strip()
            ss.step = 0
            ss.t0 = time.time()
            st.rerun()
        return

    if ss.step >= len(SECTIONS):
        st.success("お疲れさまでした。以上で終了です。面接官にお知らせください。")
        return

    sec = SECTIONS[ss.step]
    st.progress(ss.step / len(SECTIONS), text=f"{ss.step + 1} / {len(SECTIONS)}")
    st.header(sec["title"])
    st.write(sec["intro"])
    if "rules" in sec:
        st.markdown("**施設ルール**\n" + "\n".join(f"{i}. {r}" for i, r in enumerate(sec["rules"], 1)))
    if "menu" in sec:
        st.markdown(f"**献立**:{sec['menu']}")
    if "table" in sec:
        st.table(sec["table"])
    for key, label, height in sec["qs"]:
        ss.answers[key] = st.text_area(label, value=ss.answers.get(key, ""), height=height, key=f"ta_{key}")

    last = ss.step == len(SECTIONS) - 1
    if st.button("提出する" if last else "次へ", type="primary"):
        ss.secs[sec["key"]] = ss.secs.get(sec["key"], 0) + int(time.time() - ss.t0)
        ss.t0 = time.time()
        ss.step += 1
        if last:
            now = datetime.now()
            rec = {
                "name": ss.name,
                "submitted_at": now.strftime("%Y-%m-%d %H:%M"),
                "answers": ss.answers,
                "sections": {k: {"seconds": v} for k, v in ss.secs.items()},
            }
            fn = DATA / f"{now:%Y%m%d_%H%M%S}_{ss.name}.json"
            fn.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        st.rerun()


if st.query_params.get("admin") == "1":
    admin_view()
else:
    candidate_view()
