import streamlit as st
import json
import matplotlib.pyplot as plt
import socket #polaczenie z ESP32
import threading
from matplotlib.patches import Rectangle


st.set_page_config("ESP32 - Localization Center")

st.sidebar.header("Pozycje Beaconów [m]")
st.sidebar.subheader("Beacon 1")
b1_x = st.sidebar.number_input("BEACON_1 (X)", value=0.0, step = 0.1)
b1_y = st.sidebar.number_input("BEACON_1 (Y)", value=0.0, step = 0.1)
st.sidebar.subheader("Beacon 2")
b2_x = st.sidebar.number_input("BEACON_2 (X)", value=0.0, step = 0.1)
b2_y = st.sidebar.number_input("BEACON_2 (Y)", value=0.0, step = 0.1)
st.sidebar.subheader("Beacon 3")
b3_x = st.sidebar.number_input("BEACON_3 (X)", value=0.0, step = 0.1)
b3_y = st.sidebar.number_input("BEACON_3 (Y)", value=0.0, step = 0.1)
st.sidebar.subheader("Wymiary pokoju")
room_x = st.sidebar.number_input("Szerokość pokoju [m]", value = 0.0, step = 0.1)
room_y = st.sidebar.number_input("Długość pokoju [m]", value = 0.0, step = 0.1)


beacons = {
    "BEACON_1": (b1_x,b1_y),
    "BEACON_2": (b2_x,b2_y),
    "BEACON_3": (b3_x,b3_y),
}


if "data_log" not in st.session_state:
    st.session_state.data_log = []

def udp_listener():
    #config UDP
    UDP_IP = "0.0.0.0"
    UDP_PORT = 5005
    socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket1.bind((UDP_IP, UDP_PORT))

    while True:
        data, addr = socket1.recvfrom(1024)
        msg = data.decode("utf-8")  #dekodowanie z utf na str
        st.session_state.data_log.append(msg)

#uruchomienie UDP
if "udp_thread" not in st.session_state:
    thread = threading.Thread(target=udp_listener, daemon=True)
    thread.start()
    st.session_state.udp_thread = True

#podzial na karty
tab_map, tab_login = st.tabs(["Mapa Lokalizacji - heatmapa", "Logowanie"])

with tab_login:
    st.header("Połączenie ESP32 z siecią")
    st.info('Najpierw połącz się z siecią "ESP32_AP" (hasło:123454321)')

    with st.form('wifi_form'):
        ssid = st.text_input("SSID Twojej sieci")
        password = st.text_input("Hasło", type="password")
        submit_wifi = st.form_submit_button("Połącz z siecią")

#interpretacja/odebranie rssi
def get_latest_rssi():
    if not st.session_state.data_log:
        return{}
    #otrzymujemy wiadomość postaci "NAZWA:RSSI; ..."
    last_msg = st.session_state.data_log[-1]
    try:
        data = {} #slownik przechowujacy klucz (nazwe) i wartosc (RSSI)
        for item in last_msg.strip(';').split(';'):
            if ':' in item:
                name, rssi = item.split(':')
                data[name] = int(rssi)

        return data
    except:
        return {}


with tab_map:
    #wyswietlanie wartosci zmierzonych RSSI
    current_data = get_latest_rssi()
    cols = st.columns(3)
    for i,name in enumerate(["BEACON_1", "BEACON_2", "BEACON_3"]):
        val = current_data.get(name, "N/A")
        cols[i].metric(label=name, value=f"{val} dBm")


    st.header("Wizualizacja mapy pomiarów")

    fig,ax = plt.subplots()
    for name,pos in beacons.items():
        ax.scatter(pos[0], pos[1], s=100, label=name)
    ax.add_patch(Rectangle((0,0),room_x,room_y, fill=False))
        #ax.text(pos[0] + 0.1, pos[1] + 0.1, name)

    ax.set_xlabel("Szerokość (X) [m]")
    ax.set_ylabel("Długość (Y) [m]")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()

    st.pyplot(fig)

    st.header("Parametry sygnału")
    A = st.slider("Moc z 1 metra (A) [dBm]", -80, -30, -55)
    n = st.slider("Współczynnik tłumienia (n)", 1.0, 5.0, 2.0)
