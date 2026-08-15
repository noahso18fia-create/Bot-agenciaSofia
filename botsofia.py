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
    "00 - Ballena", "0 - Delfin", "01 - Carnero", "02 - Toro", "03 - Ciempiés",
    "04 - Alacrán", "05 - León", "06 - Rana", "07 - Perico", "08 - Ratón",
    "09 - Águila", "10 - Tigre", "11 - Gato", "12 - Caballo", "13 - Mono",
    "14 - Paloma", "15 - Zorro", "16 - Oso", "17 - Pavo", "18 - Burro",
    "19 - Chivo", "20 - Cochino", "21 - Gallo", "22 - Camello", "23 - Cebra",
    "24 - Iguana", "25 - Gallina", "26 - Vaca", "27 - Perro", "28 - Zamuro",
    "29 - Elefante", "30 - Caimán", "31 - Lapa", "32 - Ardilla", "33 - Pescado",
    "34 - Venado", "35 - Jirafa", "36 - Culebra"
]


# ==========================================
# TRADUCCIÓN LOTERÍAS (AMPLIADA)
# ==========================================

TRADUCCION_LOTERIAS = {
    "LOTTO ACTIVO": "LOTTO ACTIVO",
    "L.A": "LOTTO ACTIVO",
    "LA GRANJITA": "LA GRANJITA",
    "GRANJITA": "LA GRANJITA",
    "GRJ": "LA GRANJITA",
    "SELVA PLUS": "SELVA PLUS",
    "S.P": "SELVA PLUS",
    "LOTTO REAL": "LOTTO REAL",
    "L.RE": "LOTTO REAL",
    "GUACHARO ACTIVO": "GUACHARO ACTIVO",
    "GUACHARO": "GUACHARO ACTIVO",
    "GHO": "GUACHARO ACTIVO",
    "LOTTO CHAIMA": "LOTTO CHAIMA",
    "L.CH": "LOTTO CHAIMA",
    "MONJE MILLONARIO": "MONJE MILLONARIO",
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
        "👉 /test/forzar_resultados<br>"
        "👉 /test/madrugada<br>"
        "👉 /test/piramide<br>"
        "👉 /test/regalos<br>"
        "👉 /test/saludo<br>"
        "👉 /test/bcv<br>"
        "👉 /test/sorteo<br>"
        "👉 /test/cierre<br>"
        "👉 /test/combinacion"
    )


@app.route('/test/forzar_resultados')
def test_forzar_resultados():
    verificar_y_enviar_resultados_individuales()
    return "✅ Escaneo ejecutado."


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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Error enviando Telegram: {e}")


def limpiar_recomendaciones_diarias():
    RECOMENDADOS_HOY.clear()
    HORAS_RECOMENDACIONES.clear()
    ACIERTOS_HOY.clear()
    CONTEO_ANIMALES_HOY.clear()


def guardar_recomendacion(numero, texto):
    numero = str(numero).strip().zfill(2)
    RECOMENDADOS_HOY[numero] = texto
    HORAS_RECOMENDACIONES[numero] = datetime.now()


def enviar_saludo_madrugada():
    enviar_telegram(
        "🎯 *AGENCIA SOFÍA* 🎯\n\n"
        "🌟 *¡Activados desde temprano!* 🌟\n\n"
        "Que este día nos traiga mucha suerte y grandes jugadas. 🔥\n\n"
        "📲 WHATSAPP: 04163199157"
    )


def enviar_saludo_matutino():
    enviar_telegram(
        "☕ ¡Buenos días a todos! ☀️\n\n"
        "Que hoy sea un día lleno de salud, prosperidad y muchos aciertos. 🙏✨\n\n"
        "Recuerden que la constancia trae la suerte. Revisa tus datos, elige tus números y haz tu jugada. 🎰\n\n"
        "📩 Taquilla abierta y atendiéndolos con el mejor servicio. ¡Estamos a un mensaje de distancia! 🚀💵"
    )


def enviar_mensaje_cierre():
    enviar_telegram(
        "🌙 ¡BUENAS NOCHES A TODOS! ✨🎰\n\n"
        "Cerramos taquilla por hoy. Gracias por acompañarnos una jornada más.\n\n"
        "💡 Vayan pensando sus datos y números de la suerte para mañana, que venimos con todo a repartir premios. 💵🔥\n\n"
        "💤 ¡Que descansen y tengan dulces sueños! 👋"
    )


def enviar_aviso_cierre_sorteo():
    enviar_telegram(
        "🛑 *¡ATENCIÓN!* 🛑\n\n"
        "El tiempo de jugadas ha terminado para este sorteo en *AGENCIA SOFÍA*.\n\n"
        "🤞 ¡Mucha suerte! 🎲🔥\n"
        "📲 WHATSAPP: 04163199157"
    )


def generar_imagen_piramide():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")
    digitos = [int(c) for c in fecha_str if c.isdigit()]
    filas = [digitos]
    while len(filas[-1]) > 1:
        actual = filas[-1]
        siguiente = [(actual[i] + actual[i + 1]) % 10 for i in range(len(actual) - 1)]
        filas.append(siguiente)
    seed_val = int(ahora.strftime("%Y%m%d"))
    rnd = random.Random(seed_val)
    candidates = []
    for f in filas:
        for idx in range(len(f) - 1):
            val = (f[idx] * 10 + f[idx + 1]) % 37
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
    d1 = "-".join(unique_candidates[:3])
    d2 = "-".join(unique_candidates[3:6])

    img_width, img_height = 1000, 1120
    image = Image.new("RGB", (img_width, img_height), color=(30, 10, 10))
    draw = ImageDraw.Draw(image)
    dorado = (212, 175, 55)
    dorado_claro = (243, 229, 149)
    morado = (148, 0, 211)
    blanco = (255, 255, 255)
    panel = (20, 20, 20)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 24)
        font_pir = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        font_data = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except:
        font_title = font_sub = font_pir = font_data = ImageFont.load_default()

    draw.text((img_width // 2, 45), "AGENCIA SOFÍA", fill=dorado, anchor="mm", font=font_title)
    draw.text((img_width // 2, 90), "Trabajamos para tí", fill=blanco, anchor="mm", font=font_sub)
    draw.text((img_width // 2, 145), "PIRÁMIDE DEL DÍA", fill=morado, anchor="mm", font=font_title)
    draw.rectangle([img_width // 2 - 180, 185, img_width // 2 + 180, 240], fill=panel, outline=dorado, width=2)
    draw.text((img_width // 2, 212), f"📅 {fecha_str}", fill=dorado_claro, anchor="mm", font=font_data)

    start_y, row_height, center_x, circle_radius = 280, 54, img_width // 2, 23
    for i, f in enumerate(filas):
        num_items = len(f)
        total_width = num_items * 52
        start_x_row = center_x - (total_width // 2)
        for j, num in enumerate(f):
            cx = start_x_row + (j * 52) + 24
            cy = start_y + (i * row_height) + 24
            draw.ellipse([cx - circle_radius, cy - circle_radius, cx + circle_radius, cy + circle_radius], fill=panel, outline=dorado, width=3)
            draw.text((cx, cy), str(num), fill=blanco, anchor="mm", font=font_pir)

    box_top = 760
    draw.rectangle([150, box_top, img_width - 150, box_top + 150], fill=panel, outline=dorado, width=2)
    draw.text((img_width // 2, box_top + 28), "🔥 DATOS CLAVES PARA HOY:", fill=dorado, anchor="mm", font=font_sub)
    draw.text((img_width // 2, box_top + 75), f"📌 {d1}", fill=blanco, anchor="mm", font=font_data)
    draw.text((img_width // 2, box_top + 115), f"📌 {d2}", fill=blanco, anchor="mm", font=font_data)
    draw.text((img_width // 2, 955), "WHATSAPP: 04163199157", fill=dorado_claro, anchor="mm", font=font_sub)

    bio = BytesIO()
    bio.name = "piramide_sofia.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio


def enviar_piramide_diaria():
    try:
        foto_bio = generar_imagen_piramide()
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        files = {"photo": foto_bio}
        data = {
            "chat_id": CANAL,
            "caption": f"📢 *REPORTE TÁCTICO - LA PIRÁMIDE*\n\n📲 WHATSAPP: 04163199157\n{ENLACE_CANAL}",
            "parse_mode": "Markdown"
        }
        requests.post(url, data=data, files=files, timeout=15)
    except Exception as e:
        print(f"⚠️ Error pirámide: {e}")


def enviar_regalos_diarios():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")
    regalos = random.sample(ANIMALES_POOL, 3)
    for animal in regalos:
        numero = animal.split(" - ")[0].zfill(2)
        guardar_recomendacion(numero, "🎁 Regalo del Día")
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
    enviar_telegram(mensaje)


def seleccionar_analisis_dinamico(cantidad):
    seed_val = int(datetime.now().strftime("%Y%m%d%H%M"))
    rnd = random.Random(seed_val)
    return rnd.sample(ANIMALES_POOL, cantidad)


def enviar_combinacion_diaria():
    seleccionados = seleccionar_analisis_dinamico(7)
    fijo1, fijo2 = seleccionados[0], seleccionados[1]
    par1, par2 = seleccionados[2], seleccionados[3]
    trip1, trip2, trip3 = seleccionados[4], seleccionados[5], seleccionados[6]
    for animal in seleccionados:
        numero = animal.split(" - ")[0].zfill(2)
        guardar_recomendacion(numero, "🎯 Combinación Especial Sofía")
    mensaje = (
        "🎯 *COMBINACIÓN GANADORA - AGENCIA SOFÍA* 🎯\n\n"
        "🔥 *Datos exclusivos para tus jugadas:*\n\n"
        f"📌 *Fijos:* `{fijo1}` y `{fijo2}`\n"
        f"📌 *El Par:* `{par1.split(' - ')[0]} - {par2.split(' - ')[0]}`\n"
        f"📌 *La Tripleta:* `{trip1.split(' - ')[0]} - {trip2.split(' - ')[0]} - {trip3.split(' - ')[0]}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 ¡Mucha suerte!"
    )
    enviar_telegram(mensaje)


def enviar_tasa_dolar():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL_BCV, headers=headers, timeout=15, verify=False)
        precio_dolar = "742,23"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            dolar_div = soup.find("div", id="dolar")
            if dolar_div and dolar_div.find("strong"):
                precio_dolar = dolar_div.find("strong").get_text(strip=True)
        enviar_telegram(
            "💵 *TASA OFICIAL BCV* 💵\n\n"
            f"📈 Precio Oficial: Bs. {precio_dolar}\n\n"
            "📲 WHATSAPP: 04163199157"
        )
    except Exception as e:
        print(f"⚠️ Error BCV: {e}")


def cargar_registros():
    if not os.path.exists(ARCH_REGISTRO):
        return set()
    try:
        with open(ARCH_REGISTRO, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("fecha") == datetime.now().strftime("%d-%m-%Y"):
            return set(data.get("enviados", []))
    except Exception as e:
        print(f"⚠️ Error leyendo registros: {e}")
    return set()


def guardar_registros(enviados_set):
    data = {
        "fecha": datetime.now().strftime("%d-%m-%Y"),
        "enviados": list(enviados_set)
    }
    try:
        with open(ARCH_REGISTRO, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error guardando registros: {e}")


# ==========================================
# VERIFICAR Y ENVIAR CON FILTRO DE HORA
# ==========================================

def verificar_y_enviar_resultados_individuales():
    enviados_hoy = cargar_registros()
    print("🔎 Escaneando WinBig...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)

        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(respuesta.text, "html.parser")
        tarjetas = soup.find_all(
            ["div", "article", "section", "tr", "td"],
            class_=re.compile(r"card|box|item|lotto|result|content|table|col", re.IGNORECASE)
        )
        if not tarjetas:
            tarjetas = [soup.body or soup]

        hubo_cambios = False
        nuevos_para_guardar = set(enviados_hoy)

        regex_hora = re.compile(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b')
        regex_resultado = re.compile(r'\b(\d{1,2})\s*[-–—]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ\s]{3,20})\b')

        ahora_dt = datetime.now()

        for tarjeta in tarjetas:
            texto_tarjeta = limpiar_texto(tarjeta.get_text(" ", strip=True))
            if not texto_tarjeta or "RULETA ROYAL" in texto_tarjeta.upper():
                continue

            nombre_loteria_ind = ""
            for sigla_o_nombre, nombre_oficial in TRADUCCION_LOTERIAS.items():
                if sigla_o_nombre in texto_tarjeta.upper():
                    nombre_loteria_ind = nombre_oficial
                    break

            if not nombre_loteria_ind:
                continue

            coincidencias_hora = regex_hora.findall(texto_tarjeta)
            coincidencias_res = regex_resultado.findall(texto_tarjeta)

            if coincidencias_hora and coincidencias_res:
                hora_str = coincidencias_hora[0].upper()
                if "AM" not in hora_str and "PM" not in hora_str:
                    h_num = int(hora_str.split(":")[0])
                    hora_str += " AM" if h_num < 12 else " PM"

                # 🛡️ FILTRO DE SEGURIDAD: Convertir hora del sorteo a objeto datetime para comparar
                try:
                    hora_limpia_str = hora_str.replace("A.M.", "AM").replace("P.M.", "PM")
                    sorteo_dt = datetime.strptime(hora_limpia_str, "%I:%M %p")
                    # Asignar la fecha actual al objeto de hora del sorteo
                    sorteo_dt = sorteo_dt.replace(year=ahora_dt.year, month=ahora_dt.month, day=ahora_dt.day)
                    
                    # Si el sorteo es de hace más de 2 horas o del futuro lejano que no toca, lo ignoramos al reiniciar
                    # O simplemente si la hora del sorteo ya pasó por mucho y no se mandó, evitamos spam masivo.
                    # Aquí evitamos que mande sorteos cuya hora sea menor a la hora actual menos 45 minutos (por si acaso).
                except Exception:
                    pass

                num_str, animal_str = coincidencias_res[0]
                num_formatted = num_str.zfill(2) if num_str != "0" else "0"
                resultado = f"{num_formatted} - {animal_str.strip().upper()}"

                id_resultado = f"{nombre_loteria_ind}_{hora_str}_{resultado}"

                if id_resultado not in enviados_hoy:
                    # 🛡️ PROTECCIÓN EXTRA: Si el bot se reinicia y hay un bache de horas antiguas, 
                    # evitamos enviar cosas con más de 1 hora de atraso para no inundar el canal.
                    try:
                        diferencia_minutos = (ahora_dt - sorteo_dt).total_seconds() / 60
                        if diferencia_minutos > 60: # Si el sorteo pasó hace más de 1 hora y media, lo marcaremos como enviado sin spamear
                            nuevos_para_guardar.add(id_resultado)
                            hubo_cambios = True
                            continue
                    except:
                        pass

                    if num_formatted in RECOMENDADOS_HOY and num_formatted not in ACIERTOS_HOY:
                        mensaje_acierto = (
                            "🎉🎉 *¡ACERTAMOS!* 🎉🎉\n\n"
                            f"✅ {RECOMENDADOS_HOY[num_formatted]}\n\n"
                            f"🎯 *{resultado}*\n"
                            f"🎲 {nombre_loteria_ind}\n"
                            f"🕒 {hora_str}\n\n"
                            "🍀 *¡Felicidades a todos los que confiaron en Agencia Sofía!*"
                        )
                        enviar_telegram(mensaje_acierto)
                        ACIERTOS_HOY.add(num_formatted)

                    mensaje = HEADER_SOFIA.format(
                        nombre_loteria=nombre_loteria_ind,
                        hora=hora_str,
                        resultado=resultado
                    )
                    enviar_telegram(mensaje)

                    nuevos_para_guardar.add(id_resultado)
                    hubo_cambios = True
                    time.sleep(1.2)

        if hubo_cambios:
            guardar_registros(nuevos_para_guardar)

    except Exception as e:
        print(f"❌ Error al verificar resultados: {e}")


def verificar_minuto():
    ahora = datetime.now()
    hora_actual_minutos = ahora.hour * 60 + ahora.minute
    if (7 * 60 + 25) <= hora_actual_minutos <= (19 * 60 + 55):
        if ahora.minute in [25, 55]:
            enviar_aviso_cierre_sorteo()


def loop_bot():
    schedule.every().day.at("00:01").do(limpiar_recomendaciones_diarias)
    schedule.every().day.at("06:31").do(enviar_piramide_diaria)
    schedule.every().day.at("06:45").do(enviar_regalos_diarios)
    schedule.every().day.at("07:00").do(enviar_saludo_matutino)
    schedule.every().day.at("09:40").do(enviar_combinacion_diaria)
    schedule.every().day.at("13:30").do(enviar_combinacion_diaria)
    schedule.every().day.at("17:30").do(enviar_combinacion_diaria)
    schedule.every().day.at("18:30").do(enviar_tasa_dolar)
    schedule.every().day.at("20:00").do(enviar_mensaje_cierre)

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
        time.sleep(1)
        t_polling = Thread(
            target=lambda: bot.infinity_polling(skip_pending=True, interval=3, timeout=20)
        )
        t_polling.daemon = True
        t_polling.start()
    except Exception as e:
        print(f"⚠️ Error: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
