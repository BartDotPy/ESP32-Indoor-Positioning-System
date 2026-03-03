import streamlit as st
import json
import matplotlib.pyplot as plt
import socket #polaczenie z ESP32
import threading
from matplotlib.patches import Rectangle
#naprawa błędu
import queue
import requests

#import obliczeń
from calculations import rssi_to_distance, trilaterate
import time

st.set_page_config("ESP32 - Localization Center")

#jednorazowa konfiguracja portów 
@st.cache_resource
def start_udp_engine():
    msg_queue = queue.Queue()

    def udp_listener(q):
        UDP_IP = "0.0.0.0"
        UDP_PORT = 5005
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #sprawdzanie i konfiguracja
        try:
            sock.bind((UDP_IP, UDP_PORT))
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode("utf-8")
                print(f"ODEBRANO: {msg}")
                q.put(msg)
            except:
                continue

    thread = threading.Thread(target=udp_listener, args=(msg_queue,), daemon=True)
    thread.start()
    return msg_queue

#pobieranie kolejki
shared_queue = start_udp_engine()


if "data_log" not in st.session_state:
    st.session_state.data_log = []


while not shared_queue.empty():
    st.session_state.data_log.append(shared_queue.get())



#inicjalizacja beaconów i przypisanie podstawowych pozycji
st.sidebar.header("Pozycje Beaconów [m]")
st.sidebar.subheader("Beacon 1")
b1_x = st.sidebar.number_input("BEACON_1 (X)", value=0.0, step = 0.1)
b1_y = st.sidebar.number_input("BEACON_1 (Y)", value=0.0, step = 0.1)
st.sidebar.subheader("Beacon 2")
b2_x = st.sidebar.number_input("BEACON_2 (X)", value=2.0, step = 0.1)
b2_y = st.sidebar.number_input("BEACON_2 (Y)", value=2.0, step = 0.1)
st.sidebar.subheader("Beacon 3")
b3_x = st.sidebar.number_input("BEACON_3 (X)", value=2.0, step = 0.1)
b3_y = st.sidebar.number_input("BEACON_3 (Y)", value=0.0, step = 0.1)
st.sidebar.subheader("Wymiary pokoju")
room_x = st.sidebar.number_input("Szerokość pokoju [m]", value = 1.0, step = 0.1)
room_y = st.sidebar.number_input("Długość pokoju [m]", value = 2.5, step = 0.1)


beacons = {
    "BEACON_1": (b1_x,b1_y),
    "BEACON_2": (b2_x,b2_y),
    "BEACON_3": (b3_x,b3_y),
}



#podzial na karty
tab_map, tab_login, tab_logs = st.tabs(["Mapa Lokalizacji - heatmapa", "Konfiguracja", "Odebrano"])

with tab_login:
    st.header("Połączenie ESP32 z siecią")
    st.info('Najpierw połącz się z siecią "ESP32_AP" (hasło:123454321)')

    with st.form('wifi_form'):
        ssid = st.text_input("SSID Twojej sieci")
        password = st.text_input("Hasło", type="password")
        new_ip = st.text_input("IP laptopa", value = "192.168.1.XX")

        submit_wifi = st.form_submit_button("Połącz z siecią")

        if submit_wifi:
            try:
                target_url = "http://192.168.4.1/set_wifi"
                data = {"ssid": ssid, "pass": password, "ip": new_ip}
                response = requests.post(target_url, data = data, timeout = 5)

                if response.status_code == 200:
                    st.success("Konfiguracja wysłana pomyślnie!")
            except Exception as e:
                st.error(f"Brak połącznia z ESP: {e}")

#interpretacja/odebranie rssi
def get_latest_rssi():
    if not st.session_state.data_log:
        return {}
    
    last_msg = st.session_state.data_log[-1]
    
    try:
        # dekodujemy JSON, bo ESP32 wysyła {"BEACON_1": -65, ...} - tak jak w pilot_http.ino
        data = json.loads(last_msg)
        
        # Upewnijmy się, że klucze są Stringami a wartości Intami
        formatted_data = {str(k): int(v) for k, v in data.items()}
        return formatted_data
    except Exception as e:
        try:
            data = {}
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

    
    
    st.header("Parametry sygnału")
    A = st.slider("Moc z 1 metra (A) [dBm]", -80, -30, -55)
    n = st.slider("Współczynnik tłumienia (n)", 1.0, 5.0, 2.0)

    distances = []
    beacons_found = 0
    for name in ['BEACON_1', 'BEACON_2', 'BEACON_3']:
        rssi_val = current_data.get(name)        
        if rssi_val:
            #przeliczanie na dystans
            dist = rssi_to_distance(rssi_val, A, n)
            distances.append(dist)
            beacons_found += 1
        else:
            distances.append(None)

    fig,ax = plt.subplots()
    for name,pos in beacons.items():
        ax.scatter(pos[0], pos[1], s=100, label=name)
    ax.add_patch(Rectangle((0,0),room_x,room_y, fill=False))
        #ax.text(pos[0] + 0.1, pos[1] + 0.1, name)

    ax.set_xlabel("Szerokość (X) [m]")
    ax.set_ylabel("Długość (Y) [m]")

    #dla kompletu beaconów
    user_pos = None
    if beacons_found == 3:
        user_pos = trilaterate(beacons, distances)
        #jezeli uda sie zrealizowac
        if user_pos:
            st.success(f"Twoja pozycja: X={user_pos[0]:.2f}, Y={user_pos[1]:.2f}")
            ax.scatter(user_pos[0], user_pos[1], color='red', label='Pilot', edgecolor='black')


    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()

    st.pyplot(fig)

    st.write(f"Liczba odebranych pakietów: {len(st.session_state.data_log)}")
    if st.session_state.data_log:
        st.write(f"Ostatnia wiadomość: {st.session_state.data_log[-1]}")

    if st.checkbox("Włącz śledzenie na żywo"):
        time.sleep(0.5) # nie obciążajmy procka zbyt mocno
        st.rerun()

with tab_logs:
    st.header("Podgląd odebranych pakietów")

    if st.session_state.data_log:
        last_logs = st.session_state.data_log[-20:][::-1]

        for i, log in enumerate(last_logs):
            st.code(f"[{i}] {log}", language="json")
        if st.button("Wyczyść historię logów"):
            st.session_state.data_log = []
            st.rerun()
    else:
        st.warning("Brak danych w logach. Sprawdź połączenie UDP i Firewall.")