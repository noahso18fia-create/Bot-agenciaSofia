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

# Diccionario para almacenar recomendaciones con su hora exacta de emisión (para evitar falsos aciertos)
RECOMENDADOS_HOY = {} # Estructura: { "numero": {"motivo": "...", "hora_emision": datetime} }
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
    return f"El bot de la <b>Agencia Sofía</b> está activo en el canal {CANAL}."

@app.route('/ping')
def ping():
    return "OK", 200

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

def limpiar_recomendaciones_diarias():
    RECOMENDADOS_HOY.clear()
    ACIERTOS_HOY.clear()
    CONTEO_ANIMALES_HOY.clear()

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

def enviar_saludo_madrugada():
    enviar_telegram(
        "☕ ¡Buenos días a todos! ☀️\n\nQue hoy sea un día lleno de salud y muchos aciertos. 🙏✨\n📲 WhatsApp: 04163199157\n" + ENLACE_CANAL,
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

    # Semilla única para Sofía diferente a cualquier otra agencia (+9999)
    seed_val = int(ahora.strftime("%Y%m%d")) + 9999
    rnd = random.Random(seed_val)
    
    # Seleccionar números totalmente independientes basados en la semilla de Sofía
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
    # Generador con semilla única y dinámica basada en microsegundos para evitar patrones cruzados
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
    """Convierte un string de hora tipo '4:00 PM' en un objeto datetime de hoy con esa hora exacta."""
    try:
        limpia = hora_str.strip().upper()
        dt_time = datetime.strptime(limpia, "%I:%M %p")
        ahora = datetime.now()
        return ahora.replace(hour=dt_time.hour, minute=dt_time.minute, second=0, microsecond=0)
    except Exception:
        return None

def verificar_y_enviar_resultados_individuales():
    enviados_hoy = cargar_registros()
    es_primera = len(enviados_hoy) == 0
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

                # VALIDACIÓN CRÍTICA: ¿El sorteo ocurrió DESPUÉS de que se envió el dato/análisis?
                if numero in RECOMENDADOS_HOY and numero not in ACIERTOS_HOY:
                    info_rec = RECOMENDADOS_HOY[numero]
                    hora_emision = info_rec["hora_emision"]
                    dt_sorteo = parsear_hora_sorteo(hora)

                    # Solo celebra si el sorteo es estrictamente posterior a la emisión del mensaje
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

                if es_primera:
                    nuevos_para_guardar.add(id_res)
                    continue
                if id_res not in enviados_hoy:
                    enviar_telegram(HEADER_Sofia.format(nombre_loteria=nombre_loteria, hora=hora, resultado=resultado))
                    nuevos_para_guardar.add(id_res)
                    hubo_cambios = True
                    time.sleep(1.5)

        if es_primera or hubo_cambios:
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
    app.run(host="0.0.0.0", port=port)
