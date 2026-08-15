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
from datetime import datetime, timedelta
import random
import json
import telebot
import traceback
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Desactivar advertencias de certificados SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES Y ENLACES (Agencia Sofía)
# ==========================================
TOKEN = '8893057303:AAHi1D9GJEentjBJJB_6IdMNtSbQ2jxj7WQ'
CANAL = '@agenciasofiaoficial'
ENLACE_CANAL = 'https://t.me/agenciasofiaoficial'

bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

ARCH_REGISTRO = "resultados_sofia.json"

RECOMENDADOS_HOY = {} 
ACIERTOS_HOY = set()
CONTEO_ANIMALES_HOY = {}
ULTIMO_INDICE_MENSAJE = -1

MENSAJES_AUTOMATICOS = [
    f"🔥 *Agencia Sofía* 🔥\n¡La banca está encendida! Sella tus animalitos favoritos y asegura tu jugada de una vez.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🎯 ¡No te quedes sin cobrar hoy! La pizarra de *Agencia Sofía* te espera con los mejores animalitos.\n📲 WhatsApp: 04163199157",
    f"🍀 ¿Ya sabes con cuál animalito vas a reventar la banca? Escríbenos en *Agencia Sofía* y juega seguro.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"⚡️ ¡Pago rápido y atención al instante! Así trabajamos para ti en *Agencia Sofía*.\n📲 WhatsApp: 04163199157",
    f"🌟 La suerte favorece a los valientes. ¡Haz tu jugada ahora mismo con *Agencia Sofía*!\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🎲 ¿Cuál es tu corazonada para el próximo sorteo? Llévala a ganar con *Agencia Sofía*.\n📲 WhatsApp: 04163199157",
    f"🚀 ¡Arranca tu jugada ganadora! En *Agencia Sofía* te pagamos derecho y sin complicaciones.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"💡 Confía en tu instinto, elige tu animalito preferido y ven a ganar con *Agencia Sofía*.\n📲 WhatsApp: 04163199157",
    f"🏆 ¡El próximo tiquet ganador del día puede ser el tuyo! Juega con confianza en *Agencia Sofía*.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"✨ ¡Activa tu buena racha hoy! La taquilla de *Agencia Sofía* está abierta y lista para recibir tus jugadas.\n📲 WhatsApp: 04163199157"
]

PUBLICIDAD_CASHEA_9AM = (
    "💳 ¡**CASHEA ACTIVO** en **Agencia Sofía**! 🚀\n"
    "Arranca tu día con la mejor facilidad. Juega y asegura tus animalitos pagando después en 💰 **cómodas cuotas** y ✨ **sin inicial**.\n"
    f"📲 WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

PUBLICIDAD_CASHEA_12PM = (
    "✨ ¿Mitad de día y con ganas de probar tu suerte? 🎰\n"
    "Recuerda que tenemos **CASHEA ACTIVO** 💳: ✨ **sin inicial** y 💰 **cómodas cuotas** para tus jugadas.\n"
    f"📲 WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

PUBLICIDAD_CASHEA_3PM = (
    "⭐ ¡No pares tu buena racha de la tarde! 🚀\n"
    "Utiliza **CASHEA ACTIVO** en **Agencia Sofía** 💳 con 💰 **cómodas cuotas** y ✨ **sin inicial**.\n"
    f"📲 WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

PUBLICIDAD_CASHEA_430PM = (
    "🔥 ¡Última llamada de la tarde con **CASHEA ACTIVO**! 💳\n"
    "Juega ahora y paga después con ✨ **sin inicial** y 💰 **cómodas cuotas**.\n"
    f"📲 Escríbenos ya al WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

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

HEADER_Sofia = (
    "🎯 *AGENCIA SOFIA* 🎯\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🎲{nombre_loteria}🎲\n"
    "🕐 Hora: {hora}\n"
    "🐾 Resultado: *{resultado}*\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "📲 04163199157"
)

app = Flask('')

@app.route('/')
def home():
    return f"El bot de la <b>Agencia Sofía</b> está activo en el canal {CANAL}."

@app.route('/ping')
def ping():
    return "OK", 200

def limpiar_texto(texto):
    """Limpia espacios dobles y caracteres extraños de los textos extraídos."""
    return re.sub(r'\s+', ' ', texto).strip()

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
        print(f"⚠️ Error al enviar: {e}")

def enviar_mensaje_automatico():
    global ULTIMO_INDICE_MENSAJE
    if not MENSAJES_AUTOMATICOS:
        return
    indice = random.randint(0, len(MENSAJES_AUTOMATICOS) - 1)
    ULTIMO_INDICE_MENSAJE = indice
    enviar_telegram(MENSAJES_AUTOMATICOS[indice], disable_web_preview=True)

def enviar_publicidad_cashea_9am(): enviar_telegram(PUBLICIDAD_CASHEA_9AM)
def enviar_publicidad_cashea_12pm(): enviar_telegram(PUBLICIDAD_CASHEA_12PM)
def enviar_publicidad_cashea_3pm(): enviar_telegram(PUBLICIDAD_CASHEA_3PM)
def enviar_publicidad_cashea_430pm(): enviar_telegram(PUBLICIDAD_CASHEA_430PM)

def generar_imagen_piramide():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")
    digitos = [int(c) for c in fecha_str if c.isdigit()]
    filas = [digitos]
    while len(filas[-1]) > 1:
        actual = filas[-1]
        siguiente = [(actual[i] + actual[i+1]) % 10 for i in range(len(actual) - 1)]
        filas.append(siguiente)

    seed_val = int(ahora.strftime("%Y%m%d")) + 9999
    rnd = random.Random(seed_val)
    pool_nums = [f"{i:02d}" for i in range(37)] + ["00"]
    candidates = rnd.sample(pool_nums, 6)
    
    d1 = f"{candidates[0]}-{candidates[1]}-{candidates[2]}"
    d2 = f"{candidates[3]}-{candidates[4]}-{candidates[5]}"

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
        font_title = font_sub = font_pir = font_data = ImageFont.load_default()

    draw.text((img_width // 2, 45), "AGENCIA Sofía", fill=color_dorado, anchor="mm", font=font_title)
    draw.text((img_width // 2, 90), "Trabajamos para tí", fill=color_blanco, anchor="mm", font=font_sub)
    draw.text((img_width // 2, 145), "PIRÁMIDE DEL DÍA", fill=color_morado, anchor="mm", font=font_title)
    draw.rectangle([img_width // 2 - 180, 185, img_width // 2 + 180, 240], fill=color_panel, outline=color_dorado, width=2)
    draw.text((img_width // 2, 212), f"📅  {fecha_str}", fill=color_dorado_claro, anchor="mm", font=font_data)

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
        data = {'chat_id': CANAL, 'caption': f"📢 *REPORTE TÁCTICO - LA PIRÁMIDE*\n\nWHATSAPP: 04163199157\n{ENLACE_CANAL}", 'parse_mode': 'Markdown'}
        requests.post(url, data=data, files=files, timeout=15)
    except Exception as e:
        print(f"Error imagen pirámide: {e}")

def seleccionar_analisis_dinamico(cantidad):
    seed_val = int(datetime.now().strftime("%Y%m%d%H%M%S%f")) + 5555
    rnd = random.Random(seed_val)
    return rnd.sample(ANIMALES_POOL, cantidad)

def enviar_regalos_diarios():
    regalos = seleccionar_analisis_dinamico(3)
    hora_actual = datetime.now()
    for animal in regalos:
        num = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[num] = {"motivo": "🎁 Regalo del Día (Análisis)", "hora_emision": hora_actual}

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n🎁 *LOS REGALOS DEL DÍA* 🎁\n\n"
        f"🌟 *1er Regalo:* `{regalos[0]}`\n🌟 *2do Regalo:* `{regalos[1]}`\n🌟 *3er Regalo:* `{regalos[2]}`\n\n"
        "📲 WhatsApp: 04163199157\n" + ENLACE_CANAL
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_combinacion_diaria():
    seleccionados = seleccionar_analisis_dinamico(7)
    hora_actual = datetime.now()
    for animal in seleccionados:
        num = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[num] = {"motivo": "🔥 Combinación Ganadora", "hora_emision": hora_actual}

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n🔥 *COMBINACIÓN GANADORA* 🔥\n\n"
        f"📌 *Fijos:* `{seleccionados[0]}` y `{seleccionados[1]}`\n"
        f"📲 WhatsApp: 04163199157\n" + ENLACE_CANAL
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def registrar_estudio_analisis(motivo):
    seleccionados = seleccionar_analisis_dinamico(2)
    hora_actual = datetime.now()
    for animal in seleccionados:
        num = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[num] = {"motivo": motivo, "hora_emision": hora_actual}
    return seleccionados

def enviar_estudio_8am():
    sel = registrar_estudio_analisis("🔍 Análisis 8:15 AM")
    enviar_telegram(f"🎯 *AGENCIA Sofía* 🎯\n🔍 Análisis de las 8 AM listo: `{sel[0]}` y `{sel[1]}`\n📲 04163199157\n" + ENLACE_CANAL)

def enviar_estudio_mediodia():
    sel = registrar_estudio_analisis("☀️ Análisis Mediodía")
    enviar_telegram(f"🎯 *AGENCIA Sofía* 🎯\n☀️ Análisis del mediodía listo: `{sel[0]}` y `{sel[1]}`\n📲 04163199157\n" + ENLACE_CANAL)

def enviar_estudio_tarde():
    sel = registrar_estudio_analisis("🌇 Análisis Tarde")
    enviar_telegram(f"🎯 *AGENCIA Sofía* 🎯\n🌇 Análisis de la tarde listo: `{sel[0]}` y `{sel[1]}`\n📲 04163199157\n" + ENLACE_CANAL)

def enviar_saludo_matutino(): enviar_telegram("🎯 AGENCIA Sofía 🎯\n☀️ ¡Buenos días! Arrancamos la jornada con la mejor energía.\n📲 04163199157")

def enviar_tasa_dolar():
    enviar_telegram("💵 TASA OFICIAL BCV 💵\nVerifica la tasa oficial en: " + URL_BCV, disable_web_preview=True)

def enviar_mensaje_cierre():
    enviar_telegram("🌙 ¡BUENAS NOCHES! ✨🎰\nCerramos taquilla por hoy. ¡Gracias por preferirnos!\n📲 04163199157\n" + ENLACE_CANAL, disable_web_preview=True)

def enviar_aviso_cierre_sorteo():
    enviar_telegram("🔔 ¡JUGADAS CERRADAS para este sorteo en la **AGENCIA SOFÍA**! 🎰", disable_web_preview=True)

def cargar_registros():
    if os.path.exists(ARCH_REGISTRO):
        try:
            with open(ARCH_REGISTRO, "r") as f:
                data = json.load(f)
                if data.get("fecha") == datetime.now().strftime("%d-%m-%Y"):
                    return set(data.get("enviados", []))
        except:
            pass
    return set()

def guardar_registros(enviados_set):
    try:
        with open(ARCH_REGISTRO, "w") as f:
            json.dump({"fecha": datetime.now().strftime("%d-%m-%Y"), "enviados": list(enviados_set)}, f)
    except Exception as e:
        print(f"Error al guardar registros: {e}")

def parsear_hora_sorteo(hora_str):
    try:
        limpia = hora_str.strip().upper()
        dt_time = datetime.strptime(limpia, "%I:%M %p")
        ahora = datetime.now()
        return ahora.replace(hour=dt_time.hour, minute=dt_time.minute, second=0, microsecond=0)
    except Exception:
        return None

def verificar_y_enviar_resultados_individuales():
    enviados_hoy = cargar_registros()
    try:
        respuesta = requests.get(URL_LOTERIA, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if respuesta.status_code != 200: return
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))
        hubo_cambios = False
        nuevos_para_guardar = set(enviados_hoy)

        for tarjeta in tarjetas:
            nombre_loteria = "LOTTO ACTIVO"
            posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text:
                    if t_text not in ["WINBIG", "RESULTADOS", "RESULTADOS ANIMALITOS", "ANIMALITOS"]:
                        nombre_loteria = t_text
                        break

            slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
            if not slots_sorteo: slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                if "PENDIENTE" in texto_slot: continue
                match_h = re.search(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b', texto_slot)
                if not match_h: continue
                hora = match_h.group(1).upper()
                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+)', texto_slot)
                if not match_res: continue
                resultado = limpiar_texto(match_res.group(1)).upper()
                numero = resultado.split("-")[0].strip().zfill(2)

                id_res = f"{nombre_loteria}_{hora}_{resultado}"

                if numero in RECOMENDADOS_HOY and numero not in ACIERTOS_HOY:
                    info_rec = RECOMENDADOS_HOY[numero]
                    hora_emision = info_rec["hora_emision"]
                    dt_sorteo = parsear_hora_sorteo(hora)

                    if dt_sorteo and dt_sorteo > hora_emision:
                        mensaje_acierto = (
                            "🎉🎉 *¡ACERTAMOS!* 🎉🎉\n\n"
                            f"✅ {info_rec['motivo']}\n\n"
                            f"🎯 *{resultado}*\n"
                            f"🎲 {nombre_loteria}\n"
                            f"🕒 {hora}\n\n"
                            "🍀 *¡Felicidades a los que confiaron en Agencia Sofía!*"
                        )
                        enviar_telegram(mensaje_acierto)
                        ACIERTOS_HOY.add(numero)

                if id_res not in enviados_hoy:
                    enviar_telegram(HEADER_Sofia.format(nombre_loteria=nombre_loteria, hora=hora, resultado=resultado))
                    nuevos_para_guardar.add(id_res)
                    hubo_cambios = True
                    time.sleep(1.5)

        if hubo_cambios:
            guardar_registros(nuevos_para_guardar)
    except Exception as e:
        print(f"Error en resultados: {e}")

ultimo_aviso_minuto = ""
def verificar_minuto():
    global ultimo_aviso_minuto
    ahora = datetime.now()
    if ahora.minute in [25, 55]:
        clave = ahora.strftime("%H:%M")
        if ultimo_aviso_minuto != clave:
            enviar_aviso_cierre_sorteo()
            ultimo_aviso_minuto = clave

# ==========================================
# MANEJADORES DE COMANDOS DEL ROBOT (TELEBOT)
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(message):
    bot.reply_to(message, "¡Hola! El bot de **Agencia Sofía** está activo y operando correctamente. 🎰✨")

def loop_bot():
    schedule.every().day.at("06:31").do(enviar_piramide_diaria)
    schedule.every().day.at("06:45").do(enviar_regalos_diarios)
    schedule.every().day.at("07:00").do(enviar_saludo_matutino)
    schedule.every().day.at("08:15").do(enviar_estudio_8am)
    schedule.every().day.at("12:15").do(enviar_estudio_mediodia)
    schedule.every().day.at("16:15").do(enviar_estudio_tarde)
    schedule.every().day.at("15:30").do(enviar_tasa_dolar)
    schedule.every().day.at("20:00").do(enviar_mensaje_cierre)
    
    schedule.every().day.at("09:00").do(enviar_publicidad_cashea_9am)
    schedule.every().day.at("12:00").do(enviar_publicidad_cashea_12pm)
    schedule.every().day.at("15:00").do(enviar_publicidad_cashea_3pm)
    schedule.every().day.at("16:30").do(enviar_publicidad_cashea_430pm)

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
        print(f"Error polling: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

ARCH_REGISTRO = "resultados_enviados.json"

RECOMENDADOS_HOY = {}
ACIERTOS_HOY = set()
CONTEO_ANIMALES_HOY = {}
ULTIMO_INDICE_MENSAJE = -1

MENSAJES_AUTOMATICOS = [
    f"🔥 *Agencia Sofía* 🔥\n¡La banca está encendida! Sella tus animalitos favoritos y asegura tu jugada de una vez.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🎯 ¡No te quedes sin cobrar hoy! La pizarra de *Agencia Sofía* te espera con los mejores animalitos.\n📲 WhatsApp: 04163199157",
    f"🍀 ¿Ya sabes con cuál animalito vas a reventar la banca? Escríbenos en *Agencia Sofía* y juega seguro.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"⚡️ ¡Pago rápido y atención al instante! Así trabajamos para ti en *Agencia Sofía*.\n📲 WhatsApp: 04163199157",
    f"🌟 La suerte favorece a los valientes. ¡Haz tu jugada ahora mismo con *Agencia Sofía*!\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🎲 ¿Cuál es tu corazonada para el próximo sorteo? Llévala a ganar con *Agencia Sofía*.\n📲 WhatsApp: 04163199157",
    f"🚀 ¡Arranca tu jugada ganadora! En *Agencia Sofía* te pagamos derecho y sin complicaciones.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"💡 Confía en tu instinto, elige tu animalito preferido y ven a ganar con *Agencia Sofía*.\n📲 WhatsApp: 04163199157",
    f"🏆 ¡El próximo tiquet ganador del día puede ser el tuyo! Juega con confianza en *Agencia Sofía*.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"✨ ¡Activa tu buena racha hoy! La taquilla de *Agencia Sofía* está abierta y lista para recibir tus jugadas.\n📲 WhatsApp: 04163199157",
    f"🔥 ¡Atención apostadores! Los animalitos más calientes del día los consigues en *Agencia Sofía*.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🍀 Seguridad, rapidez y la mejor atención. ¡Todo lo que buscas está en *Agencia Sofía*!\n📲 WhatsApp: 04163199157",
    f"🎯 ¡No dejes que te lo cuenten! Ven, juega y cobra al instante con *Agencia Sofía*.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"⚡️ ¡El tiempo corre y la suerte también! Escríbenos al WhatsApp y sella tus animalitos con *Agencia Sofía*.\n📲 04163199157",
    f"🌟 ¡Sube la apuesta y prepárate para ganar! *Agencia Sofía* te acompaña en cada sorteo.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🎲 ¡La emoción de los animalitos se vive al máximo con *Agencia Sofía*! Haz tu jugada ya.\n📲 WhatsApp: 04163199157",
    f"🚀 ¿Listo para acertar? La banca de *Agencia Sofía* te paga tus aciertos al instante.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"💡 Recuerda que en *Agencia Sofía* estamos comprometidos con tu buena suerte todos los días.\n📲 WhatsApp: 04163199157",
    f"✨ ¡Que nada te detenga hoy! Sella tus animalitos favoritos de la mano de *Agencia Sofía*.\n📲 WhatsApp: 04163199157\n{ENLACE_CANAL}",
    f"🏆 ¡Juega, acierta y cobra seguro con *Agencia Sofía*! Escríbenos al WhatsApp.\n📲 04163199157"
]

# ==========================================
# PUBLICIDADES DE CASHEA FIJAS (4 HORARIOS)
# ==========================================
PUBLICIDAD_CASHEA_9AM = (
    "💳 ¡**CASHEA ACTIVO** en **Agencia Sofía**! 🚀\n"
    "Arranca tu día con la mejor facilidad. Ahora puedes jugar y asegurar tus animalitos favoritos "
    "pagando después en 💰 **cómodas cuotas** y ✨ **sin inicial**.\n"
    "🔒 100% seguro y confiable para todos nuestros apostadores.\n"
    f"📲 WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

PUBLICIDAD_CASHEA_12PM = (
    "✨ ¿Mitad de día y con ganas de probar tu suerte? 🎰\n"
    "Recuerda que tenemos **CASHEA ACTIVO** 💳: ✨ **sin inicial** y 💰 **cómodas cuotas** "
    "para que juegues ahora y pagues después de forma 🔒 **100% segura**.\n"
    f"📲 WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

PUBLICIDAD_CASHEA_3PM = (
    "⭐ ¡No pares tu buena racha de la tarde! 🚀\n"
    "Utiliza **CASHEA ACTIVO** en **Agencia Sofía** 💳. Disfruta de 💰 **cómodas cuotas** "
    "y ✨ **sin inicial** para tus jugadas. ¡Un sistema 🔒 **100% seguro** pensado para ti!\n"
    f"📲 WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

PUBLICIDAD_CASHEA_430PM = (
    "🔥 ¡Última llamada de la tarde con **CASHEA ACTIVO**! 💳\n"
    "No te quedes sin hacer tu jugada ganadora. Juega ahora y paga después con ✨ **sin inicial**, "
    "aprovechando las 💰 **cómodas cuotas** de forma 🔒 **100% segura**.\n"
    f"📲 Escríbenos ya al WhatsApp: 04163199157\n{ENLACE_CANAL}"
)

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
    "🎯 *AGENCIA SOFIA* 🎯\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🎲{nombre_loteria}🎲\n"
    "🕐 Hora: {hora}\n"
    "🐾 Resultado: *{resultado}*\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "📲 04163199157"
)

app = Flask('')

@app.route('/')
def home():
    return (
        f"¡El bot de resultados individuales de la <b>Agencia Sofía</b> está activo en el canal {CANAL}!<br><br>"
        "<b>Enlaces de prueba rápida (Test):</b><br>"
        "👉 <a href='/test/madrugada'>Probar Saludo de Madrugada</a><br>"
        "👉 <a href='/test/piramide'>Probar Pirámide Numérica (Imagen)</a><br>"
        "👉 <a href='/test/regalos'>Probar Regalos del Día (Análisis)</a><br>"
        "👉 <a href='/test/saludo'>Probar Saludo Matutino</a><br>"
        "👉 <a href='/test/estudio_manana'>Probar Análisis de las 8 AM</a><br>"
        "👉 <a href='/test/estudio_mediodia'>Probar Análisis del Mediodía</a><br>"
        "👉 <a href='/test/estudio_tarde'>Probar Análisis de la Tarde</a><br>"
        "👉 <a href='/test/bcv'>Probar Tasa Oficial BCV</a><br>"
        "👉 <a href='/test/sorteo'>Probar Cierre de Sorteo (Min 25/55)</a><br>"
        "👉 <a href='/test/cierre'>Probar Cierre de Jornada (8:00 PM)</a><br>"
        "👉 <a href='/test/combinacion'>Probar Combinación Diaria (Análisis)</a><br>"
        "👉 <a href='/test/publicidad_cashea'>Probar Publicidad Cashea</a>"
    )

@app.route('/ping')
def ping():
    return "OK", 200

@app.route('/test/madrugada')
def test_madrugada():
    enviar_saludo_madrugada()
    return "Prueba de Saludo de Madrugada ejecutada."

@app.route('/test/piramide')
def test_piramide():
    enviar_piramide_diaria()
    return "Prueba de Pirámide Numérica en Imagen ejecutada."

@app.route('/test/regalos')
def test_regalos():
    enviar_regalos_diarios()
    return "Prueba de Regalos del Día ejecutada."

@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "Prueba de Saludo Matutino ejecutada."

@app.route('/test/estudio_manana')
def test_estudio_manana():
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

@app.route('/test/publicidad_cashea')
def test_publicidad_cashea():
    enviar_publicidad_cashea_9am()
    return "Prueba de Publicidad Cashea ejecutada."

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

def enviar_mensaje_automatico():
    global ULTIMO_INDICE_MENSAJE
    if not MENSAJES_AUTOMATICOS:
        return
    
    indice = random.randint(0, len(MENSAJES_AUTOMATICOS) - 1)
    if len(MENSAJES_AUTOMATICOS) > 1:
        while indice == ULTIMO_INDICE_MENSAJE:
            indice = random.randint(0, len(MENSAJES_AUTOMATICOS) - 1)
            
    ULTIMO_INDICE_MENSAJE = indice
    enviar_telegram(MENSAJES_AUTOMATICOS[indice], disable_web_preview=True)

# ==========================================
# FUNCIONES DE ENVÍO PARA CADA HORARIO DE CASHEA
# ==========================================
def enviar_publicidad_cashea_9am():
    enviar_telegram(PUBLICIDAD_CASHEA_9AM, disable_web_preview=True)

def enviar_publicidad_cashea_12pm():
    enviar_telegram(PUBLICIDAD_CASHEA_12PM, disable_web_preview=True)

def enviar_publicidad_cashea_3pm():
    enviar_telegram(PUBLICIDAD_CASHEA_3PM, disable_web_preview=True)

def enviar_publicidad_cashea_430pm():
    enviar_telegram(PUBLICIDAD_CASHEA_430PM, disable_web_preview=True)

def enviar_saludo_madrugada():
    enviar_telegram(
        "☕ ¡Buenos días a todos! ☀️\n\n"
        "Que hoy sea un día lleno de salud, prosperidad y muchos aciertos. 🙏✨\n\n"
        "Recuerden que la constancia trae la suerte. Revisa tus datos, elige tus números y haz tu jugada. 🎰\n\n"
        "📩 Taquilla abierta y atendiéndolos con el mejor servicio. ¡Estamos a un mensaje de distancia! 🚀💵\n"
        "📲 WhatsApp: 04163199157\n"
        f"{ENLACE_CANAL}",
        disable_web_preview=True
    )

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

    draw.text((img_width // 2, 45), "AGENCIA Sofía", fill=color_dorado, anchor="mm", font=font_title)
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
        requests.post(url, data=data, files=files, timeout=15)
    except Exception as e:
        print(f"Error generando/enviando imagen pirámide: {e}")

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

    seed_val = int(datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(0, 999)))
    rnd = random.Random(seed_val)
    return rnd.sample(disponibles, cantidad)

def enviar_regalos_diarios():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")
    regalos_seleccionados = seleccionar_analisis_dinamico(3)
     
    for animal in regalos_seleccionados:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = "🎁 Regalo del Día (Análisis)"

    mensaje_regalos = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎁 *LOS REGALOS DEL DÍA* 🎁\n"
        f"📅 Fecha: {fecha_str}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 *¡Estudio del tablero en vivo, los fijos recomendados para reventar la banca hoy:* 🔥\n\n"
        f"🌟 *1er Regalo:* `{regalos_seleccionados[0]}`\n"
        f"🌟 *2do Regalo:* `{regalos_seleccionados[1]}`\n"
        f"🌟 *3er Regalo:* `{regalos_seleccionados[2]}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📲 WhatsApp: 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 *¡Mucha suerte en tus jugadas!* ✨"
    )
    enviar_telegram(mensaje_regalos, disable_web_preview=True)

def enviar_combinacion_diaria():
    seleccionados = seleccionar_analisis_dinamico(7)

    fijo1, fijo2, par1, par2, trip1, trip2, trip3 = seleccionados[:7]

    for animal in seleccionados:
        num = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[num] = "🎯 Combinación Especial por Análisis"

    par_str = f"{par1.split(' - ')[0]} - {par2.split(' - ')[0]}"
    trip_str = f"{trip1.split(' - ')[0]} - {trip2.split(' - ')[0]} - {trip3.split(' - ')[0]}"

    mensaje = (
        "🎯 *AGENCIA SOFIA* 🎯\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔥 *COMBINACIÓN GANADORA* 🔥\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📊 *Datos calculados mediante análisis del tablero:*\n\n"
        f"📌 *Fijos del Día:* `{fijo1}` y `{fijo2}`\n"
        f"📌 *El Par:* `{par_str}`\n"
        f"📌 *La Tripleta:* `{trip_str}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📲 WhatsApp: 04163199157\n"
        f"{ENLACE_CANAL}\n\n"
        "🍀 *¡A cobrar se ha dicho!* ✨"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_estudio_8am():
    analisis = seleccionar_analisis_dinamico(2)
    for animal in analisis:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = "🔍 Análisis 8:15 AM"

    mensaje = (
        "🎯 *AGENCIA Sofía* 🎯\n"
        "🔍 *ANÁLISIS TRAS EL SORTEO DE LAS 8:00 AM* 🔍\n\n"
        "¡Ya salieron los primeros animalitos! Evaluando la apertura de la pizarra y descartando lo ya jugado, la casa trae las proyecciones analíticas para los siguientes sorteos:\n\n"
        f"🔥 *Regalitos recomendados:* `{analisis[0]}` y `{analisis[1]}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_estudio_mediodia():
    analisis = seleccionar_analisis_dinamico(2)
    for animal in analisis:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = "☀️ Análisis Mediodía"

    tripleta = seleccionar_analisis_dinamico(3)
    for animal in tripleta:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = "🎯 Tripleta Mediodía"

    t_str = f"{tripleta[0].split(' - ')[0]} - {tripleta[1].split(' - ')[0]} - {tripleta[2].split(' - ')[0]}"
     
    mensaje = (
        "🎯 *AGENCIA Sofía* 🎯\n"
        "☀️ *ANÁLISIS DEL MEDIODÍA* ☀️\n\n"
        "*¡Mitad de jornada! Estudiando los resultados que nos dejó la mañana y analizando tendencias en vivo, el tablero apunta hacia las siguientes proyecciones analíticas:*\n\n"
        f"🔥 *Animales calientes:* `{analisis[0]}` y `{analisis[1]}`\n"
        f"🎯 *Tripleta recomendada:* `{t_str}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_estudio_tarde():
    analisis = seleccionar_analisis_dinamico(2)
    for animal in analisis:
        numero = animal.split(" - ")[0].zfill(2)
        RECOMENDADOS_HOY[numero] = "🌇 Análisis Tarde"

    mensaje = (
        "🎯 *AGENCIA Sofía* 🎯\n"
        "🌇 *ANÁLISIS Y CIERRE DE LA TARDE* 🌇\n\n"
        "¡A pocas horas de terminar la jornada! Evaluando el comportamiento de los últimos sorteos y filtrando por análisis los animales con mayor probabilidad para asegurar el cierre:\n\n"
        f"⚡️ *Imparables de la Tarde / Cierre:* `{analisis[0]}` y `{analisis[1]}`\n\n"
        "📲 *WHATSAPP:* 04163199157\n"
        f"{ENLACE_CANAL}"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_saludo_matutino():
    enviar_telegram(
        "🎯 AGENCIA Sofía 🎯\n\n"
        "☀️ ¡Buenos días! Arrancamos la jornada con la mejor actitud y la mejor energía para ganar.\n\n"
        "📲 WHATSAPP: 04163199157\n"
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
            f"Verifica la tasa oficial en: {URL_BCV}",
            disable_web_preview=True
        )
    except Exception as e:
        print(f"Error BCV: {e}")

def enviar_mensaje_cierre():
    enviar_telegram(
        "🌙 ¡BUENAS NOCHES A TODOS! ✨🎰\n\n"
        "Cerramos taquilla por hoy. Gracias por acompañarnos una jornada más.\n\n"
        "💡 Vayan pensando sus datos y números de la suerte para mañana, que venimos con todo a repartir premios. 💵🔥\n\n"
        "💤 ¡Que descansen y tengan dulces sueños! 👋\n\n"
        "📲 WhatsApp: 04163199157\n"
        f"{ENLACE_CANAL}",
        disable_web_preview=True
    )

def enviar_aviso_cierre_sorteo():
    enviar_telegram(
        "🔔 ¡JUGADAS CERRADAS! 🎰\n\n"
        "⏰ Se cerró el tiempo de jugadas para este sorteo en la **AGENCIA F&D**.\n\n"
        "🍀 ¡Mucha suerte a todos nuestros jugadores! 💜",
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
                hora = match_h.group(1).upper()

                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado = limpiar_texto(match_res.group(1)).upper()
                CONTEO_ANIMALES_HOY[resultado] = CONTEO_ANIMALES_HOY.get(resultado, 0) + 1
                numero = resultado.split("-")[0].strip().zfill(2)

                if numero in RECOMENDADOS_HOY and numero not in ACIERTOS_HOY:
                    mensaje = (
                        "🎉🎉 *¡ACERTAMOS!* 🎉🎉\n\n"
                        f"✅ {RECOMENDADOS_HOY[numero]}\n\n"
                        f"🎯 *{resultado}*\n"
                        f"🎲 {nombre_loteria_ind}\n"
                        f"🕒 {hora}\n\n"
                        "🍀 *¡Felicidades a todos los que confiaron en Agencia Sofía!*"
                    )
                    enviar_telegram(mensaje)
                    ACIERTOS_HOY.add(numero)

                id_resultado = f"{nombre_loteria_ind}_{hora}_{resultado}"

                if es_primera_ejecucion:
                    nuevos_para_guardar.add(id_resultado)
                    continue

                if id_resultado not in enviados_hoy:
                    mensaje = HEADER_Sofia.format(
                        nombre_loteria=nombre_loteria_ind,
                        hora=hora,
                        resultado=resultado
                    )
                    enviar_telegram(mensaje)
                    nuevos_para_guardar.add(id_resultado)
                    hubo_cambios = True
                    time.sleep(1.5)

        if es_primera_ejecucion or hubo_cambios:
            guardar_registros(nuevos_para_guardar)

    except Exception as e:
        print(f"Error al verificar resultados individuales: {e}")

ultimo_aviso_minuto = ""

def verificar_minuto():
    global ultimo_aviso_minuto
    ahora = datetime.now()
    hora_actual_minutos = ahora.hour * 60 + ahora.minute
    if not (7 * 60 + 25 <= hora_actual_minutos <= 19 * 60 + 55):
        return

    if ahora.minute in [25, 55]:
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
            bot.reply_to(message, "⚠️ No se pudo conectar con la página de resultados.")
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
            "🎯 *AGENCIA Sofía* 🎯\n"
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
    schedule.every().day.at("06:31").do(enviar_piramide_diaria)
    schedule.every().day.at("06:45").do(enviar_regalos_diarios)
    schedule.every().day.at("07:00").do(enviar_saludo_matutino)
     
    schedule.every().day.at("08:15").do(enviar_estudio_8am)
    schedule.every().day.at("12:15").do(enviar_estudio_mediodia)
    schedule.every().day.at("16:15").do(enviar_estudio_tarde)
    
    schedule.every().day.at("15:30").do(enviar_tasa_dolar)
    schedule.every().day.at("20:00").do(enviar_mensaje_cierre)
    
    schedule.every().day.at("09:30").do(enviar_mensaje_automatico)
    schedule.every().day.at("10:30").do(enviar_mensaje_automatico)
    schedule.every().day.at("11:30").do(enviar_mensaje_automatico)
    schedule.every().day.at("13:30").do(enviar_mensaje_automatico)
    schedule.every().day.at("14:30").do(enviar_mensaje_automatico)
    schedule.every().day.at("15:40").do(enviar_mensaje_automatico)
    schedule.every().day.at("17:30").do(enviar_mensaje_automatico)
    schedule.every().day.at("19:30").do(enviar_mensaje_automatico)
    
    schedule.every().day.at("09:40").do(enviar_combinacion_diaria)
    schedule.every().day.at("13:30").do(enviar_combinacion_diaria)
    schedule.every().day.at("17:30").do(enviar_combinacion_diaria)

    # ==========================================
    # PROGRAMACIÓN DE CASHEA (4 PUBLICIDADES EXACTAS)
    # ==========================================
    schedule.every().day.at("09:00").do(enviar_publicidad_cashea_9am)
    schedule.every().day.at("12:00").do(enviar_publicidad_cashea_12pm)
    schedule.every().day.at("15:00").do(enviar_publicidad_cashea_3pm)
    schedule.every().day.at("16:30").do(enviar_publicidad_cashea_430pm)

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
