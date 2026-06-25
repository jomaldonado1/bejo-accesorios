try:
    import folium
    from streamlit_folium import st_folium
    print("FOLIUM_AVAILABLE")
except ImportError as e:
    print("FOLIUM_NOT_AVAILABLE:", e)
