# app.py
import streamlit as st
import random
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Legends of Nusantara (Prototype)", layout="wide")

# ----------------------
# Utilities & Data
# ----------------------
CLASSES = {
    "Ksatria": {"hp": 30, "atk": 6, "def": 2},
    "Penyihir": {"hp": 22, "atk": 8, "def": 1, "mana": 10},
    "Pemanah": {"hp": 24, "atk": 7, "def": 1, "crit": 0.15},
    "Penjelajah": {"hp": 26, "atk": 5, "def": 2, "dodge": 0.12},
}

ENEMIES = [
    {"name": "Siluman Hutan", "hp": 12, "atk": 4, "def": 0, "exp": 6},
    {"name": "Naga Kecil", "hp": 18, "atk": 6, "def": 1, "exp": 12},
    {"name": "Leak Nakal", "hp": 10, "atk": 5, "def": 0, "exp": 8},
    {"name": "Raksasa Batu", "hp": 24, "atk": 7, "def": 2, "exp": 18},
]

MAP_W = 7
MAP_H = 5

# ----------------------
# Session state init
# ----------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.player_class = None
    st.session_state.player = {}
    st.session_state.pos = [0, 0]  # x,y
    st.session_state.level = 1
    st.session_state.exp = 0
    st.session_state.inventory = {}
    st.session_state.in_battle = False
    st.session_state.enemy = None
    st.session_state.log = []
    st.session_state.map = [["." for _ in range(MAP_W)] for _ in range(MAP_H)]
    st.session_state.map[0][0] = "P"  # start
    st.session_state.visited = set([(0,0)])


# ----------------------
# Helper functions
# ----------------------
def write_log(message):
    st.session_state.log.append(message)
    if len(st.session_state.log) > 30:
        st.session_state.log.pop(0)


def gen_enemy():
    e = random.choice(ENEMIES).copy()
    # small variability
    e["hp"] += random.randint(-2, 3)
    return e


def start_battle():
    st.session_state.in_battle = True
    st.session_state.enemy = gen_enemy()
    write_log(f"👾 Musuh muncul: {st.session_state.enemy['name']} (HP {st.session_state.enemy['hp']})")


def end_battle(victory):
    if victory:
        exp = st.session_state.enemy.get("exp", 8)
        st.session_state.exp += exp
        write_log(f"🏆 Kamu menang! Dapat {exp} EXP.")
        # level up simple
        if st.session_state.exp >= st.session_state.level * 20:
            st.session_state.level += 1
            st.session_state.player["hp"] += 6
            st.session_state.player["atk"] += 1
            write_log(f"✨ Level up! Sekarang level {st.session_state.level}. HP dan ATK meningkat.")
    else:
        # penalty: respawn to start
        st.session_state.pos = [0, 0]
        st.session_state.player["hp"] = max(1, st.session_state.player["hp"] // 2)
        write_log("💥 Kamu kalah dan kembali ke start dengan HP dipotong.")

    st.session_state.in_battle = False
    st.session_state.enemy = None


def enemy_turn():
    if not st.session_state.enemy:
        return
    e = st.session_state.enemy
    dmg = max(0, e["atk"] - st.session_state.player.get("def", 0))
    # dodge check
    if st.session_state.player.get("dodge") and random.random() < st.session_state.player["dodge"]:
        write_log("✨ Kamu lolos dari serangan musuh (dodge)!")
        return
    st.session_state.player["hp"] -= dmg
    write_log(f"👾 {e['name']} menyerang dan memberi {dmg} damage. (HP kamu: {st.session_state.player['hp']})")


def player_attack(special=None):
    e = st.session_state.enemy
    player = st.session_state.player
    if not e:
        return
    base_atk = player["atk"]
    if special == "magic":
        if player.get("mana", 0) >= 3:
            dmg = base_atk + 4
            player["mana"] -= 3
            write_log(f"💫 Kamu menggunakan magic dan memberi {dmg} damage.")
        else:
            write_log("❌ Mana tidak cukup!")
            return
    else:
        # critical check
        if player.get("crit") and random.random() < player["crit"]:
            dmg = int((base_atk + 2) * 1.8)
            write_log(f"🔥 Critical! Kamu memberi {dmg} damage.")
        else:
            dmg = base_atk
            write_log(f"⚔️ Kamu menyerang dan memberi {dmg} damage.")
    dmg = max(0, dmg - e.get("def", 0))
    e["hp"] -= dmg
    if e["hp"] <= 0:
        end_battle(True)
    else:
        enemy_turn()


def draw_map():
    # create a simple image grid to visualize
    cell = 48
    img = Image.new("RGBA", (MAP_W * cell, MAP_H * cell), (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    fnt = None
    for y in range(MAP_H):
        for x in range(MAP_W):
            left = x * cell
            top = y * cell
            rect_color = (60, 160, 100) if (x, y) in st.session_state.visited else (40, 40, 80)
            draw.rectangle([left+2, top+2, left+cell-2, top+cell-2], fill=rect_color, outline=(20,20,20))
            # mark player
            if [x, y] == st.session_state.pos:
                draw.ellipse([left+10, top+10, left+cell-10, top+cell-10], fill=(255,220,50))
            # maybe mark visited with a small dot
            if (x, y) in st.session_state.visited:
                draw.text((left+6, top+4), "·", fill=(255,255,255))
    return img


# ----------------------
# UI layout
# ----------------------
st.title("⚔️ Legends of Nusantara — Prototype RPG (Streamlit)")
col1, col2 = st.columns([2, 1])

with col1:
    # Character selection / status
    st.subheader("Karakter & Status")
    if st.session_state.player_class is None:
        class_choice = st.radio("Pilih kelas:", list(CLASSES.keys()))
        if st.button("Buat Karakter"):
            st.session_state.player_class = class_choice
            base = CLASSES[class_choice].copy()
            st.session_state.player = base
            st.session_state.pos = [0, 0]
            st.session_state.visited = set([(0,0)])
            st.session_state.map = [["." for _ in range(MAP_W)] for _ in range(MAP_H)]
            st.session_state.map[0][0] = "P"
            write_log(f"✅ Karakter dibuat: {class_choice} (HP {base['hp']}, ATK {base['atk']})")
            st.experimental_rerun()
    else:
        st.markdown(f"**Kelas:** {st.session_state.player_class}")
        st.markdown(f"**Level:** {st.session_state.level} — **EXP:** {st.session_state.exp}/{st.session_state.level*20}")
        st.markdown(f"**HP:** {st.session_state.player.get('hp',0)}    **ATK:** {st.session_state.player.get('atk',0)}    **DEF:** {st.session_state.player.get('def',0)}")
        if "mana" in st.session_state.player:
            st.markdown(f"**Mana:** {st.session_state.player.get('mana')}")
        st.markdown("**Inventori:** " + (", ".join(st.session_state.inventory.keys()) or "Kosong"))

    st.markdown("---")
    st.subheader("Eksplorasi Map")
    map_img = draw_map()
    st.image(map_img, width=MAP_W*48)

    if st.session_state.player_class:
        if st.session_state.in_battle:
            st.warning("⚠️ Sedang dalam pertarungan!")
        else:
            # movement buttons
            col_up, col_mid, col_down = st.columns([1,2,1])
            with col_up:
                if st.button("↑ (Atas)"):
                    x,y = st.session_state.pos
                    if y-1 >= 0:
                        st.session_state.pos = [x, y-1]
                # rerun not necessary
            with col_mid:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("← (Kiri)"):
                        x,y = st.session_state.pos
                        if x-1 >= 0:
                            st.session_state.pos = [x-1, y]
                with c2:
                    st.write("")
                with c3:
                    if st.button("→ (Kanan)"):
                        x,y = st.session_state.pos
                        if x+1 < MAP_W:
                            st.session_state.pos = [x+1, y]
            with col_down:
                if st.button("↓ (Bawah)"):
                    x,y = st.session_state.pos
                    if y+1 < MAP_H:
                        st.session_state.pos = [x, y+1]

            # after movement
            px, py = st.session_state.pos
            st.session_state.visited.add((px, py))
            # random encounter chance
            if not st.session_state.in_battle and random.random() < 0.25:
                start_battle()

with col2:
    st.subheader("Pertempuran")
    if st.session_state.in_battle and st.session_state.enemy:
        e = st.session_state.enemy
        st.markdown(f"**Musuh:** {e['name']}  — HP: {e['hp']}")
        st.markdown(f"**HP Kamu:** {st.session_state.player.get('hp')}")
        atk_col1, atk_col2 = st.columns(2)
        with atk_col1:
            if st.button("Serang"):
                player_attack()
            if "mana" in st.session_state.player:
                if st.button("Magic"):
                    player_attack(special="magic")
        with atk_col2:
            if st.button("Defend"):
                # reduce incoming damage on next enemy turn
                st.session_state.player["def"] = st.session_state.player.get("def",0) + 2
                write_log("🛡️ Kamu bertahan. DEF meningkat sementara.")
                enemy_turn()
                # restore def small
                st.session_state.player["def"] = max(0, st.session_state.player.get("def",0) - 2)
            if st.button("Lari"):
                if random.random() < 0.5:
                    st.session_state.in_battle = False
                    st.session_state.enemy = None
                    write_log("🏃‍♀️ Kamu berhasil kabur!")
                else:
                    write_log("❌ Gagal kabur!")
                    enemy_turn()
    else:
        st.info("Tidak ada pertarungan sekarang. Jelajahi map untuk menemukan musuh.")

    st.markdown("---")
    st.subheader("Log")
    for entry in reversed(st.session_state.log):
        st.write(entry)

st.markdown("---")
st.caption("Prototype sederhana — ide: Legends of Nusantara. Kamu bisa kembangkan loot, quest, NPC, dan visual lebih detil.")

# Auto check player death
if st.session_state.player and st.session_state.player.get("hp", 0) <= 0:
    write_log("⚠️ HP habis! Kamu tewas...")
    # respawn
    st.session_state.player["hp"] = max(1, CLASSES[st.session_state.player_class]["hp"] // 2)
    st.session_state.pos = [0,0]
    st.session_state.in_battle = False
    st.session_state.enemy = None
    write_log("🔁 Kamu di- respawn ke start dengan HP dipulihkan sebagian.")
    st.experimental_rerun()
