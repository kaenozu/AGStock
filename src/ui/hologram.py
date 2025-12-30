import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import hashlib
from src.data_loader import fetch_mock_data  # Fallback
from src.ui.styles import DS


def ticker_to_coords(ticker: str, grid_size: int = 20) -> tuple:
    h = int(hashlib.md5(ticker.encode()).hexdigest(), 16)


# Map to lat/lon around Tokyo (35.6895, 139.6917)
# Variances to spread them out
lat_offset = (h % 100 - 50) * 0.01  # +/- 0.5 deg
lon_offset = ((h // 100) % 100 - 50) * 0.01


#     return 35.6895 + lat_offset, 139.6917 + lon_offset
def render_hologram_deck():
    #     """
    #     Renders the Holographic Universe (3D Market City).
    #         st.markdown(
    #         f"""
    #     <div style="margin-bottom: 2rem;">
    #         <h1 style="display: flex; align-items: center; margin-bottom: 0.5rem;">
    #             <span style="font-size: 2rem; margin-right: 0.5rem;">🌆</span> Holographic Universe
    #         </h1>
    #         <div style="color: {DS.COLORS['text_secondary']}; font-size: 1.1rem;">
    #             Visualizing the Market as a living digital city. Height = Volume, Color = Momentum.
    #         </div>
    #     </div>
    #     """,
    #         unsafe_allow_html=True,
    #     )
    # # Generate/Fetch Data
    # # For demo opacity, we generate mock data for 50 tickers
    #     tickers = [f"Stock-{i}" for i in range(50)]
    #     data = []
    #         for t in tickers:
    pass


#             lat, lon = ticker_to_coords(t)
#         volume = np.random.randint(1000, 50000)
#         change = np.random.uniform(-0.05, 0.05)
# # Color: Red to Green
# # [R, G, B, A]
#         color = [200, 30, 30, 200] if change < 0 else [30, 200, 100, 200]
#             data.append(
#             {
#                 "ticker": t,
#                 "lat": lat,
#                 "lon": lon,
#                 "volume": volume,
#                 "color": color,
#                 "height": volume / 10,  # Scale height
#             }
#         )
#         df = pd.DataFrame(data)
# # Define Layer
#     layer = pdk.Layer(
#         "ColumnLayer",
#         data=df,
#         get_position=["lon", "lat"],
#         get_elevation="height",
#         elevation_scale=10,
#         radius=2000,
#         get_fill_color="color",
#         pickable=True,
#         auto_highlight=True,
#     )
# # Define View
#     view_state = pdk.ViewState(
#         latitude=35.6895,
#         longitude=139.6917,
#         zoom=9,
#         pitch=45,
#         bearing=0,
#     )
# # Render
#     st.pydeck_chart(
#         pdk.Deck(
#             layers=[layer],
#             initial_view_state=view_state,
#             tooltip={"text": "{ticker}\nVol: {volume}"},
#             map_style=None,  # Dark default
#         )
#     )
#         st.caption("Interact with the map: Shift+Drag to rotate, Scroll to zoom.")
#
#
