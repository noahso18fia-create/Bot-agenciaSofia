import os
# Forzar la zona horaria de Venezuela de forma segura para Windows y Linux
os.environ['TZ'] = 'America/Caracas'
try:
    import time
    if hasattr(time, 'tzset'):
        time.tzset()
except Exception as e:
    print(f"⚠️ Nota sobre tzset: {e}")

import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3
from datetime import datetime, time as dtime
import random
import json
import telebot
import traceback
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Desactivar advertencias de certificados SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES Y ENLACES (Agencia Sofia)
# ==========================================
TOKEN = '8893057303:AAHi1D9GJEentjBJJB_6IdMNtSbQ2jxj7WQ'
CANAL = '@agenciasofiaoficial'
ENLACE_CANAL = 'https://t.me/agenciasofiaoficial'

bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

# Archivo local para control de registros persistentes y evitar duplicados
ARCH_REGISTRO = "resultados_enviados.json"

# Variables globales para control de recomendaciones, aciertos y conteo diario de animales
RECOMENDADOS_HOY = {}
ACIERTOS_HOY = set()
CONTEO_ANIMALES_HOY = {}

# Pool completo de animalitos para los análisis automáticos
ANIMALES_POOL = [
    "00 - Ballena", "0- Delfin","01 - Carnero", "02 - Toro", "03 - Ciempiés", "04 - Alacrán", 
    "05 - León", "06 - Rana", "07 - Perico", "08 - Ratón", "09 - Águila", 
    "10 - Tigre", "11 - Gato", "12 - Caballo", "13 - Mono", "14 - Paloma", 
    "15 - Zorro", "16 - Oso", "17 - Pavo", "18 - Burro", "19 - Chivo", 
    "20 - Cochino", "21 - Gallo", "22 - Camello", "23 - Cebra", "24 - Iguana", 
    "25 - Gallina", "26 - Vaca", "27 - Perro", "28 - Zamuro", "29 - Elefante", 
    "30 - Caimán", "31 - Lapa", "32 - Ardilla", "33 - Pescado", "34 - Venado", 
    "35 - Jirafa", "36 - Culebra"
]

# ==========================================
# ANIMALES GUÁCHARO ACTIVO (00/0 AL 75)
# ==========================================
ANIMALES_GUACHARO = [
    "00 - Ballena", "01 - Carnero", "02 - Toro", "03 - Ciempiés",
    "04 - Alacrán", "05 - León", "06 - Rana", "07 - Perico",
    "08 - Ratón", "09 - Águila", "10 - Tigre", "11 - Gato",
    "12 - Caballo", "13 - Mono", "14 - Paloma", "15 - Zorro",
    "16 - Oso", "17 - Pavo", "18 - Burro", "19 - Chivo",
    "20 - Cochino", "21 - Gallo", "22 - Camello", "23 - Cebra",
    "24 - Iguana", "25 - Gallina", "26 - Vaca", "27 - Perro",
    "28 - Zamuro", "29 - Elefante", "30 - Caimán", "31 - Lapa",
    "32 - Ardilla", "33 - Pescado", "34 - Venado", "35 - Jirafa",
    "36 - Culebra", "37 - Tortuga", "38 - Búfalo", "39 - Lechuza",
    "40 - Avispa", "41 - Canguro", "42 - Tucán", "43 - Mariposa",
    "44 - Chigüire", "45 - Garza", "46 - Puma", "47 - Pavo Real",
    "48 - Puercoespín", "49 - Pereza", "50 - Canario", "51 - Pelícano",
    "52 - Pulpo", "53 - Caracol", "54 - Grillo", "55 - Oso Hormiguero",
    "56 - Tiburón", "57 - Pato", "58 - Hormiga", "59 - Pantera",
    "60 - Camaleón", "61 - Panda", "62 - Cachicamo", "63 - Cangrejo",
    "64 - Gavilán", "65 - Araña", "66 - Lobo", "67 - Avestruz",
    "68 - Jaguar", "69 - Conejo", "70 - Bisonte", "71 - Guacamaya",
    "72 - Gorila", "73 - Hipopótamo", "74 - Turpial", "75 - Guácharo"
]

# Diccionario de abreviaturas oficiales solicitadas para resultados individuales
TRADUCCION_LOTERIAS = {
    "L.A": "LOTTO ACTIVO",
    "GRJ": "GRANJITA",
    "S.P": "SELVA PLUS",
    "L.RE": "LOTTO REAL",
    "GHO": "GUACHARO",
    "L.CH": "LOTTO CHAIMA",
    "MJ.M": "MONJE MILLONARIO"
}

HEADER_Sofia = (
    "*AGENCIA SOFIA*\n"
    "*RESULTADOS*\n\n"
    "🎲 *{nombre_loteria}* 🎲\n"
    "Hora: {hora}\n"
    "Animalito: *{resultado}*\n\n"
    "04163199157"
)

app = Flask('')

@app.route('/')
def home():
    return (
        f"¡El bot de resultados individuales de la <b>Agencia Sofia</b> está activo en el canal {CANAL}!<br><br>"
        "<b>Enlaces de prueba rápida (Test):</b><br>"
        "👉 <a href='/test/madrugada'>Probar Saludo de Madrugada</a><br>"
        "👉 <a href='/test/efemeride'>Probar Efeméride y Dato Oculto del Día</a><br>"
        "👉 <a href='/test/piramide'>Probar Pirámide Numérica (Imagen)</a><br>"
        "👉 <a href='/test/regalos'>Probar Regalos del Día</a><br>"
        "👉 <a href='/test/saludo'>Probar Saludo Matutino</a><br>"
        "👉 <a href='/test/estudio_manana'>Probar Análisis de las 8 AM</a><br>"
        "👉 <a href='/test/estudio_mediodia'>Probar Análisis del Mediodía</a><br>"
        "👉 <a href='/test/estudio_tarde'>Probar Análisis de la Tarde</a><br>"
        "👉 <a href='/test/bcv'>Probar Tasa Oficial BCV</a><br>"
        "👉 <a href='/test/sorteo'>Probar Cierre de Sorteo (Min 25/55)</a><br>"
        "👉 <a href='/test/cierre'>Probar Cierre de Jornada (8:00 PM)</a><br>"
        "👉 <a href='/test/combinacion'>Probar Combinación Diaria</a><br>"
        "👉 <a href='/test/resumen_repetidos'>Probar Resumen de Repetidos</a>"
    )

# --- RUTAS DE PRUEBA MANUAL (TESTS) ---
@app.route('/test/madrugada')
def test_madrugada():
    enviar_saludo_madrugada()
    return "Prueba de Saludo de Madrugada ejecutada."

@app.route('/test/efemeride')
def test_efemeride():
    enviar_efemeride_dia()
    return "Prueba de Efeméride y Dato Oculto ejecutada."

@app.route('/test/piramide')
def test_piramide():
    enviar_piramide_diaria()
    return "Prueba de Pirámide Numérica en Imagen ejecutada."

@app.route('/test/regalos')
def test_regalos():
    enviar_regalos_diarios()
    return "Prueba de Regalos del Día ejecutada."

@app.route('/test/regalos_guacharo')
def test_regalos_guacharo():
    enviar_regalitos_guacharo()
    return "Prueba de Regalitos del Día - Guácharo Activo ejecutada."

@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "Prueba de Saludo Matutino ejecutada."

@app.route('/test/estudio_manana')
def test_estudio_estudio_manana():
    enviar_estudio_8am()
    return "Prueba de Análisis de las 8 AM ejecutada."

@app.route('/test/estudio_mediodia')
def test_estudio_mediodia():
    enviar_estudio_mediodia()
    return "Prueba de Análisis del Mediodía ejecutada."

@app.route('/test/estudio_tarde')
def test_estudio_tarde():
    enviar_estudio_tarde()
    return "Prueba de Análisis de la Tarde ejecutada."

@app.route('/test/bcv')
def test_bcv():
    enviar_tasa_dolar()
    return "Prueba de Tasa BCV ejecutada."

@app.route('/test/sorteo')
def test_sorteo():
    enviar_aviso_cierre_sorteo()
    return "Prueba de Cierre de Sorteo ejecutada."

@app.route('/test/cierre')
def test_cierre():
    enviar_mensaje_cierre()
    return "Prueba de Cierre de Jornada ejecutada."

@app.route('/test/combinacion')
def test_combinacion():
    enviar_combinacion_diaria()
    return "Prueba de Combinación Diaria ejecutada."

@app.route('/test/forzar')
def test_forzar():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL,
        "text": "🚨 PRUEBA DIRECTA: Si lees esto, el bot tiene acceso total y perfecto al canal oficial.",
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    return f"Respuesta de Telegram: {r.status_code} - {r.text}"

def limpiar_texto(texto):
    return " ".join(texto.split())

def enviar_telegram(mensaje, disable_web_preview=True):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL, 
        "text": mensaje, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": disable_web_preview
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Error al enviar al canal: {response.text}")
    except Exception as e:
        print(f"⚠️ Excepción de conexión con Telegram: {e}")

def limpiar_recomendaciones_diarias():
    RECOMENDADOS_HOY.clear()
    ACIERTOS_HOY.clear()
    CONTEO_ANIMALES_HOY.clear()

def enviar_saludo_madrugada():
    enviar_telegram(
        "🎯 AGENCIA SOFIA 🎯\n\n"
        "*¡Activados desde temprano! 🌟 Que este día nos traiga mucha suerte y grandes jugadas. ¡Muy buenos días! 🔥*\n"
        "WHATSAPP: 04163199157",
        disable_web_preview=True
    )

def enviar_efemeride_dia():
    ahora = datetime.now()
    mes_dia = ahora.strftime("%m-%d")
    fecha_str = ahora.strftime("%d/%m/%Y")

    efemerides_db = {
        "01-01": ("Año Nuevo y el Día Mundial de la Paz", "01 - Carnero"),
        "01-14": ("Día de la Divina Pastora", "12 - Caballo"),
        "02-04": ("Día Mundial contra el Cáncer", "05 - León"),
        "02-14": ("Día del Amor y la Amistad", "11 - Gato"),
        "03-08": ("Día Internacional de la Mujer", "26 - Vaca"),
        "03-22": ("Día Mundial del Agua", "0 - Delfin"),
        "04-19": ("Día de la Declaración de Independencia", "09 - Águila"),
        "04-22": ("Día Internacional de la Madre Tierra", "30 - Caimán"),
        "05-01": ("Día del Trabajador", "18 - Burro"),
        "05-10": ("Día de la Afrovenezolanidad", "13 - Mono"),
        "06-05": ("Día Mundial del Medio Ambiente", "23 - Cebra"),
        "06-24": ("Batalla de Carabobo", "12 - Caballo"),
        "07-05": ("Día de la Independencia de Venezuela", "09 - Águila"),
        "07-24": ("Natalicio del Libertador Simón Bolívar", "05 - León"),
        "08-03": ("Día de la Bandera Nacional", "09 - Águila"),
        "08-14": ("Día Mundial del Lagarto", "24 - Iguana"),
        "08-25": ("Día del Peluquero", "16 - Oso"),
        "09-08": ("Día de la Virgen del Valle", "33 - Pescado"),
        "10-12": ("Día de la Resistencia Indígena", "14 - Paloma"),
        "10-31": ("Día de la Canción Criolla y Halloween", "36 - Culebra"),
        "11-18": ("Día de la Chinita", "21 - Gallo"),
        "12-24": ("Nochebuena", "27 - Perro"),
        "12-31": ("Fin de Año y la Quema del Año Viejo", "28 - Zamuro")
    }

    if mes_dia in efemerides_db:
        evento, animal_sugerido = efemerides_db[mes_dia]
    else:
        seed_val = int(ahora.strftime("%m%d"))
        rnd = random.Random(seed_val)
        eventos_comunes = [
            ("Día de la buena vibra y la suerte en los negocios", rnd.choice(ANIMALES_POOL)),
            ("Día de activar la suerte y reventar la pizarra", rnd.choice(ANIMALES_POOL)),
            ("Día de buscar el billete y cobrar temprano", rnd.choice(ANIMALES_POOL)),
            ("Día de la gran jugada maestra", rnd.choice(ANIMALES_POOL))
        ]
        evento, animal_sugerido = rnd.choice(eventos_comunes)

    num_oculto = animal_sugerido.split(" - ")[0].zfill(2)
    RECOMENDADOS_HOY[num_oculto] = {"motivo": f"✨ Dato Oculto por Efeméride ({evento})", "hora_emision": ahora}

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        f"📅 *{fecha_str}* — ¡Buenos días mi gente!\n\n"
        f"💡 *¿Sabías qué se celebra hoy?* Hoy se conmemora el *{evento}* 🌟.\n\n"
        "Y como la suerte tiene sus señales, el sistema detectó un **dato oculto** directo de esta celebración para asegurar las jugadas:\n\n"
        f"🔥 *Dato Oculto / Fijo del Día:* `{animal_sugerido}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "¡A cobrar temprano con la energía de hoy! 🍀✨"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def generar_imagen_piramide():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")
    digitos = [int(c) for c in fecha_str if c.isdigit()]
    filas = [digitos]
    while len(filas[-1]) > 1:
        actual = filas[-1]
        siguiente = [(actual[i] + actual[i+1]) % 10 for i in range(len(actual) - 1)]
        filas.append(siguiente)

    seed_val = int(ahora.strftime("%Y%m%d"))
    rnd = random.Random(seed_val)
    candidates = []
    for f in filas:
        for idx in range(len(f) - 1):
            val = (f[idx] * 10 + f[idx+1]) % 37
            candidates.append(f"{val:02d}" if val != 0 else "0")
            candidates.append("00")
        for num in f:
            val = (num * 7) % 37
            candidates.append(f"{val:02d}" if val != 0 else "0")
            candidates.append("00")

    unique_candidates = []
    for c in candidates:
        if c not in unique_candidates:
            unique_candidates.append(c)

    while len(unique_candidates) < 6:
        r_val = rnd.randint(0, 36)
        c_rand = f"{r_val:02d}" if r_val != 0 else ("0" if rnd.random() > 0.5 else "00")
        if c_rand not in unique_candidates:
            unique_candidates.append(c_rand)

    d1 = f"{unique_candidates[0]}-{unique_candidates[1]}-{unique_candidates[2]}"
    d2 = f"{unique_candidates[3]}-{unique_candidates[4]}-{unique_candidates[5]}"

    img_width, img_height = 1000, 1120
    image = Image.new("RGB", (img_width, img_height), color=(30, 10, 10))
    draw = ImageDraw.Draw(image)

    color_dorado = (212, 175, 55)
    color_dorado_claro = (243, 229, 149)
    color_morado = (148, 0, 211)
    color_blanco = (255, 255, 255)
    color_panel = (20, 20, 20)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 24)
        font_pir = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        font_data = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_pir = ImageFont.load_default()
        font_data = ImageFont.load_default()

    draw.text((img_width // 2, 45), "AGENCIA SOFIA", fill=color_dorado, anchor="mm", font=font_title)
    draw.text((img_width // 2, 90), "Trabajamos para tí", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((img_width // 2, 145), "PIRÁMIDE DEL DÍA", fill=color_morado, anchor="mm", font=font_title)

    draw.rectangle([img_width // 2 - 180, 185, img_width // 2 + 180, 240], fill=color_panel, outline=color_dorado, width=2)
    draw.text((img_width // 2, 212), f"📅  {fecha_str}", fill=color_dorado_claro, anchor="mm", font=font_data)

    panel_bottom = 740
    draw.rectangle([40, 290, 280, panel_bottom], fill=color_panel, outline=color_morado, width=2)
    draw.text((160, 315), "★ DATOS ★", fill=color_dorado, anchor="mm", font=font_data)
    draw.text((160, 355), "NÚMEROS USADOS", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((160, 390), f"{len(set([d for f in filas for d in f])) * 4}", fill=color_dorado_claro, anchor="mm", font=font_data)
    draw.text((160, 440), "SUMA TOTAL", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((160, 475), f"{sum([sum(f) for f in filas]) * 3}", fill=color_dorado_claro, anchor="mm", font=font_data)
    draw.text((160, 525), "NÚMERO MAYOR", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((160, 560), f"{max([max(f) for f in filas])}", fill=color_dorado_claro, anchor="mm", font=font_data)
    draw.text((160, 610), "NÚMERO MENOR", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((160, 645), f"{min([min(f) for f in filas])}", fill=color_dorado_claro, anchor="mm", font=font_data)
    draw.text((160, 695), "NÚMERO FRECUENTE", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((160, 730), f"{digitos[0]} (7 VECES)", fill=color_dorado_claro, anchor="mm", font=font_data)

    draw.rectangle([720, 290, 960, panel_bottom], fill=color_panel, outline=color_morado, width=2)
    draw.text((840, 315), "★ SUMA ★", fill=color_dorado, anchor="mm", font=font_data)
    draw.text((840, 350), "POR FILA", fill=color_dorado, anchor="mm", font=font_data)
    
    y_suma_pos = 400
    for idx, f in enumerate(filas):
        suma_fila = sum(f)
        draw.text((840, y_suma_pos), f"{idx+1}RA FILA: {suma_fila}", fill=color_blanco, anchor="mm", font=font_sub)
        y_suma_pos += 40

    start_y = 280
    row_height = 54
    center_x = img_width // 2
    circle_radius = 23

    for i, f in enumerate(filas):
        num_items = len(f)
        total_width = num_items * 52
        start_x_row = center_x - (total_width // 2)

        for j, num in enumerate(f):
            cx = start_x_row + (j * 52) + 24
            cy = start_y + (i * row_height) + 24
            
            draw.ellipse([cx - circle_radius, cy - circle_radius, cx + circle_radius, cy + circle_radius], fill=color_panel, outline=color_dorado, width=3)
            draw.text((cx, cy), str(num), fill=color_blanco, anchor="mm", font=font_pir)

    box_top = 760
    draw.rectangle([150, box_top, img_width - 150, box_top + 150], fill=color_panel, outline=color_dorado, width=2)
    draw.text((img_width // 2, box_top + 28), "🔥 DATOS CLAVES PARA HOY:", fill=color_dorado, anchor="mm", font=font_sub)
    draw.text((img_width // 2, box_top + 75), f"📌 {d1}", fill=color_blanco, anchor="mm", font=font_data)
    draw.text((img_width // 2, box_top + 115), f"📌 {d2}", fill=color_blanco, anchor="mm", font=font_data)

    footer_y = 955
    draw.text((img_width // 2, footer_y), "WHATSAPP: 04163199157", fill=color_dorado_claro, anchor="mm", font=font_sub)

    bio = BytesIO()
    bio.name = 'piramide_sofia.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio

def enviar_piramide_diaria():
    try:
        foto_bio = generar_imagen_piramide()
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        files = {'photo': foto_bio}
        data = {
            'chat_id': CANAL,
            'caption': f"📢 *REPORTE TÁCTICO - LA PIRÁMIDE*\n\nWHATSAPP: 04163199157\n{ENLACE_CANAL}",
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=data, files=files, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ Error al enviar imagen de pirámide: {response.text}")
    except Exception as e:
        print(f"Error generando/enviando imagen pirámide: {e}")

def enviar_regalos_diarios():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")

    # ==========================================================
    # REGALOS DEL OTRO BOT
    # Deben ser exactamente los mismos que genera tu otro bot
    # ==========================================================
    seed_otro_bot = int(ahora.strftime("%Y%m%d")) + 99
    rnd_otro_bot = random.Random(seed_otro_bot)

    regalos_otro_bot = rnd_otro_bot.sample(ANIMALES_POOL, 3)

    numeros_otro_bot = set()

    for animal in regalos_otro_bot:
        numero = animal.split(" - ")[0].strip()

        if numero.isdigit():
            numero = f"{int(numero):02d}"

        numeros_otro_bot.add(numero)

    print("🎁 Regalos del otro bot:", numeros_otro_bot)

    # ==========================================================
    # REGALOS AGENCIA SOFIA
    # Se seleccionan únicamente del 00 al 36
    # EXCLUYENDO los que ya usa el otro bot
    # ==========================================================
    disponibles_sofia = []

    for animal in ANIMALES_POOL:
        numero = animal.split(" - ")[0].strip()

        if numero.isdigit():
            numero_normalizado = f"{int(numero):02d}"
        else:
            numero_normalizado = numero

        if numero_normalizado not in numeros_otro_bot:
            disponibles_sofia.append(animal)

    # Semilla diferente para que Sofia tenga una selección propia
    seed_sofia = int(ahora.strftime("%Y%m%d")) + 2026
    rnd_sofia = random.Random(seed_sofia)

    regalos_seleccionados = rnd_sofia.sample(disponibles_sofia, 3)

    # ==========================================================
    # REGISTRAR LOS REGALOS DE SOFIA
    # ==========================================================
    for animal in regalos_seleccionados:
        numero = animal.split(" - ")[0].strip()

        if numero.isdigit():
            numero = f"{int(numero):02d}"

        RECOMENDADOS_HOY[numero] = {
            "motivo": "🎁 Regalo del Día - Agencia Sofia",
            "hora_emision": ahora
        }

    # ==========================================================
    # MENSAJE
    # ==========================================================
    mensaje_regalos = (
        "🎁 *LOS REGALOS DE LA AGENCIA SOFIA* 🎁\n"
        f"📅 Fecha: {fecha_str}\n\n"
        "🔥 *Regalitos exclusivos de Agencia Sofia:*\n\n"
        f"🌟 *1er Regalo:* {regalos_seleccionados[0]}\n"
        f"🌟 *2do Regalo:* {regalos_seleccionados[1]}\n"
        f"🌟 *3er Regalo:* {regalos_seleccionados[2]}\n\n"
        "📲 WHATSAPP: 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 ¡Mucha suerte en tus jugadas!"
    )

    enviar_telegram(mensaje_regalos, disable_web_preview=True)
def enviar_regalitos_guacharo():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")

    # ==========================================
    # REGALITOS EXCLUSIVOS - GUÁCHARO ACTIVO
    # ==========================================
    # Semilla diaria: los 5 regalitos se mantienen
    # iguales durante todo el día y cambian mañana.
    seed_val = int(ahora.strftime("%Y%m%d")) + 7575
    rnd = random.Random(seed_val)

    # Seleccionar exactamente 5 animales diferentes
    regalitos = rnd.sample(ANIMALES_GUACHARO, 5)

    # Registrar los números como recomendaciones
    for animal in regalitos:
        partes = animal.split(" - ", 1)
        numero = partes[0].strip()

        # Normalizar 0 -> 00 y números de 1 dígito -> 01, 02...
        if numero.isdigit():
            numero = f"{int(numero):02d}"

        RECOMENDADOS_HOY[numero] = {
            "motivo": "🦜 Regalito del Día - Guácharo Activo",
            "hora_emision": ahora
        }

    # Normalizar presentación de cada regalito
    regalos_formateados = []

    for animal in regalitos:
        partes = animal.split(" - ", 1)

        if len(partes) == 2:
            numero = partes[0].strip()
            nombre = partes[1].strip()

            if numero.isdigit():
                numero = f"{int(numero):02d}"

            regalos_formateados.append(f"{numero} - {nombre}")
        else:
            regalos_formateados.append(animal)

    mensaje = (
        "🎁 *REGALITOS DEL DÍA* 🎁\n"
        "🦜 *GUÁCHARO ACTIVO* 🦜\n"
        f"📅 Fecha: {fecha_str}\n\n"
        f"🌟 *1er Regalito:* {regalos_formateados[0]}\n"
        f"🌟 *2do Regalito:* {regalos_formateados[1]}\n"
        f"🌟 *3er Regalito:* {regalos_formateados[2]}\n"
        f"🌟 *4to Regalito:* {regalos_formateados[3]}\n"
        f"🌟 *5to Regalito:* {regalos_formateados[4]}\n\n"
        "🦜 *Datos seleccionados exclusivamente del listado Guácharo Activo 00 al 75.*\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 ¡Mucha suerte en tus jugadas!"
    )

    enviar_telegram(mensaje, disable_web_preview=True)


def obtener_animales_salidos_actuales():
    salidos = set()
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            texto_total = soup.get_text(" ", strip=True)
            matches = re.findall(r'(\d{1,2})\s*-\s*([A-ZÁÉÍÓÚÑa-zñáéíóú]+)', texto_total)
            for m in matches:
                num_str = f"{int(m[0]):02d}" if m[0].isdigit() else m[0]
                salidos.add(num_str)
    except Exception as e:
        print(f"Error obteniendo salidos para análisis: {e}")
    return salidos

def seleccionar_analisis_dinamico(cantidad):
    salidos = obtener_animales_salidos_actuales()
    disponibles = [a for a in ANIMALES_POOL if a.split(" - ")[0].zfill(2) not in salidos]
     
    if len(disponibles) < cantidad:
        disponibles = ANIMALES_POOL

    seed_val = int(datetime.now().strftime("%Y%m%d%H%M"))
    rnd = random.Random(seed_val)
    return rnd.sample(disponibles, cantidad)

def enviar_combinacion_diaria():
    ahora = datetime.now()
    salidos = obtener_animales_salidos_actuales()
    disponibles = [a for a in ANIMALES_POOL if a.split(" - ")[0].zfill(2) not in salidos]
    if len(disponibles) < 7:
        disponibles = ANIMALES_POOL

    seed_val = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    rnd = random.Random(seed_val)
    seleccionados = rnd.sample(disponibles, 7)

    fijo1 = seleccionados[0]
    fijo2 = seleccionados[1]
    par1 = seleccionados[2]
    par2 = seleccionados[3]
    trip1 = seleccionados[4]
    trip2 = seleccionados[5]
    trip3 = seleccionados[6]

    for animal in seleccionados:
        num = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[num] = {"motivo": "🎯 Combinación Especial Sofia", "hora_emision": ahora}

    par_str = f"{par1.split(' - ')[0]} - {par2.split(' - ')[0]}"
    trip_str = f"{trip1.split(' - ')[0]} - {trip2.split(' - ')[0]} - {trip3.split(' - ')[0]}"

    mensaje = (
        "🎯 *COMBINACIÓN GANADORA - AGENCIA SOFIA* 🎯\n"
        "🔥 ¡Datos exclusivos y directos para asegurar tus jugadas:\n\n"
        f"📌 *Fijos del Día:* `{fijo1}` y `{fijo2}`\n"
        f"📌 *El Par:* `{par_str}`\n"
        f"📌 *La Tripleta:* `{trip_str}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "¡A cobrar se ha dicho! 🍀✨"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_estudio_8am():
    ahora = datetime.now()
    analisis = seleccionar_analisis_dinamico(2)
    for animal in analisis:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = {"motivo": "🔍 Análisis 8:15 AM", "hora_emision": ahora}

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "🔍 *ANÁLISIS TRAS EL SORTEO DE LAS 8:00 AM* 🔍\n\n"
        "¡Ya salieron los primeros animalitos! Evaluando la apertura de la pizarra y descartando lo ya jugado, la casa trae las recomendaciones probables para los siguientes sorteos:\n\n"
        f"🔥 *Regalitos recomendados:* `{analisis[0]}` y `{analisis[1]}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_estudio_mediodia():
    ahora = datetime.now()
    analisis = seleccionar_analisis_dinamico(2)
    for animal in analisis:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = {"motivo": "☀️ Análisis Mediodía", "hora_emision": ahora}

    tripleta = seleccionar_analisis_dinamico(3)
    for animal in tripleta:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = {"motivo": "🎯 Tripleta Mediodía", "hora_emision": ahora}

    t_str = f"{tripleta[0].split(' - ')[0]} - {tripleta[1].split(' - ')[0]} - {tripleta[2].split(' - ')[0]}"
     
    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "☀️ *ANÁLISIS DEL MEDIODÍA* ☀️\n\n"
        "*¡Mitad de jornada! Estudiando los resultados que nos dejó la mañana y analizando tendencias en vivo, el tablero apunta hacia las siguientes proyecciones:*\n\n"
        f"🔥 *Animales calientes:* `{analisis[0]}` y `{analisis[1]}`\n"
        f"🎯 *Tripleta recomendada:* `{t_str}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_estudio_tarde():
    ahora = datetime.now()
    analisis = seleccionar_analisis_dinamico(2)
    for animal in analisis:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = {"motivo": "🌇 Análisis Tarde", "hora_emision": ahora}

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "🌇 *ANÁLISIS Y CIERRE DE LA TARDE* 🌇\n\n"
        "¡A pocas horas de terminar la jornada! Evaluando el comportamiento de los últimos sorteos y filtrando los ganadores del día, la casa trae los animales con mayor probabilidad de reventar para asegurar el cierre:\n\n"
        f"⚡️ *Imparables de la Tarde / Cierre:* `{analisis[0]}` y `{analisis[1]}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_saludo_matutino():
    enviar_telegram(
        "🎯 AGENCIA SOFIA 🎯\n\n"
        "☀️ ¡Buenos días! Arrancamos la jornada con la mejor actitud y la mejor energía para ganar.\n\n"
        "📲 WHATSAPP: 04163199157\n"
        f"{ENLACE_CANAL}\n"
        "¡Mucho éxito en tus jugadas de hoy! 🍀🔥",
        disable_web_preview=True
    )

def enviar_tasa_dolar():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL_BCV, headers=headers, timeout=15, verify=False)
        precio_dolar = "742,23"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            dolar_div = soup.find('div', id='dolar')
            if dolar_div and dolar_div.find('strong'):
                precio_dolar = dolar_div.find('strong').get_text(strip=True)
        enviar_telegram(
            "💵 TASA OFICIAL BCV 💵\n"
            f"📈 Precio Oficial: Bs. {precio_dolar}\n"
            f"Verifica la tasa oficial en: {URL_BCV}\n"
            f"{ENLACE_CANAL}",
            disable_web_preview=True
        )
    except Exception as e:
        print(f"Error BCV: {e}")

def enviar_mensaje_cierre():
    enviar_telegram(
        "AGENCIA SOFIA\n"
        "🌙 ¡FINAL DE JORNADA! 🌙\n"
        "*¡Listo por hoy! 🚀 Que descansen y sueñen en grande. Mañana nos vemos tempranito con más suerte y nuevos retos. ¡Buenas noches! 🌟💤*\n\n"
        f"{ENLACE_CANAL}",
        disable_web_preview=True
    )

def enviar_aviso_cierre_sorteo():
    enviar_telegram(
        "🛑 *¡ATENCIÓN!* 🛑\n\n"
        "El tiempo de jugadas ha terminado por este sorteo en la **AGENCIA SOFIA**.\n\n"
        f"🤞 ¡Cruzamos los dedos por ti, mucha suerte en tus apuestas! 🎲🔥\n{ENLACE_CANAL}",
        disable_web_preview=True
    )

def cargar_registros():
    if os.path.exists(ARCH_REGISTRO):
        try:
            with open(ARCH_REGISTRO, "r") as f:
                data = json.load(f)
                if data.get("fecha") == datetime.now().strftime("%d-%m-%Y"):
                    return set(data.get("enviados", []))
        except Exception:
            pass
    return set()

def guardar_registros(enviados_set):
    data = {
        "fecha": datetime.now().strftime("%d-%m-%Y"),
        "enviados": list(enviados_set)
    }
    try:
        with open(ARCH_REGISTRO, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error al guardar registros: {e}")

def verificar_y_enviar_resultados_individuales():
    enviados_hoy = cargar_registros()
    es_primera_ejecucion = len(enviados_hoy) == 0
     
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))

        hubo_cambios = False
        nuevos_para_guardar = set(enviados_hoy)

        for tarjeta in tarjetas:
            nombre_loteria = ""
            posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text:
                    if t_text not in ["WINBIG", "RESULTADOS", "RESULTADOS ANIMALITOS", "ANIMALITOS"]:
                        nombre_loteria = t_text
                        break

            if not nombre_loteria:
                lineas = [l.strip().upper() for l in tarjeta.get_text("\n", strip=True).split("\n") if l.strip()]
                for linea in lineas:
                    if len(linea) > 2 and not re.search(r'\d{1,2}:\d{2}', linea) and "PENDIENTE" not in linea and "-" not in linea:
                        if linea not in ["RESULTADOS ANIMALITOS", "ANIMALITOS", "RESULTADOS"]:
                            nombre_loteria = linea
                            break

            if not nombre_loteria or len(nombre_loteria) > 40:
                continue

            nombre_loteria_limpio = limpiar_texto(nombre_loteria)

            nombre_loteria_ind = nombre_loteria_limpio
            for sigla, nombre_largo in TRADUCCION_LOTERIAS.items():
                if sigla in nombre_loteria_limpio.upper() or nombre_loteria_limpio.upper() == sigla:
                    nombre_loteria_ind = nombre_largo
                    break

            if "RULETA ROYAL" in nombre_loteria_limpio.upper() or "RESULTADOS" in nombre_loteria_limpio.upper():
                continue

            slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                if "PENDIENTE" in texto_slot:
                    continue

                match_h = re.search(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b', texto_slot)
                if not match_h:
                    continue
                hora_sorteo_str = match_h.group(1).upper()

                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado = limpiar_texto(match_res.group(1)).upper()
                CONTEO_ANIMALES_HOY[resultado] = CONTEO_ANIMALES_HOY.get(resultado, 0) + 1

                numero = resultado.split("-")[0].strip().zfill(2)

                # VALIDACIÓN DE ACIERTOS CON FILTRO DE HORA ESTRICTO
                if numero in RECOMENDADOS_HOY and numero not in ACIERTOS_HOY:
                    info_rec = RECOMENDADOS_HOY[numero]
                    hora_emision = info_rec["hora_emision"]
                    
                    try:
                        hora_limpia = hora_sorteo_str.replace(" ", "")
                        dt_sorteo = datetime.strptime(hora_limpia, "%I:%M%p")
                        hora_sorteo_dt = datetime.now().replace(hour=dt_sorteo.hour, minute=dt_sorteo.minute, second=0, microsecond=0)
                        
                        if hora_sorteo_dt >= hora_emision:
                            mensaje = (
                                "🎉🎉 *¡ACERTAMOS!* 🎉🎉\n\n"
                                f"✅ {info_rec['motivo']}\n\n"
                                f"🎯 *{resultado}*\n"
                                f"🎲 {nombre_loteria_ind}\n"
                                f"🕒 {hora_sorteo_str}\n\n"
                                f"🍀 *¡Felicidades a todos los que confiaron en Agencia Sofia!*\n"
                                f"{ENLACE_CANAL}"
                            )
                            enviar_telegram(mensaje)
                            ACIERTOS_HOY.add(numero)
                    except Exception as err:
                        print(f"Error evaluando hora de acierto: {err}")

                id_resultado = f"{nombre_loteria_ind}_{hora_sorteo_str}_{resultado}"

                if es_primera_ejecucion:
                    nuevos_para_guardar.add(id_resultado)
                    continue

                if id_resultado not in enviados_hoy:
                    hora_actual_str = datetime.now().strftime("%I:%M %p")
                    mensaje = HEADER_Sofia.format(
                        hora_str=hora_actual_str,
                        nombre_loteria=nombre_loteria_ind,
                        hora=hora_sorteo_str,
                        resultado=resultado
                    ) + f"\n{ENLACE_CANAL}"
                    
                    enviar_telegram(mensaje)
                    nuevos_para_guardar.add(id_resultado)
                    hubo_cambios = True
                    time.sleep(1.5)

        if es_primera_ejecucion:
            guardar_registros(nuevos_para_guardar)
        elif hubo_cambios:
            guardar_registros(nuevos_para_guardar)

    except Exception as e:
        print(f"Error al verificar resultados individuales: {e}")

ultimo_aviso_minuto = ""

def verificar_minuto():
    global ultimo_aviso_minuto
    ahora = datetime.now()
     
    hora_actual_minutos = ahora.hour * 60 + ahora.minute
    inicio_minutos = 7 * 60 + 25   # 07:25 AM
    fin_minutos = 19 * 60 + 55     # 07:55 PM

    if not (inicio_minutos <= hora_actual_minutos <= fin_minutos):
        return

    minuto_actual = ahora.minute
    if minuto_actual in [25, 55]:
        clave_tiempo = ahora.strftime("%H:%M")
        if ultimo_aviso_minuto != clave_tiempo:
            enviar_aviso_cierre_sorteo()
            ultimo_aviso_minuto = clave_tiempo

@bot.message_handler(commands=['resumen', 'tabla'])
def cmd_resumen(message):
    try:
        bot.reply_to(message, "🔍 Consultando resumen de resultados actual, por favor espera...")
         
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            bot.reply_to(message, "⚠️ No se pudo conectar con la página de resultados en este momento.")
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))

        resumen_por_loterias = {}

        for tarjeta in tarjetas:
            try:
                nombre_loteria = ""
                posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
                for pt in posibles_titulos:
                    t_text = pt.get_text(" ", strip=True).upper()
                    if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text:
                        if t_text not in ["WINBIG", "RESULTADOS", "RESULTADOS ANIMALITOS", "ANIMALITOS"]:
                            nombre_loteria = t_text
                            break

                if not nombre_loteria:
                    lineas = [l.strip().upper() for l in tarjeta.get_text("\n", strip=True).split("\n") if l.strip()]
                    for linea in lineas:
                        if len(linea) > 2 and not re.search(r'\d{1,2}:\d{2}', linea) and "PENDIENTE" not in linea and "-" not in linea:
                            if linea not in ["RESULTADOS ANIMALITOS", "ANIMALITOS", "RESULTADOS"]:
                                nombre_loteria = linea
                                break

                if not nombre_loteria or len(nombre_loteria) > 40:
                    continue

                nombre_loteria = limpiar_texto(nombre_loteria)
                 
                for sigla, nombre_largo in TRADUCCION_LOTERIAS.items():
                    if sigla in nombre_loteria.upper() or nombre_loteria.upper() == sigla:
                        nombre_loteria = nombre_largo
                        break

                if "RULETA ROYAL" in nombre_loteria.upper() or "RESULTADOS" in nombre_loteria.upper():
                    continue

                if nombre_loteria not in resumen_por_loterias:
                    resumen_por_loterias[nombre_loteria] = []

                slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
                if not slots_sorteo:
                    slots_sorteo = [tarjeta]

                for slot in slots_sorteo:
                    try:
                        texto_slot = slot.get_text(" ", strip=True).upper()
                         
                        match_h = re.search(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b', texto_slot)
                        if not match_h:
                            continue
                        hora = match_h.group(1).upper()

                        if "PENDIENTE" in texto_slot:
                            resumen_por_loterias[nombre_loteria].append(f"• {hora} ➔ ⏳ Pendiente")
                        else:
                            match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                            if match_res:
                                resultado = limpiar_texto(match_res.group(1)).upper()
                                resumen_por_loterias[nombre_loteria].append(f"• {hora} ➔ {resultado}")
                    except Exception:
                        continue
            except Exception:
                continue

        if not resumen_por_loterias:
            bot.reply_to(message, "⚠️ No se encontraron resultados disponibles en este momento.")
            return

        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        texto_final = (
            "🎯 *AGENCIA SOFIA* 🎯\n"
            "_Trabajamos para tí_\n\n"
            "📊 *RESUMEN DE GANADORES DEL DÍA* 📊\n"
            f"📅 Fecha: {fecha_hoy}\n\n"
        )

        for loteria, items in resumen_por_loterias.items():
            if items:
                texto_final += f"🎲 *{loteria}*\n"
                for item in items:
                    texto_final += f"  {item}\n"
                texto_final += "\n"

        texto_final += f"📲 *WHATSAPP:* 04163199157\n{ENLACE_CANAL}"

        if len(texto_final) > 4000:
            for x in range(0, len(texto_final), 4000):
            	bot.send_message(message.chat.id, texto_final[x:x+4000], parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, texto_final, parse_mode="Markdown")

    except Exception as e:
        print(f"Error general en comando tabla: {e}")
        bot.reply_to(message, f"⚠️ Error técnico: {str(e)}")

def loop_bot():
    schedule.every().day.at("07:00").do(enviar_efemeride_dia)
    schedule.every().day.at("06:31").do(enviar_piramide_diaria)
    schedule.every().day.at("06:45").do(enviar_regalos_diarios)
    schedule.every().day.at("06:50").do(enviar_regalitos_guacharo)
    schedule.every().day.at("07:30").do(enviar_saludo_matutino)
     
    schedule.every().day.at("08:15").do(enviar_estudio_8am)
    schedule.every().day.at("12:15").do(enviar_estudio_mediodia)
    schedule.every().day.at("16:15").do(enviar_estudio_tarde)
    
    schedule.every().day.at("18:30").do(enviar_tasa_dolar)
    schedule.every().day.at("20:00").do(enviar_mensaje_cierre)
    
    schedule.every().day.at("09:40").do(enviar_combinacion_diaria)
    schedule.every().day.at("13:30").do(enviar_combinacion_diaria)
    schedule.every().day.at("17:30").do(enviar_combinacion_diaria)

    schedule.every().day.at("00:01").do(limpiar_recomendaciones_diarias)
    
    schedule.every(1).minutes.do(verificar_y_enviar_resultados_individuales)
    schedule.every(1).minutes.do(verificar_minuto)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    t_bot = Thread(target=loop_bot)
    t_bot.daemon = True
    t_bot.start()
     
    try:
        bot.remove_webhook()
        t_polling = Thread(target=lambda: bot.infinity_polling(skip_pending=True, interval=3, timeout=20))
        t_polling.daemon = True
        t_polling.start()
    except Exception as e:
        print(f"Error iniciando polling: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
