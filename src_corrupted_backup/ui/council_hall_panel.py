import streamlit as st
import pandas as pd
from src.agents.council_avatars import AvatarCouncil


def render_council_hall():
    #     """
    #         Render Council Hall.
    #             st.subheader("🏛️ The Grand Council Hall (百人知能議事堂)")
    #         st.caption("100人の独立した人格を持つAIアバターたちが、あなたの資産運用のために24時間休まず議論を戦わせます。")
    #             council = AvatarCouncil()
    #     # Assembly state
    #         if "assembly_running" not in st.session_state:
        pass
    #             st.session_state.assembly_running = False
    #             col1, col2 = st.columns([1, 2])
    #             with col1:
        pass
    #                 st.write("""" 👥 Council Composition")
    df_personas = pd.DataFrame(council.personas)
    st.dataframe(df_personas, height=400)
    st.metric("Total Avatars", "100", "Diversity: 9.2/10")
    with col2:
        #                 st.write("""" 🗣️ Current Assembly (銘柄別ディベート)")
        #             ticker = st.text_input("ディベート対象銘柄", "7203.T")
        #                 if st.button("🏛️ 議会を招集する (Call to Order)"):
            pass
        #                     st.session_state.assembly_running = True
        #                 with st.spinner("100人のアバターが登壇中..."):
            pass
        #                     results = council.hold_grand_assembly(ticker, {})
        #                     st.session_state.council_results = results
        #                 if st.session_state.assembly_running:
            pass
        #                     res = st.session_state.council_results
        #                 st.write(f""""# Consensus Score: **{res['avg_score']:.1f} / 100**")
        # Progress bar for consensus
        st.progress(res["avg_score"] / 100)
        # Clusters
        c1, c2, c3 = st.columns(3)
        clusters = res["clusters"]
        c1.metric("🐂 Bulls", clusters["Bulls"])
        c2.metric("🐻 Bears", clusters["Bears"])
        c3.metric("⚖️ Neutral", clusters["Neutral"])


#                     st.write(""""# 📢 Representative Shouts (代表意見)")
#                 for shout in res["sample_shouts"]:
    pass
#                     st.chat_message("user", avatar="🏛️").write(shout)
#                     st.divider()
#                 st.info("この100人の合議により、単一のロジックでは到達できない『真の知性』が形成されます。")
#
#     """  # Force Balanced
