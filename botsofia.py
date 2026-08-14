import os

# ==========================================
# ZONA HORARIA
# ==========================================
os.environ['TZ'] = 'America/Caracas'

try:
    import time
    if hasattr(time, 'tzset'):
        time.tzset()
except Exception as e:
    print(f"⚠️ Nota sobre tzset: {e}")

import requests
from bs4 import BeautifulSoup
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3
from datetime import datetime
import random
import json
import telebot
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# CONFIGURACIÓN AGENCIA SOFIA
# ==========================================

TOKEN = '8893057303:AAHi1D9GJEentjBJJB_6IdMNtSbQ2jxj7WQ'

CANAL = '@agenciasofiaoficial'

# Coloca aquí el enlace real de tu canal
ENLACE_CANAL = 'https://t.me/agenciasofiaoficial'

TELEFONO = '04163199157'

bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

# Archivo local para evitar duplicados
ARCH_REGISTRO = "resultados_enviados.json"

# Variables para recomendaciones y aciertos
RECOMENDADOS_HOY = {}
ACIERTOS_HOY = set()
CONTEO_ANIMALES_HOY = {}

# ==========================================
# ANIMALES
# ==========================================

ANIMALES_POOL = [
    "00 - Ballena",
    "0 - Delfin",
    "01 - Carnero",
    "02 - Toro",
    "03 - Ciempiés",
    "04 - Alacrán",
    "05 - León",
    "06 - Rana",
    "07 - Perico",
    "08 - Ratón",
    "09 - Águila",
    "10 - Tigre",
    "11 - Gato",
    "12 - Caballo",
    "13 - Mono",
    "14 - Paloma",
    "15 - Zorro",
    "16 - Oso",
    "17 - Pavo",
    "18 - Burro",
    "19 - Chivo",
    "20 - Cochino",
    "21 - Gallo",
    "22 - Camello",
    "23 - Cebra",
    "24 - Iguana",
    "25 - Gallina",
    "26 - Vaca",
    "27 - Perro",
    "28 - Zamuro",
    "29 - Elefante",
    "30 - Caimán",
    "31 - Lapa",
    "32 - Ardilla",
    "33 - Pescado",
    "34 - Venado",
    "35 - Jirafa",
    "36 - Culebra"
]

# ==========================================
# TRADUCCIÓN DE LOTERÍAS
# ==========================================

TRADUCCION_LOTERIAS = {
    "L.A": "LOTTO ACTIVO",
    "GRJ": "GRANJITA",
    "S.P": "SELVA PLUS",
    "L.RE": "LOTTO REAL",
    "GHO": "GUACHARO",
    "L.CH": "LOTTO CHAIMA",
    "MJ.M": "MONJE MILLONARIO"
}

# ==========================================
# PLANTILLA NUEVA DE RESULTADOS
# ==========================================

HEADER_SOFIA = (
    "🎯 AGENCIA SOFIA 🎯\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🎲 🎰 {nombre_loteria} 🎲\n"
    "🕐 Hora: {hora}\n"
    "🐾 Resultado: {resultado}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "📲 04163199157"
)

# ==========================================
# FLASK
# ==========================================

app = Flask('')


@app.route('/')
def home():
    return (
        "<b>🎯 AGENCIA SOFIA 🎯</b><br><br>"
        "El bot de resultados está activo.<br><br>"
        "<b>Enlaces de prueba:</b><br>"
        "👉 <a href='/test/madrugada'>Saludo de Madrugada</a><br>"
        "👉 <a href='/test/piramide'>Pirámide Numérica</a><br>"
        "👉 <a href='/test/regalos'>Regalos del Día</a><br>"
        "👉 <a href='/test/saludo'>Saludo Matutino</a><br>"
        "👉 <a href='/test/estudio_manana'>Análisis 8 AM</a><br>"
        "👉 <a href='/test/estudio_mediodia'>Análisis Mediodía</a><br>"
        "👉 <a href='/test/estudio_tarde'>Análisis Tarde</a><br>"
        "👉 <a href='/test/bcv'>Tasa BCV</a><br>"
        "👉 <a href='/test/sorteo'>Cierre de Sorteo</a><br>"
        "👉 <a href='/test/cierre'>Cierre de Jornada</a><br>"
        "👉 <a href='/test/combinacion'>Combinación Diaria</a><br>"
        "👉 <a href='/test/resumen_repetidos'>Resumen</a>"
    )


# ==========================================
# RUTAS DE PRUEBA
# ==========================================

@app.route('/test/madrugada')
def test_madrugada():
    enviar_saludo_madrugada()
    return "Prueba ejecutada."


@app.route('/test/piramide')
def test_piramide():
    enviar_piramide_diaria()
    return "Pirámide ejecutada."


@app.route('/test/regalos')
def test_regalos():
    enviar_regalos_diarios()
    return "Regalos ejecutados."


@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "Saludo ejecutado."


@app.route('/test/estudio_manana')
def test_estudio_manana():
    enviar_estudio_8am()
    return "Análisis de mañana ejecutado."


@app.route('/test/estudio_mediodia')
def test_estudio_mediodia():
    enviar_estudio_mediodia()
    return "Análisis de mediodía ejecutado."


@app.route('/test/estudio_tarde')
def test_estudio_tarde():
    enviar_estudio_tarde()
    return "Análisis de tarde ejecutado."


@app.route('/test/bcv')
def test_bcv():
    enviar_tasa_dolar()
    return "Tasa BCV ejecutada."


@app.route('/test/sorteo')
def test_sorteo():
    enviar_aviso_cierre_sorteo()
    return "Aviso ejecutado."


@app.route('/test/cierre')
def test_cierre():
    enviar_mensaje_cierre()
    return "Cierre ejecutado."


@app.route('/test/combinacion')
def test_combinacion():
    enviar_combinacion_diaria()
    return "Combinación ejecutada."


@app.route('/test/forzar')
def test_forzar():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CANAL,
        "text": "🚨 PRUEBA DIRECTA - AGENCIA SOFIA 🚨",
        "parse_mode": "Markdown"
    }

    r = requests.post(url, json=payload)

    return f"Respuesta de Telegram: {r.status_code} - {r.text}"


# ==========================================
# FUNCIONES GENERALES
# ==========================================

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
        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            print(f"⚠️ Error Telegram: {response.text}")

    except Exception as e:
        print(f"⚠️ Error conectando con Telegram: {e}")


def limpiar_recomendaciones_diarias():

    RECOMENDADOS_HOY.clear()
    ACIERTOS_HOY.clear()
    CONTEO_ANIMALES_HOY.clear()


# ==========================================
# SALUDO MADRUGADA
# ==========================================

def enviar_saludo_madrugada():

    enviar_telegram(
        "🎯 AGENCIA SOFIA 🎯\n\n"
        "🌟 ¡Activados desde temprano! "
        "Que este día venga cargado de mucha suerte. 🍀🔥\n\n"
        "📲 04163199157",
        disable_web_preview=True
    )


# ==========================================
# PIRÁMIDE
# ==========================================

def generar_imagen_piramide():

    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")

    digitos = [
        int(c)
        for c in fecha_str
        if c.isdigit()
    ]

    filas = [digitos]

    while len(filas[-1]) > 1:

        actual = filas[-1]

        siguiente = [
            (actual[i] + actual[i + 1]) % 10
            for i in range(len(actual) - 1)
        ]

        filas.append(siguiente)

    seed_val = int(ahora.strftime("%Y%m%d"))

    rnd = random.Random(seed_val)

    candidates = []

    for f in filas:

        for idx in range(len(f) - 1):

            val = (f[idx] * 10 + f[idx + 1]) % 37

            candidates.append(
                f"{val:02d}" if val != 0 else "0"
            )

            candidates.append("00")

        for num in f:

            val = (num * 7) % 37

            candidates.append(
                f"{val:02d}" if val != 0 else "0"
            )

            candidates.append("00")

    unique_candidates = []

    for c in candidates:

        if c not in unique_candidates:
            unique_candidates.append(c)

    while len(unique_candidates) < 6:

        r_val = rnd.randint(0, 36)

        c_rand = (
            f"{r_val:02d}"
            if r_val != 0
            else ("0" if rnd.random() > 0.5 else "00")
        )

        if c_rand not in unique_candidates:
            unique_candidates.append(c_rand)

    d1 = (
        f"{unique_candidates[0]}-"
        f"{unique_candidates[1]}-"
        f"{unique_candidates[2]}"
    )

    d2 = (
        f"{unique_candidates[3]}-"
        f"{unique_candidates[4]}-"
        f"{unique_candidates[5]}"
    )

    img_width = 1000
    img_height = 1120

    image = Image.new(
        "RGB",
        (img_width, img_height),
        color=(30, 10, 10)
    )

    draw = ImageDraw.Draw(image)

    color_dorado = (212, 175, 55)
    color_dorado_claro = (243, 229, 149)
    color_morado = (148, 0, 211)
    color_blanco = (255, 255, 255)
    color_panel = (20, 20, 20)

    try:

        font_title = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            40
        )

        font_sub = ImageFont.truetype(
            "DejaVuSans.ttf",
            24
        )

        font_pir = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            26
        )

        font_data = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            26
        )

    except:

        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_pir = ImageFont.load_default()
        font_data = ImageFont.load_default()

    # Cabecera

    draw.text(
        (img_width // 2, 45),
        "AGENCIA SOFIA",
        fill=color_dorado,
        anchor="mm",
        font=font_title
    )

    draw.text(
        (img_width // 2, 90),
        "Trabajamos para tí",
        fill=color_blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (img_width // 2, 145),
        "PIRÁMIDE DEL DÍA",
        fill=color_morado,
        anchor="mm",
        font=font_title
    )

    # Fecha

    draw.rectangle(
        [
            img_width // 2 - 180,
            185,
            img_width // 2 + 180,
            240
        ],
        fill=color_panel,
        outline=color_dorado,
        width=2
    )

    draw.text(
        (img_width // 2, 212),
        f"📅 {fecha_str}",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_data
    )

    # Panel izquierdo

    panel_bottom = 740

    draw.rectangle(
        [40, 290, 280, panel_bottom],
        fill=color_panel,
        outline=color_morado,
        width=2
    )

    draw.text(
        (160, 315),
        "★ DATOS ★",
        fill=color_dorado,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (160, 355),
        "NÚMEROS USADOS",
        fill=color_blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (160, 390),
        f"{len(set([d for f in filas for d in f])) * 4}",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (160, 440),
        "SUMA TOTAL",
        fill=color_blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (160, 475),
        f"{sum([sum(f) for f in filas]) * 3}",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (160, 525),
        "NÚMERO MAYOR",
        fill=color_blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (160, 560),
        f"{max([max(f) for f in filas])}",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (160, 610),
        "NÚMERO MENOR",
        fill=color_blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (160, 645),
        f"{min([min(f) for f in filas])}",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (160, 695),
        "NÚMERO FRECUENTE",
        fill=color_blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (160, 730),
        f"{digitos[0]} (7 VECES)",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_data
    )

    # Panel derecho

    draw.rectangle(
        [720, 290, 960, panel_bottom],
        fill=color_panel,
        outline=color_morado,
        width=2
    )

    draw.text(
        (840, 315),
        "★ SUMA ★",
        fill=color_dorado,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (840, 350),
        "POR FILA",
        fill=color_dorado,
        anchor="mm",
        font=font_data
    )

    y_suma_pos = 400

    for idx, f in enumerate(filas):

        suma_fila = sum(f)

        draw.text(
            (840, y_suma_pos),
            f"{idx + 1}RA FILA: {suma_fila}",
            fill=color_blanco,
            anchor="mm",
            font=font_sub
        )

        y_suma_pos += 40

    # Pirámide central

    start_y = 280
    row_height = 54
    center_x = img_width // 2
    circle_radius = 23

    for i, f in enumerate(filas):

        num_items = len(f)

        total_width = num_items * 52

        start_x_row = center_x - (
            total_width // 2
        )

        for j, num in enumerate(f):

            cx = (
                start_x_row
                + (j * 52)
                + 24
            )

            cy = (
                start_y
                + (i * row_height)
                + 24
            )

            draw.ellipse(
                [
                    cx - circle_radius,
                    cy - circle_radius,
                    cx + circle_radius,
                    cy + circle_radius
                ],
                fill=color_panel,
                outline=color_dorado,
                width=3
            )

            draw.text(
                (cx, cy),
                str(num),
                fill=color_blanco,
                anchor="mm",
                font=font_pir
            )

    # Datos claves

    box_top = 760

    draw.rectangle(
        [
            150,
            box_top,
            img_width - 150,
            box_top + 150
        ],
        fill=color_panel,
        outline=color_dorado,
        width=2
    )

    draw.text(
        (img_width // 2, box_top + 28),
        "🔥 DATOS CLAVES PARA HOY:",
        fill=color_dorado,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (img_width // 2, box_top + 75),
        f"📌 {d1}",
        fill=color_blanco,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (img_width // 2, box_top + 115),
        f"📌 {d2}",
        fill=color_blanco,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (img_width // 2, 955),
        "WHATSAPP: 04163199157",
        fill=color_dorado_claro,
        anchor="mm",
        font=font_sub
    )

    bio = BytesIO()
    bio.name = 'piramide_sofia.png'

    image.save(
        bio,
        'PNG'
    )

    bio.seek(0)

    return bio


def enviar_piramide_diaria():

    try:

        foto_bio = generar_imagen_piramide()

        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

        files = {
            'photo': foto_bio
        }

        data = {
            'chat_id': CANAL,
            'caption': (
                "🎯 *AGENCIA SOFIA* 🎯\n\n"
                "📊 *REPORTE TÁCTICO - LA PIRÁMIDE*\n\n"
                "📲 04163199157"
            ),
            'parse_mode': 'Markdown'
        }

        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=15
        )

        if response.status_code != 200:
            print(
                f"⚠️ Error enviando pirámide: "
                f"{response.text}"
            )

    except Exception as e:

        print(
            f"Error generando/enviando pirámide: {e}"
        )


# ==========================================
# REGALOS DEL DÍA
# ==========================================

def enviar_regalos_diarios():

    ahora = datetime.now()

    fecha_str = ahora.strftime("%d/%m/%Y")

    seed_val = (
        int(ahora.strftime("%Y%m%d"))
        + 99
    )

    rnd = random.Random(seed_val)

    regalos_seleccionados = rnd.sample(
        ANIMALES_POOL,
        3
    )

    for animal in regalos_seleccionados:

        numero = animal.split(" - ")[0].zfill(2)

        RECOMENDADOS_HOY[numero] = (
            "🎁 Regalo del Día"
        )

    mensaje_regalos = (
        "🎁 *REGALOS DE AGENCIA SOFIA* 🎁\n"
        f"📅 Fecha: {fecha_str}\n\n"
        "🌟 *1er Regalo:* "
        f"{regalos_seleccionados[0]}\n"
        "🌟 *2do Regalo:* "
        f"{regalos_seleccionados[1]}\n"
        "🌟 *3er Regalo:* "
        f"{regalos_seleccionados[2]}\n\n"
        "📲 04163199157\n\n"
        "🍀 ¡Mucha suerte!"
    )

    enviar_telegram(
        mensaje_regalos,
        disable_web_preview=True
    )


# ==========================================
# OBTENER ANIMALES SALIDOS
# ==========================================

def obtener_animales_salidos_actuales():

    salidos = set()

    try:

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        respuesta = requests.get(
            URL_LOTERIA,
            headers=headers,
            timeout=10
        )

        if respuesta.status_code == 200:

            soup = BeautifulSoup(
                respuesta.text,
                'html.parser'
            )

            texto_total = soup.get_text(
                " ",
                strip=True
            )

            matches = re.findall(
                r'(\d{1,2})\s*-\s*([A-ZÁÉÍÓÚÑa-zñáéíóú]+)',
                texto_total
            )

            for m in matches:

                num_str = (
                    f"{int(m[0]):02d}"
                    if m[0].isdigit()
                    else m[0]
                )

                salidos.add(num_str)

    except Exception as e:

        print(
            f"Error obteniendo salidos: {e}"
        )

    return salidos


# ==========================================
# ANÁLISIS DINÁMICO
# ==========================================

def seleccionar_analisis_dinamico(cantidad):

    salidos = obtener_animales_salidos_actuales()

    disponibles = [
        a
        for a in ANIMALES_POOL
        if a.split(" - ")[0].zfill(2)
        not in salidos
    ]

    if len(disponibles) < cantidad:
        disponibles = ANIMALES_POOL

    seed_val = int(
        datetime.now().strftime("%Y%m%d%H%M")
    )

    rnd = random.Random(seed_val)

    return rnd.sample(
        disponibles,
        cantidad
    )


# ==========================================
# COMBINACIÓN DIARIA
# ==========================================

def enviar_combinacion_diaria():

    salidos = obtener_animales_salidos_actuales()

    disponibles = [
        a
        for a in ANIMALES_POOL
        if a.split(" - ")[0].zfill(2)
        not in salidos
    ]

    if len(disponibles) < 7:
        disponibles = ANIMALES_POOL

    seed_val = int(
        datetime.now().strftime("%Y%m%d%H%M%S")
    )

    rnd = random.Random(seed_val)

    seleccionados = rnd.sample(
        disponibles,
        7
    )

    fijo1 = seleccionados[0]
    fijo2 = seleccionados[1]

    par1 = seleccionados[2]
    par2 = seleccionados[3]

    trip1 = seleccionados[4]
    trip2 = seleccionados[5]
    trip3 = seleccionados[6]

    for animal in seleccionados:

        num = animal.split(" - ")[0].zfill(2)

        RECOMENDADOS_HOY[num] = (
            "🎯 Combinación Especial SOFIA"
        )

    par_str = (
        f"{par1.split(' - ')[0]} - "
        f"{par2.split(' - ')[0]}"
    )

    trip_str = (
        f"{trip1.split(' - ')[0]} - "
        f"{trip2.split(' - ')[0]} - "
        f"{trip3.split(' - ')[0]}"
    )

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n\n"
        "🔥 *COMBINACIÓN DEL DÍA*\n\n"
        f"📌 *Fijos:* `{fijo1}` y `{fijo2}`\n"
        f"📌 *El Par:* `{par_str}`\n"
        f"📌 *La Tripleta:* `{trip_str}`\n\n"
        "📲 04163199157"
    )

    enviar_telegram(
        mensaje,
        disable_web_preview=True
    )


# ==========================================
# ANÁLISIS 8 AM
# ==========================================

def enviar_estudio_8am():

    analisis = seleccionar_analisis_dinamico(2)

    for animal in analisis:

        numero = animal.split(" - ")[0].zfill(2)

        RECOMENDADOS_HOY[numero] = (
            "🔍 Análisis 8:15 AM"
        )

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔍 *ANÁLISIS 8:15 AM*\n\n"
        f"🔥 *Recomendados:* `{analisis[0]}` "
        f"y `{analisis[1]}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📲 04163199157"
    )

    enviar_telegram(
        mensaje,
        disable_web_preview=True
    )


# ==========================================
# ANÁLISIS MEDIODÍA
# ==========================================

def enviar_estudio_mediodia():

    analisis = seleccionar_analisis_dinamico(2)

    for animal in analisis:

        numero = animal.split(" - ")[0].zfill(2)

        RECOMENDADOS_HOY[numero] = (
            "☀️ Análisis Mediodía"
        )

    tripleta = seleccionar_analisis_dinamico(3)

    for animal in tripleta:

        numero = animal.split(" - ")[0].zfill(2)

        RECOMENDADOS_HOY[numero] = (
            "🎯 Tripleta Mediodía"
        )

    t_str = (
        f"{tripleta[0].split(' - ')[0]} - "
        f"{tripleta[1].split(' - ')[0]} - "
        f"{tripleta[2].split(' - ')[0]}"
    )

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "☀️ *ANÁLISIS DEL MEDIODÍA*\n\n"
        f"🔥 *Animales calientes:* "
        f"`{analisis[0]}` y `{analisis[1]}`\n\n"
        f"🎯 *Tripleta:* `{t_str}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📲 04163199157"
    )

    enviar_telegram(
        mensaje,
        disable_web_preview=True
    )


# ==========================================
# ANÁLISIS TARDE
# ==========================================

def enviar_estudio_tarde():

    analisis = seleccionar_analisis_dinamico(2)

    for animal in analisis:

        numero = animal.split(" - ")[0].zfill(2)

        RECOMENDADOS_HOY[numero] = (
            "🌇 Análisis Tarde"
        )

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🌇 *ANÁLISIS DE LA TARDE*\n\n"
        f"⚡️ *Imparables:* `{analisis[0]}` "
        f"y `{analisis[1]}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📲 04163199157"
    )

    enviar_telegram(
        mensaje,
        disable_web_preview=True
    )


# ==========================================
# SALUDO MATUTINO
# ==========================================

def enviar_saludo_matutino():

    enviar_telegram(
        "🎯 AGENCIA SOFIA 🎯\n\n"
        "☀️ ¡Buenos días!\n\n"
        "Arrancamos la jornada con la mejor "
        "actitud y mucha energía. 🍀🔥\n\n"
        "📲 04163199157",
        disable_web_preview=True
    )


# ==========================================
# TASA BCV
# ==========================================

def enviar_tasa_dolar():

    try:

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        response = requests.get(
            URL_BCV,
            headers=headers,
            timeout=15,
            verify=False
        )

        precio_dolar = "742,23"

        if response.status_code == 200:

            soup = BeautifulSoup(
                response.text,
                'html.parser'
            )

            dolar_div = soup.find(
                'div',
                id='dolar'
            )

            if (
                dolar_div
                and dolar_div.find('strong')
            ):

                precio_dolar = (
                    dolar_div
                    .find('strong')
                    .get_text(strip=True)
                )

        enviar_telegram(
            "💵 *TASA OFICIAL BCV* 💵\n\n"
            f"📈 Precio Oficial: Bs. {precio_dolar}\n\n"
            "🎯 AGENCIA SOFIA\n"
            "📲 04163199157",
            disable_web_preview=True
        )

    except Exception as e:

        print(f"Error BCV: {e}")


# ==========================================
# CIERRE DE JORNADA
# ==========================================

def enviar_mensaje_cierre():

    enviar_telegram(
        "🎯 AGENCIA SOFIA 🎯\n\n"
        "🌙 *FINAL DE JORNADA* 🌙\n\n"
        "¡Listo por hoy! 🚀\n"
        "Gracias por acompañarnos.\n\n"
        "🍀 Mañana seguimos con más suerte.\n\n"
        "📲 04163199157",
        disable_web_preview=True
    )


# ==========================================
# AVISO CIERRE DE SORTEO
# ==========================================

def enviar_aviso_cierre_sorteo():

    enviar_telegram(
        "🛑 *¡ATENCIÓN!* 🛑\n\n"
        "El tiempo de jugadas ha terminado "
        "para este sorteo en:\n\n"
        "🎯 *AGENCIA SOFIA* 🎯\n\n"
        "🍀 ¡Mucha suerte!\n\n"
        "📲 04163199157",
        disable_web_preview=True
    )


# ==========================================
# REGISTRO DE RESULTADOS
# ==========================================

def cargar_registros():

    if os.path.exists(ARCH_REGISTRO):

        try:

            with open(
                ARCH_REGISTRO,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                if (
                    data.get("fecha")
                    == datetime.now().strftime("%d-%m-%Y")
                ):

                    return set(
                        data.get("enviados", [])
                    )

        except Exception:
            pass

    return set()


def guardar_registros(enviados_set):

    data = {
        "fecha": datetime.now().strftime(
            "%d-%m-%Y"
        ),
        "enviados": list(enviados_set)
    }

    try:

        with open(
            ARCH_REGISTRO,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            f"Error guardando registros: {e}"
        )


# ==========================================
# VERIFICAR Y ENVIAR RESULTADOS
# ==========================================

def verificar_y_enviar_resultados_individuales():

    enviados_hoy = cargar_registros()

    es_primera_ejecucion = (
        len(enviados_hoy) == 0
    )

    try:

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        respuesta = requests.get(
            URL_LOTERIA,
            headers=headers,
            timeout=15
        )

        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(
            respuesta.text,
            'html.parser'
        )

        tarjetas = soup.find_all(
            ['div', 'article', 'section'],
            class_=re.compile(
                r'card|box|item|lotto|result',
                re.IGNORECASE
            )
        )

        hubo_cambios = False

        nuevos_para_guardar = set(
            enviados_hoy
        )

        for tarjeta in tarjetas:

            nombre_loteria = ""

            posibles_titulos = tarjeta.find_all(
                [
                    'h1',
                    'h2',
                    'h3',
                    'h4',
                    'h5',
                    'span',
                    'div',
                    'strong',
                    'b'
                ],
                class_=re.compile(
                    r'title|header|name|lotto|text',
                    re.IGNORECASE
                )
            )

            for pt in posibles_titulos:

                t_text = pt.get_text(
                    " ",
                    strip=True
                ).upper()

                if (
                    t_text
                    and len(t_text) > 2
                    and not re.search(
                        r'\d{1,2}:\d{2}',
                        t_text
                    )
                    and "PENDIENTE" not in t_text
                ):

                    if t_text not in [
                        "WINBIG",
                        "RESULTADOS",
                        "RESULTADOS ANIMALITOS",
                        "ANIMALITOS"
                    ]:

                        nombre_loteria = t_text
                        break

            if not nombre_loteria:

                lineas = [
                    l.strip().upper()
                    for l in tarjeta
                    .get_text(
                        "\n",
                        strip=True
                    )
                    .split("\n")
                    if l.strip()
                ]

                for linea in lineas:

                    if (
                        len(linea) > 2
                        and not re.search(
                            r'\d{1,2}:\d{2}',
                            linea
                        )
                        and "PENDIENTE" not in linea
                        and "-" not in linea
                    ):

                        if linea not in [
                            "RESULTADOS ANIMALITOS",
                            "ANIMALITOS",
                            "RESULTADOS"
                        ]:

                            nombre_loteria = linea
                            break

            if (
                not nombre_loteria
                or len(nombre_loteria) > 40
            ):
                continue

            nombre_loteria_limpio = limpiar_texto(
                nombre_loteria
            )

            nombre_loteria_ind = (
                nombre_loteria_limpio
            )

            for sigla, nombre_largo in (
                TRADUCCION_LOTERIAS.items()
            ):

                if (
                    sigla in
                    nombre_loteria_limpio.upper()
                    or
                    nombre_loteria_limpio.upper()
                    == sigla
                ):

                    nombre_loteria_ind = (
                        nombre_largo
                    )

                    break

            if (
                "RULETA ROYAL"
                in nombre_loteria_limpio.upper()
                or
                "RESULTADOS"
                in nombre_loteria_limpio.upper()
            ):
                continue

            slots_sorteo = tarjeta.find_all(
                [
                    'div',
                    'li',
                    'span',
                    'tr'
                ],
                class_=re.compile(
                    r'item|slot|draw|row|col',
                    re.IGNORECASE
                )
            )

            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:

                texto_slot = slot.get_text(
                    " ",
                    strip=True
                ).upper()

                if "PENDIENTE" in texto_slot:
                    continue

                match_h = re.search(
                    r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b',
                    texto_slot
                )

                if not match_h:
                    continue

                hora = match_h.group(1).upper()

                match_res = re.search(
                    r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)',
                    texto_slot
                )

                if not match_res:
                    continue

                resultado = limpiar_texto(
                    match_res.group(1)
                ).upper()

                CONTEO_ANIMALES_HOY[
                    resultado
                ] = (
                    CONTEO_ANIMALES_HOY.get(
                        resultado,
                        0
                    ) + 1
                )

                numero = (
                    resultado
                    .split("-")[0]
                    .strip()
                    .zfill(2)
                )

                # ==================================
                # DETECTAR ACIERTOS
                # ==================================

                if (
                    numero in RECOMENDADOS_HOY
                    and numero not in ACIERTOS_HOY
                ):

                    mensaje = (
                        "🎉🎉 *¡ACERTAMOS!* 🎉🎉\n\n"
                        f"✅ {RECOMENDADOS_HOY[numero]}\n\n"
                        f"🎯 *{resultado}*\n"
                        f"🎲 {nombre_loteria_ind}\n"
                        f"🕒 {hora}\n\n"
                        "🍀 ¡Felicidades!\n"
                        "🎯 *AGENCIA SOFIA*\n"
                        "📲 04163199157"
                    )

                    enviar_telegram(mensaje)

                    ACIERTOS_HOY.add(numero)

                # ==================================
                # ID ÚNICO DEL RESULTADO
                # ==================================

                id_resultado = (
                    f"{nombre_loteria_ind}_"
                    f"{hora}_"
                    f"{resultado}"
                )

                # Primera ejecución:
                # guarda lo existente sin enviarlo
                if es_primera_ejecucion:

                    nuevos_para_guardar.add(
                        id_resultado
                    )

                    continue

                # Nuevo resultado
                if id_resultado not in enviados_hoy:

                    mensaje = HEADER_SOFIA.format(
                        nombre_loteria=nombre_loteria_ind,
                        hora=hora,
                        resultado=resultado
                    )

                    enviar_telegram(
                        mensaje,
                        disable_web_preview=True
                    )

                    nuevos_para_guardar.add(
                        id_resultado
                    )

                    hubo_cambios = True

                    time.sleep(1.5)

        if es_primera_ejecucion:

            guardar_registros(
                nuevos_para_guardar
            )

        elif hubo_cambios:

            guardar_registros(
                nuevos_para_guardar
            )

    except Exception as e:

        print(
            "Error verificando resultados: "
            f"{e}"
        )


# ==========================================
# AVISOS DE CIERRE 25 / 55
# ==========================================

ultimo_aviso_minuto = ""


def verificar_minuto():

    global ultimo_aviso_minuto

    ahora = datetime.now()

    hora_actual_minutos = (
        ahora.hour * 60
        + ahora.minute
    )

    inicio_minutos = (
        7 * 60 + 25
    )

    fin_minutos = (
        19 * 60 + 55
    )

    if not (
        inicio_minutos
        <= hora_actual_minutos
        <= fin_minutos
    ):
        return

    minuto_actual = ahora.minute

    if minuto_actual in [25, 55]:

        clave_tiempo = ahora.strftime(
            "%H:%M"
        )

        if (
            ultimo_aviso_minuto
            != clave_tiempo
        ):

            enviar_aviso_cierre_sorteo()

            ultimo_aviso_minuto = (
                clave_tiempo
            )


# ==========================================
# COMANDO /RESUMEN Y /TABLA
# ==========================================

@bot.message_handler(
    commands=['resumen', 'tabla']
)
def cmd_resumen(message):

    try:

        bot.reply_to(
            message,
            "🔍 Consultando resultados de AGENCIA SOFIA..."
        )

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        respuesta = requests.get(
            URL_LOTERIA,
            headers=headers,
            timeout=15
        )

        if respuesta.status_code != 200:

            bot.reply_to(
                message,
                "⚠️ No se pudo conectar con "
                "la página de resultados."
            )

            return

        soup = BeautifulSoup(
            respuesta.text,
            'html.parser'
        )

        tarjetas = soup.find_all(
            ['div', 'article', 'section'],
            class_=re.compile(
                r'card|box|item|lotto|result',
                re.IGNORECASE
            )
        )

        resumen_por_loterias = {}

        for tarjeta in tarjetas:

            try:

                nombre_loteria = ""

                posibles_titulos = tarjeta.find_all(
                    [
                        'h1',
                        'h2',
                        'h3',
                        'h4',
                        'h5',
                        'span',
                        'div',
                        'strong',
                        'b'
                    ],
                    class_=re.compile(
                        r'title|header|name|lotto|text',
                        re.IGNORECASE
                    )
                )

                for pt in posibles_titulos:

                    t_text = pt.get_text(
                        " ",
                        strip=True
                    ).upper()

                    if (
                        t_text
                        and len(t_text) > 2
                        and not re.search(
                            r'\d{1,2}:\d{2}',
                            t_text
                        )
                        and "PENDIENTE"
                        not in t_text
                    ):

                        if t_text not in [
                            "WINBIG",
                            "RESULTADOS",
                            "RESULTADOS ANIMALITOS",
                            "ANIMALITOS"
                        ]:

                            nombre_loteria = t_text
                            break

                if not nombre_loteria:

                    lineas = [
                        l.strip().upper()
                        for l in tarjeta
                        .get_text(
                            "\n",
                            strip=True
                        )
                        .split("\n")
                        if l.strip()
                    ]

                    for linea in lineas:

                        if (
                            len(linea) > 2
                            and not re.search(
                                r'\d{1,2}:\d{2}',
                                linea
                            )
                            and "PENDIENTE"
                            not in linea
                            and "-"
                            not in linea
                        ):

                            if linea not in [
                                "RESULTADOS ANIMALITOS",
                                "ANIMALITOS",
                                "RESULTADOS"
                            ]:

                                nombre_loteria = linea
                                break

                if (
                    not nombre_loteria
                    or len(nombre_loteria) > 40
                ):
                    continue

                nombre_loteria = limpiar_texto(
                    nombre_loteria
                )

                for sigla, nombre_largo in (
                    TRADUCCION_LOTERIAS.items()
                ):

                    if (
                        sigla in
                        nombre_loteria.upper()
                        or
                        nombre_loteria.upper()
                        == sigla
                    ):

                        nombre_loteria = (
                            nombre_largo
                        )

                        break

                if (
                    "RULETA ROYAL"
                    in nombre_loteria.upper()
                    or
                    "RESULTADOS"
                    in nombre_loteria.upper()
                ):
                    continue

                if (
                    nombre_loteria
                    not in resumen_por_loterias
                ):

                    resumen_por_loterias[
                        nombre_loteria
                    ] = []

                slots_sorteo = tarjeta.find_all(
                    [
                        'div',
                        'li',
                        'span',
                        'tr'
                    ],
                    class_=re.compile(
                        r'item|slot|draw|row|col',
                        re.IGNORECASE
                    )
                )

                if not slots_sorteo:
                    slots_sorteo = [tarjeta]

                for slot in slots_sorteo:

                    try:

                        texto_slot = slot.get_text(
                            " ",
                            strip=True
                        ).upper()

                        match_h = re.search(
                            r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b',
                            texto_slot
                        )

                        if not match_h:
                            continue

                        hora = (
                            match_h.group(1)
                            .upper()
                        )

                        if "PENDIENTE" in texto_slot:

                            resumen_por_loterias[
                                nombre_loteria
                            ].append(
                                f"• {hora} ➔ ⏳ Pendiente"
                            )

                        else:

                            match_res = re.search(
                                r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)',
                                texto_slot
                            )

                            if match_res:

                                resultado = (
                                    limpiar_texto(
                                        match_res.group(1)
                                    ).upper()
                                )

                                resumen_por_loterias[
                                    nombre_loteria
                                ].append(
                                    f"• {hora} ➔ {resultado}"
                                )

                    except Exception:
                        continue

            except Exception:
                continue

        if not resumen_por_loterias:

            bot.reply_to(
                message,
                "⚠️ No se encontraron resultados."
            )

            return

        fecha_hoy = datetime.now().strftime(
            "%d/%m/%Y"
        )

        texto_final = (
            "🎯 *AGENCIA SOFIA* 🎯\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📊 *RESUMEN DE GANADORES DEL DÍA*\n"
            f"📅 Fecha: {fecha_hoy}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

        for loteria, items in (
            resumen_por_loterias.items()
        ):

            if items:

                texto_final += (
                    f"🎲 *{loteria}*\n"
                )

                for item in items:

                    texto_final += (
                        f"  {item}\n"
                    )

                texto_final += "\n"

        texto_final += (
            "━━━━━━━━━━━━━━━━━━\n"
            "📲 *04163199157*"
        )

        if len(texto_final) > 4000:

            for x in range(
                0,
                len(texto_final),
                4000
            ):

                bot.send_message(
                    message.chat.id,
                    texto_final[
                        x:x + 4000
                    ],
                    parse_mode="Markdown"
                )

        else:

            bot.send_message(
                message.chat.id,
                texto_final,
                parse_mode="Markdown"
            )

    except Exception as e:

        print(
            f"Error general en resumen: {e}"
        )

        bot.reply_to(
            message,
            f"⚠️ Error técnico: {str(e)}"
        )


# ==========================================
# PROGRAMACIÓN
# ==========================================

def loop_bot():

    # Pirámide
    schedule.every().day.at(
        "06:31"
    ).do(enviar_piramide_diaria)

    # Regalos
    schedule.every().day.at(
        "06:45"
    ).do(enviar_regalos_diarios)

    # Saludo
    schedule.every().day.at(
        "07:00"
    ).do(enviar_saludo_matutino)

    # Análisis
    schedule.every().day.at(
        "08:15"
    ).do(enviar_estudio_8am)

    schedule.every().day.at(
        "12:15"
    ).do(enviar_estudio_mediodia)

    schedule.every().day.at(
        "16:15"
    ).do(enviar_estudio_tarde)

    # BCV
    schedule.every().day.at(
        "15:30"
    ).do(enviar_tasa_dolar)

    # Cierre
    schedule.every().day.at(
        "20:00"
    ).do(enviar_mensaje_cierre)

    # ======================================
    # COMBINACIONES
    # ======================================

    schedule.every().day.at(
        "09:40"
    ).do(enviar_combinacion_diaria)

    schedule.every().day.at(
        "13:30"
    ).do(enviar_combinacion_diaria)

    schedule.every().day.at(
        "17:30"
    ).do(enviar_combinacion_diaria)

    # ======================================
    # REINICIO DIARIO
    # ======================================

    schedule.every().day.at(
        "00:01"
    ).do(limpiar_recomendaciones_diarias)

    # ======================================
    # RESULTADOS CADA MINUTO
    # ======================================

    schedule.every(1).minutes.do(
        verificar_y_enviar_resultados_individuales
    )

    # ======================================
    # AVISOS 25 / 55
    # ======================================

    schedule.every(1).minutes.do(
        verificar_minuto
    )

    # ======================================
    # LOOP
    # ======================================

    while True:

        schedule.run_pending()

        time.sleep(1)


# ==========================================
# INICIO
# ==========================================

if __name__ == "__main__":

    t_bot = Thread(
        target=loop_bot
    )

    t_bot.daemon = True
    t_bot.start()

    try:

        bot.remove_webhook()

        t_polling = Thread(
            target=lambda:
            bot.infinity_polling(
                skip_pending=True,
                interval=3,
                timeout=20
            )
        )

        t_polling.daemon = True
        t_polling.start()

    except Exception as e:

        print(
            f"Error iniciando polling: {e}"
        )

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
