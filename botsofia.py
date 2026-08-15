import os

# ==========================================
# ZONA HORARIA VENEZUELA
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
from datetime import datetime
import random
import json
import telebot
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ==========================================
# CONFIGURACIÓN
# ==========================================

TOKEN = os.environ.get(
    "TELEGRAM_TOKEN",
    "8893057303:AAHi1D9GJEentjBJJB_6IdMNtSbQ2jxj7WQ"
)

CANAL = '@agenciasofiaoficial'
ENLACE_CANAL = 'https://t.me/agenciasofiaoficial'

bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

ARCH_REGISTRO = "resultados_enviados_sofia.json"


# ==========================================
# CONTROL DE RECOMENDACIONES
# ==========================================

RECOMENDADOS_HOY = {}
HORAS_RECOMENDACIONES = {}
ACIERTOS_HOY = set()
CONTEO_ANIMALES_HOY = {}


# ==========================================
# ANIMALITOS
# ==========================================

ANIMALES_POOL = [
    "00 - Ballena",
    "0- Delfin",
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
# TRADUCCIÓN LOTERÍAS
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
# HEADER RESULTADOS
# ==========================================

HEADER_SOFIA = (
    "🎯 *AGENCIA SOFÍA* 🎯\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🎰 *{nombre_loteria}*\n"
    "🕐 Hora: {hora}\n"
    "🐾 Resultado: *{resultado}*\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "📲 04163199157\n"
    "https://t.me/agenciasofiaoficial"
)


# ==========================================
# FLASK
# ==========================================

app = Flask('')


@app.route('/')
def home():
    return (
        "🎯 BOT AGENCIA SOFÍA ACTIVO 🎯<br><br>"
        "<b>Pruebas:</b><br>"
        "👉 /test/madrugada<br>"
        "👉 /test/piramide<br>"
        "👉 /test/regalos<br>"
        "👉 /test/saludo<br>"
        "👉 /test/estudio_manana<br>"
        "👉 /test/estudio_mediodia<br>"
        "👉 /test/estudio_tarde<br>"
        "👉 /test/bcv<br>"
        "👉 /test/sorteo<br>"
        "👉 /test/cierre<br>"
        "👉 /test/combinacion"
    )


# ==========================================
# RUTAS DE PRUEBA
# ==========================================

@app.route('/test/madrugada')
def test_madrugada():
    enviar_saludo_madrugada()
    return "OK"


@app.route('/test/piramide')
def test_piramide():
    enviar_piramide_diaria()
    return "OK"


@app.route('/test/regalos')
def test_regalos():
    enviar_regalos_diarios()
    return "OK"


@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "OK"


@app.route('/test/estudio_manana')
def test_estudio_manana():
    enviar_estudio_8am()
    return "OK"


@app.route('/test/estudio_mediodia')
def test_estudio_mediodia():
    enviar_estudio_mediodia()
    return "OK"


@app.route('/test/estudio_tarde')
def test_estudio_tarde():
    enviar_estudio_tarde()
    return "OK"


@app.route('/test/bcv')
def test_bcv():
    enviar_tasa_dolar()
    return "OK"


@app.route('/test/sorteo')
def test_sorteo():
    enviar_aviso_cierre_sorteo()
    return "OK"


@app.route('/test/cierre')
def test_cierre():
    enviar_mensaje_cierre()
    return "OK"


@app.route('/test/combinacion')
def test_combinacion():
    enviar_combinacion_diaria()
    return "OK"


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
        print(f"⚠️ Error enviando Telegram: {e}")


# ==========================================
# LIMPIAR RECOMENDACIONES
# ==========================================

def limpiar_recomendaciones_diarias():

    RECOMENDADOS_HOY.clear()
    HORAS_RECOMENDACIONES.clear()
    ACIERTOS_HOY.clear()
    CONTEO_ANIMALES_HOY.clear()

    print("🧹 Recomendaciones del día limpiadas.")


# ==========================================
# GUARDAR RECOMENDACIÓN
# ==========================================

def guardar_recomendacion(numero, texto):

    numero = str(numero).strip().zfill(2)

    RECOMENDADOS_HOY[numero] = texto
    HORAS_RECOMENDACIONES[numero] = datetime.now()

    print(
        f"📌 Recomendación guardada: "
        f"{numero} | {texto} | "
        f"{HORAS_RECOMENDACIONES[numero].strftime('%I:%M:%S %p')}"
    )


# ==========================================
# SALUDO MADRUGADA
# ==========================================

def enviar_saludo_madrugada():

    enviar_telegram(
        "🎯 *AGENCIA SOFÍA* 🎯\n\n"
        "🌟 *¡Activados desde temprano!* 🌟\n\n"
        "Que este día nos traiga mucha suerte y grandes jugadas. 🔥\n\n"
        "📲 WHATSAPP: 04163199157",
        True
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

            val = (
                f[idx] * 10 +
                f[idx + 1]
            ) % 37

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
            else (
                "0"
                if rnd.random() > 0.5
                else "00"
            )
        )

        if c_rand not in unique_candidates:
            unique_candidates.append(c_rand)

    d1 = "-".join(unique_candidates[:3])
    d2 = "-".join(unique_candidates[3:6])

    img_width = 1000
    img_height = 1120

    image = Image.new(
        "RGB",
        (img_width, img_height),
        color=(30, 10, 10)
    )

    draw = ImageDraw.Draw(image)

    dorado = (212, 175, 55)
    dorado_claro = (243, 229, 149)
    morado = (148, 0, 211)
    blanco = (255, 255, 255)
    panel = (20, 20, 20)

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

    draw.text(
        (img_width // 2, 45),
        "AGENCIA SOFÍA",
        fill=dorado,
        anchor="mm",
        font=font_title
    )

    draw.text(
        (img_width // 2, 90),
        "Trabajamos para tí",
        fill=blanco,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (img_width // 2, 145),
        "PIRÁMIDE DEL DÍA",
        fill=morado,
        anchor="mm",
        font=font_title
    )

    draw.rectangle(
        [
            img_width // 2 - 180,
            185,
            img_width // 2 + 180,
            240
        ],
        fill=panel,
        outline=dorado,
        width=2
    )

    draw.text(
        (img_width // 2, 212),
        f"📅 {fecha_str}",
        fill=dorado_claro,
        anchor="mm",
        font=font_data
    )

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
                start_x_row +
                (j * 52) +
                24
            )

            cy = (
                start_y +
                (i * row_height) +
                24
            )

            draw.ellipse(
                [
                    cx - circle_radius,
                    cy - circle_radius,
                    cx + circle_radius,
                    cy + circle_radius
                ],
                fill=panel,
                outline=dorado,
                width=3
            )

            draw.text(
                (cx, cy),
                str(num),
                fill=blanco,
                anchor="mm",
                font=font_pir
            )

    box_top = 760

    draw.rectangle(
        [
            150,
            box_top,
            img_width - 150,
            box_top + 150
        ],
        fill=panel,
        outline=dorado,
        width=2
    )

    draw.text(
        (img_width // 2, box_top + 28),
        "🔥 DATOS CLAVES PARA HOY:",
        fill=dorado,
        anchor="mm",
        font=font_sub
    )

    draw.text(
        (img_width // 2, box_top + 75),
        f"📌 {d1}",
        fill=blanco,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (img_width // 2, box_top + 115),
        f"📌 {d2}",
        fill=blanco,
        anchor="mm",
        font=font_data
    )

    draw.text(
        (img_width // 2, 955),
        "WHATSAPP: 04163199157",
        fill=dorado_claro,
        anchor="mm",
        font=font_sub
    )

    bio = BytesIO()

    bio.name = "piramide_sofia.png"

    image.save(
        bio,
        "PNG"
    )

    bio.seek(0)

    return bio


def enviar_piramide_diaria():

    try:

        foto_bio = generar_imagen_piramide()

        url = (
            f"https://api.telegram.org/"
            f"bot{TOKEN}/sendPhoto"
        )

        files = {
            "photo": foto_bio
        }

        data = {
            "chat_id": CANAL,
            "caption":
                "📢 *REPORTE TÁCTICO - LA PIRÁMIDE*\n\n"
                "📲 WHATSAPP: 04163199157\n"
                f"{ENLACE_CANAL}",
            "parse_mode": "Markdown"
        }

        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=15
        )

        if response.status_code != 200:
            print(
                f"⚠️ Error pirámide: "
                f"{response.text}"
            )

    except Exception as e:

        print(
            f"⚠️ Error pirámide: {e}"
        )


# ==========================================
# REGALOS
# ==========================================

def enviar_regalos_diarios():

    ahora = datetime.now()

    fecha_str = ahora.strftime("%d/%m/%Y")

    seed_val = (
        int(ahora.strftime("%Y%m%d"))
        + 99
    )

    rnd = random.Random(seed_val)

    regalos = rnd.sample(
        ANIMALES_POOL,
        3
    )

    for animal in regalos:

        numero = animal.split(" - ")[0]

        guardar_recomendacion(
            numero,
            "🎁 Regalo del Día"
        )

    mensaje = (
        "🎁 *LOS REGALOS DE LA AGENCIA SOFÍA* 🎁\n"
        f"📅 Fecha: {fecha_str}\n\n"
        "🔥 *Regalitos recomendados para hoy:*\n\n"
        f"🌟 *1er Regalo:* {regalos[0]}\n"
        f"🌟 *2do Regalo:* {regalos[1]}\n"
        f"🌟 *3er Regalo:* {regalos[2]}\n\n"
        "📲 WHATSAPP: 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 ¡Mucha suerte en tus jugadas!"
    )

    enviar_telegram(
        mensaje,
        True
    )


# ==========================================
# OBTENER ANIMALES SALIDOS
# ==========================================

def obtener_animales_salidos_actuales():

    salidos = set()

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        respuesta = requests.get(
            URL_LOTERIA,
            headers=headers,
            timeout=10
        )

        if respuesta.status_code == 200:

            soup = BeautifulSoup(
                respuesta.text,
                "html.parser"
            )

            texto_total = soup.get_text(
                " ",
                strip=True
            )

            matches = re.findall(
                r'(\d{1,2})\s*-\s*'
                r'([A-ZÁÉÍÓÚÑa-zñáéíóú]+)',
                texto_total
            )

            for m in matches:

                numero = int(m[0])

                salidos.add(
                    f"{numero:02d}"
                )

    except Exception as e:

        print(
            f"⚠️ Error obteniendo salidos: {e}"
        )

    return salidos


# ==========================================
# SELECCIONAR ANÁLISIS
# ==========================================

def seleccionar_analisis_dinamico(cantidad):

    salidos = obtener_animales_salidos_actuales()

    disponibles = []

    for animal in ANIMALES_POOL:

        numero = (
            animal
            .split(" - ")[0]
            .zfill(2)
        )

        if numero not in salidos:
            disponibles.append(animal)

    if len(disponibles) < cantidad:
        disponibles = ANIMALES_POOL

    seed_val = int(
        datetime.now().strftime(
            "%Y%m%d%H%M"
        )
    )

    rnd = random.Random(seed_val)

    return rnd.sample(
        disponibles,
        cantidad
    )


# ==========================================
# COMBINACIÓN
# ==========================================

def enviar_combinacion_diaria():

    seleccionados = seleccionar_analisis_dinamico(7)

    fijo1 = seleccionados[0]
    fijo2 = seleccionados[1]

    par1 = seleccionados[2]
    par2 = seleccionados[3]

    trip1 = seleccionados[4]
    trip2 = seleccionados[5]
    trip3 = seleccionados[6]

    for animal in seleccionados:

        numero = (
            animal
            .split(" - ")[0]
            .zfill(2)
        )

        guardar_recomendacion(
            numero,
            "🎯 Combinación Especial Sofía"
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
        "🎯 *COMBINACIÓN GANADORA - AGENCIA SOFÍA* 🎯\n\n"
        "🔥 *Datos exclusivos para tus jugadas:*\n\n"
        f"📌 *Fijos:* `{fijo1}` y `{fijo2}`\n"
        f"📌 *El Par:* `{par_str}`\n"
        f"📌 *La Tripleta:* `{trip_str}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 ¡Mucha suerte!"
    )

    enviar_telegram(
        mensaje,
        True
    )
    
# ==========================================
# ESTUDIO MEDIODÍA
# ==========================================

def enviar_estudio_mediodia():

    analisis = seleccionar_analisis_dinamico(2)

    for animal in analisis:

        numero = (
            animal
            .split(" - ")[0]
            .zfill(2)
        )

        guardar_recomendacion(
            numero,
            "☀️ Análisis Mediodía"
        )

    tripleta = seleccionar_analisis_dinamico(3)

    for animal in tripleta:

        numero = (
            animal
            .split(" - ")[0]
            .zfill(2)
        )

        guardar_recomendacion(
            numero,
            "🎯 Tripleta Mediodía"
        )

    t_str = (
        f"{tripleta[0].split(' - ')[0]} - "
        f"{tripleta[1].split(' - ')[0]} - "
        f"{tripleta[2].split(' - ')[0]}"
    )

    mensaje = (
        "🎯 *AGENCIA SOFÍA* 🎯\n\n"
        "☀️ *ANÁLISIS DEL MEDIODÍA* ☀️\n\n"
        "Estudiando los resultados de la mañana "
        "y las tendencias de la jornada:\n\n"
        f"🔥 *Animales calientes:* "
        f"`{analisis[0]}` y `{analisis[1]}`\n\n"
        f"🎯 *Tripleta recomendada:* `{t_str}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )

    enviar_telegram(
        mensaje,
        True
    )


# ==========================================
# SALUDO MATUTINO
# ==========================================
def enviar_saludo_matutino():
    enviar_telegram(
        "☕ ¡Buenos días a todos! ☀️\n\n"
        "Que hoy sea un día lleno de salud, prosperidad y muchos aciertos. 🙏✨\n\n"
        "Recuerden que la constancia trae la suerte. Revisa tus datos, elige tus números y haz tu jugada. 🎰\n\n"
        "📩 Taquilla abierta y atendiéndolos con el mejor servicio. ¡Estamos a un mensaje de distancia! 🚀💵",
        disable_web_preview=True
    )


# ==========================================
# TASA BCV
# ==========================================

def enviar_tasa_dolar():

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
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
                "html.parser"
            )

            dolar_div = soup.find(
                "div",
                id="dolar"
            )

            if (
                dolar_div and
                dolar_div.find("strong")
            ):

                precio_dolar = (
                    dolar_div
                    .find("strong")
                    .get_text(strip=True)
                )

        enviar_telegram(
            "💵 *TASA OFICIAL BCV* 💵\n\n"
            f"📈 Precio Oficial: Bs. {precio_dolar}\n\n"
            "📲 WHATSAPP: 04163199157",
            True
        )

    except Exception as e:

        print(
            f"⚠️ Error BCV: {e}"
        )


# ==========================================
# CIERRE
# ==========================================

def enviar_mensaje_cierre():
    enviar_telegram(
        "🌙 ¡BUENAS NOCHES A TODOS! ✨🎰\n\n"
        "Cerramos taquilla por hoy. Gracias por acompañarnos una jornada más.\n\n"
        "💡 Vayan pensando sus datos y números de la suerte para mañana, que venimos con todo a repartir premios. 💵🔥\n\n"
        "💤 ¡Que descansen y tengan dulces sueños! 👋",
        disable_web_preview=True
    )

# ==========================================
# AVISO CIERRE SORTEO
# ==========================================

def enviar_aviso_cierre_sorteo():

    enviar_telegram(
        "🛑 *¡ATENCIÓN!* 🛑\n\n"
        "El tiempo de jugadas ha terminado "
        "para este sorteo en *AGENCIA SOFÍA*.\n\n"
        "🤞 ¡Mucha suerte! 🎲🔥\n"
        "📲 WHATSAPP: 04163199157",
        True
    )


# ==========================================
# REGISTRO DE RESULTADOS
# ==========================================

def cargar_registros():

    if not os.path.exists(
        ARCH_REGISTRO
    ):
        return set()

    try:

        with open(
            ARCH_REGISTRO,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if (
            data.get("fecha") ==
            datetime.now().strftime("%d-%m-%Y")
        ):

            return set(
                data.get(
                    "enviados",
                    []
                )
            )

    except Exception as e:

        print(
            f"⚠️ Error leyendo registros: {e}"
        )

    return set()


def guardar_registros(enviados_set):

    data = {
        "fecha":
            datetime.now().strftime(
                "%d-%m-%Y"
            ),
        "enviados":
            list(enviados_set)
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
            f"⚠️ Error guardando registros: {e}"
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
            "User-Agent": "Mozilla/5.0"
        }

        respuesta = requests.get(
            URL_LOTERIA,
            headers=headers,
            timeout=15
        )

        if respuesta.status_code != 200:

            print(
                f"⚠️ WinBig respondió "
                f"{respuesta.status_code}"
            )

            return

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )

        tarjetas = soup.find_all(
            [
                "div",
                "article",
                "section"
            ],
            class_=re.compile(
                r"card|box|item|lotto|result",
                re.IGNORECASE
            )
        )

        nuevos_para_guardar = set(
            enviados_hoy
        )

        hubo_cambios = False

        for tarjeta in tarjetas:

            nombre_loteria = ""

            posibles_titulos = tarjeta.find_all(
                [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "span",
                    "div",
                    "strong",
                    "b"
                ],
                class_=re.compile(
                    r"title|header|name|lotto|text",
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
                        r"\d{1,2}:\d{2}",
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
                            r"\d{1,2}:\d{2}",
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

            for sigla, nombre_largo in TRADUCCION_LOTERIAS.items():

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
                    "div",
                    "li",
                    "span",
                    "tr"
                ],
                class_=re.compile(
                    r"item|slot|draw|row|col",
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
                    r"\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b",
                    texto_slot
                )

                if not match_h:
                    continue

                hora = match_h.group(1).upper()

                match_res = re.search(
                    r"(\d{1,2}\s-\s"
                    r"[A-ZÁÉÍÓÚÑa-zñáéíóú]+"
                    r"(?:\s+"
                    r"[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)",
                    texto_slot
                )

                if not match_res:
                    continue

                resultado = limpiar_texto(
                    match_res.group(1)
                ).upper()

                numero = (
                    resultado
                    .split("-")[0]
                    .strip()
                    .zfill(2)
                )

                # ==================================
                # CONTAR ANIMALES
                # ==================================

                CONTEO_ANIMALES_HOY[resultado] = (
                    CONTEO_ANIMALES_HOY.get(
                        resultado,
                        0
                    ) + 1
                )

                # ==================================
                # ACERTAR SOLO SI:
                #
                # 1. El animal fue recomendado
                # 2. Aún no se celebró
                # 3. El resultado ocurrió DESPUÉS
                #    de la recomendación
                # ==================================

                if (
                    numero in RECOMENDADOS_HOY
                    and numero not in ACIERTOS_HOY
                ):

                    hora_recomendacion = (
                        HORAS_RECOMENDACIONES.get(
                            numero
                        )
                    )

                    if hora_recomendacion:

                        try:

                            ahora = datetime.now()

                            hora_resultado_dt = (
                                datetime.strptime(
                                    hora,
                                    "%I:%M %p"
                                )
                            )

                            hora_resultado_dt = (
                                hora_resultado_dt.replace(
                                    year=ahora.year,
                                    month=ahora.month,
                                    day=ahora.day
                                )
                            )

                            # ==================================
                            # ESTA ES LA PROTECCIÓN IMPORTANTE
                            # ==================================

                            if (
                                hora_resultado_dt
                                > hora_recomendacion
                            ):

                                mensaje_acierto = (
                                    "🎉🎉 *¡ACERTAMOS!* 🎉🎉\n\n"
                                    f"✅ {RECOMENDADOS_HOY[numero]}\n\n"
                                    f"🎯 *{resultado}*\n"
                                    f"🎲 {nombre_loteria_ind}\n"
                                    f"🕒 {hora}\n\n"
                                    "🍀 *¡Felicidades a todos "
                                    "los que confiaron en "
                                    "Agencia Sofía!*"
                                )

                                enviar_telegram(
                                    mensaje_acierto,
                                    True
                                )

                                ACIERTOS_HOY.add(
                                    numero
                                )

                                print(
                                    f"🎉 ACierto válido: "
                                    f"{numero} | "
                                    f"Recomendado: "
                                    f"{hora_recomendacion.strftime('%I:%M %p')} | "
                                    f"Salió: {hora}"
                                )

                            else:

                                print(
                                    f"⏭️ NO se celebra "
                                    f"{numero}: "
                                    f"resultado anterior "
                                    f"a la recomendación."
                                )

                        except Exception as e:

                            print(
                                "⚠️ Error comprobando "
                                f"hora del acierto: {e}"
                            )

                # ==================================
                # ENVIAR RESULTADO NORMAL
                # ==================================

                id_resultado = (
                    f"{nombre_loteria_ind}_"
                    f"{hora}_"
                    f"{resultado}"
                )

                if es_primera_ejecucion:

                    nuevos_para_guardar.add(
                        id_resultado
                    )

                    continue

                if id_resultado not in enviados_hoy:

                    hora_actual_str = datetime.now().strftime(
                        "%I:%M %p"
                    )

                    mensaje = HEADER_SOFIA.format(
                        hora_actual=hora_actual_str,
                        nombre_loteria=nombre_loteria_ind,
                        hora=hora,
                        resultado=resultado
                    )

                    enviar_telegram(
                        mensaje,
                        True
                    )

                    nuevos_para_guardar.add(
                        id_resultado
                    )

                    hubo_cambios = True

                    print(
                        f"📤 Resultado enviado: "
                        f"{nombre_loteria_ind} | "
                        f"{hora} | "
                        f"{resultado}"
                    )

                    time.sleep(1.5)

        if es_primera_ejecucion:

            guardar_registros(
                nuevos_para_guardar
            )

            print(
                "📚 Primera ejecución: "
                "resultados actuales registrados "
                "sin reenviarlos."
            )

        elif hubo_cambios:

            guardar_registros(
                nuevos_para_guardar
            )

    except Exception as e:

        print(
            "❌ Error verificando resultados: "
            f"{e}"
        )


# ==========================================
# AVISO CIERRE
# ==========================================

ultimo_aviso_minuto = ""


def verificar_minuto():

    global ultimo_aviso_minuto

    ahora = datetime.now()

    hora_actual_minutos = (
        ahora.hour * 60 +
        ahora.minute
    )

    inicio = (
        7 * 60 +
        25
    )

    fin = (
        19 * 60 +
        55
    )

    if not (
        inicio
        <= hora_actual_minutos
        <= fin
    ):
        return

    minuto_actual = ahora.minute

    if minuto_actual in [25, 55]:

        clave_tiempo = ahora.strftime(
            "%H:%M"
        )

        if ultimo_aviso_minuto != clave_tiempo:

            enviar_aviso_cierre_sorteo()

            ultimo_aviso_minuto = (
                clave_tiempo
            )


# ==========================================
# LOOP PRINCIPAL
# ==========================================

def loop_bot():

    schedule.every().day.at(
        "00:01"
    ).do(
        limpiar_recomendaciones_diarias
    )

    schedule.every().day.at(
        "06:31"
    ).do(
        enviar_piramide_diaria
    )

    schedule.every().day.at(
        "06:45"
    ).do(
        enviar_regalos_diarios
    )

    schedule.every().day.at(
        "07:00"
    ).do(
        enviar_saludo_matutino
    )

    schedule.every().day.at(
        "08:15"
    ).do(
        enviar_estudio_8am
    )

    schedule.every().day.at(
        "09:40"
    ).do(
        enviar_combinacion_diaria
    )

    schedule.every().day.at(
        "12:15"
    ).do(
        enviar_estudio_mediodia
    )

    schedule.every().day.at(
        "13:30"
    ).do(
        enviar_combinacion_diaria
    )

    schedule.every().day.at(
        "16:15"
    ).do(
        enviar_estudio_tarde
    )

    schedule.every().day.at(
        "17:30"
    ).do(
        enviar_combinacion_diaria
    )

    schedule.every().day.at(
        "18:30"
    ).do(
        enviar_tasa_dolar
    )

    schedule.every().day.at(
        "20:00"
    ).do(
        enviar_mensaje_cierre
    )

    # ==================================
    # REVISAR WINBIG CADA MINUTO
    # ==================================

    schedule.every(
        1
    ).minutes.do(
        verificar_y_enviar_resultados_individuales
    )

    schedule.every(
        1
    ).minutes.do(
        verificar_minuto
    )

    print(
        "🟢 Scheduler de Agencia Sofía iniciado."
    )

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

        time.sleep(1)

        print(
            "🤖 Iniciando bot de Telegram..."
        )

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
            f"⚠️ Error iniciando polling: {e}"
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
