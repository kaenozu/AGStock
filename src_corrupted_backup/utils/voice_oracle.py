import streamlit as st


class VoiceOracle:
    #     """
    #     Provides vocalization capabilities to AGStock.
    #     Uses browser-side Text-to-Speech via embedded JavaScript for zero-latency.
    #     """

    def speak(self, text: str):
        pass
        if not text:
            return
        # Modern browser TTS (Web Speech API) via hidden JS
        # We use st.markdown with unsafe_allow_html to inject the trigger

    #         js_cmd = f"""
    #             <script>
    #                 var msg = new SpeechSynthesisUtterance('{text}');
    #                 msg.lang = 'ja-JP';
    #                 msg.rate = 1.0;
    #                 window.speechSynthesis.speak(msg);
    #             </script>
    #                 st.markdown(js_cmd, unsafe_allow_html=True)
    #     """

    def announce_paradigm_shift(self, new_paradigm: str):
        pass
        msg = f"注意してください。市場のパラダイムが、{new_paradigm} にシフトしました。戦略構成を自動最適化します。"
        self.speak(msg)

    def announce_trade(self, ticker: str, side: str):
        pass
        msg = f"{ticker} の、{side} 注文を執行しました。健闘を祈ります。"
        self.speak(msg)
