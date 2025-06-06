import cv2 
from ultralytics import YOLO
import easyocr
from PIL import Image, ImageTk
import tkinter as tk
import time
import os
import threading
import csv
from datetime import datetime
from skimage.metrics import structural_similarity as ssim
import numpy as np
import re

# Leer placas autorizadas desde archivo CSV
def cargar_placas_autorizadas(ruta_csv):
    placas = set()
    with open(ruta_csv, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for fila in reader:
            if fila:  # Ignorar filas vacías
                placas.add(fila[0].strip().upper())
    return placas

placas_permitidas = cargar_placas_autorizadas("placas_autorizadas.csv")

# Crear lector EasyOCR
reader = easyocr.Reader(['en', 'es'])

# Cargar modelo YOLO personalizado
model = YOLO('./modelo/LP-detection.pt')  # Cambia a tu modelo si ya tienes uno entrenado

# Crear carpeta resultados
os.makedirs("resultados", exist_ok=True)

# Crear archivo CSV si no existe
csv_path = "resultados/registros_acceso.csv"
if not os.path.exists(csv_path):
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["FechaHora", "Placa", "Acceso"])

# Captura de video
cap = cv2.VideoCapture(0)

# Interfaz Tkinter
ventana = tk.Tk()
ventana.title("Reconocimiento de Placas")
ventana.geometry("800x600")

etiqueta_video = tk.Label(ventana)
etiqueta_video.pack()

# Etiqueta para mostrar el estado de acceso
etiqueta_estado = tk.Label(ventana, text="", font=("Arial", 24))
etiqueta_estado.pack(pady=20)

frame_dibujado = None

def comparar_imagenes(img1, img2):
    # Redimensionar las imágenes al mismo tamaño
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    # Convertir a escala de grises
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Calcular SSIM
    score = ssim(img1_gray, img2_gray)
    return score

def limpiar_texto_placa(texto):
    """
    Limpia y corrige el texto de la placa con manejo específico para placas hondureñas.
    Implementa una lógica mejorada para distinguir entre '0' y 'O' basada en el contexto.
    """
    if not texto:
        return texto

    # Eliminar espacios y caracteres no deseados
    texto = texto.strip().upper().replace(" ", "")
    
    # Eliminar caracteres especiales y puntuación
    texto = re.sub(r'[^\w]', '', texto)
    
    # Si el texto no tiene al menos 6 caracteres, no es una placa válida
    if len(texto) < 6:
        return texto
    
    # Separar la parte de letras y números
    parte_letras = texto[:3]
    parte_numeros = texto[3:]
    
    # Correcciones específicas para la parte de letras
    correcciones_letras = {
        '0': 'O',  # En la parte de letras, 0 siempre debe ser O
        '1': 'I',
        '2': 'Z',
        '8': 'B'
    }
    
    # Correcciones específicas para la parte numérica
    correcciones_numeros = {
        'O': '0',  # En la parte numérica, O siempre debe ser 0
        'I': '1',
        'Z': '2',
        'S': '5',
        'G': '6',
        'T': '7',
        'B': '8',
        'D': '0',
        'Q': '0',
        'U': '0'
    }
    
    # Aplicar correcciones a cada parte por separado
    parte_letras_corregida = ''
    for i, char in enumerate(parte_letras):
        # En la parte de letras, cualquier dígito probablemente es una letra mal interpretada
        if char.isdigit():
            # Mapeo específico para dígitos en la sección de letras
            if char in correcciones_letras:
                parte_letras_corregida += correcciones_letras[char]
            else:
                # Si no hay mapeo específico, mantener el carácter original
                parte_letras_corregida += char
        else:
            parte_letras_corregida += char
    
    parte_numeros_corregida = ''
    for i, char in enumerate(parte_numeros):
        # En la parte numérica, cualquier letra probablemente es un número mal interpretado
        if char.isalpha():
            # Mapeo específico para letras en la sección numérica
            if char in correcciones_numeros:
                parte_numeros_corregida += correcciones_numeros[char]
            else:
                # Si no hay mapeo específico, mantener el carácter original
                parte_numeros_corregida += char
        else:
            parte_numeros_corregida += char
    
    # Verificar que la parte de letras solo contenga letras después de las correcciones
    if not parte_letras_corregida.isalpha():
        return texto
    
    # Verificar que la parte numérica solo contenga números después de las correcciones
    if not parte_numeros_corregida.isdigit():
        return texto
    
    # Combinar las partes corregidas
    texto_corregido = parte_letras_corregida + parte_numeros_corregida
    
    # Verificar el formato final
    if validar_formato_placa(texto_corregido):
        return texto_corregido
    
    return texto

def validar_formato_placa(texto):
    """
    Verifica si el texto tiene formato de placa de Honduras
    """
    # Verificar longitud
    if len(texto) < 6 or len(texto) > 7:
        return False
    
    # Verificar que los primeros 3 caracteres sean letras
    if not texto[:3].isalpha():
        return False
    
    # Verificar que el resto sean números
    if not texto[3:].isdigit():
        return False
    
    # Verificar formato completo
    patron_placa = r'^[A-Z]{3}\d{3,4}$'
    return re.match(patron_placa, texto) is not None

def verificar_coincidencia(placa_img):
    # Obtener el texto de la placa actual
    resultado_ocr = reader.readtext(placa_img)
    texto_actual = ""
    if resultado_ocr:
        for (_, texto_detectado, prob) in resultado_ocr:
            if prob > 0.4:
                texto = texto_detectado.strip().upper().replace(" ", "")
                # Ignorar textos que contengan HONDURAS o CENTROAM
                if "HONDURAS" not in texto and "CENTROAM" not in texto:
                    # Aplicar limpieza y validación al texto detectado
                    texto_limpio = limpiar_texto_placa(texto)
                    if validar_formato_placa(texto_limpio):
                        texto_actual = texto_limpio
                    break
    
    if not texto_actual:
        return False
    
    # Leer el archivo BD.txt
    try:
        with open("BD.txt", "r", encoding="utf-8") as f:
            placas_comparacion = [line.strip().upper().replace(" ", "") for line in f.readlines()]
    except FileNotFoundError:
        print("Archivo BD.txt no encontrado")
        return False
    
    # Verificar si el texto actual está en la lista de placas
    return texto_actual in placas_comparacion

def actualizar_estado_acceso(acceso):
    if acceso == "Sí":
        etiqueta_estado.config(text="ACCESO PERMITIDO", fg="green")
    else:
        etiqueta_estado.config(text="ACCESO DENEGADO", fg="red")

def registrar_acceso(placa, acceso, placa_img):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Verificar coincidencia de texto
    coincidencia = verificar_coincidencia(placa_img)
    if coincidencia:
        acceso = "Sí"
    
    # Actualizar la etiqueta de estado
    actualizar_estado_acceso(acceso)
    
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([fecha_hora, placa, acceso])
    
    # Guardar imagen solo si hay texto
    if placa != "SinTexto":
        nombre_archivo = f"resultados/placa_{int(time.time())}.jpg"
        cv2.imwrite(nombre_archivo, placa_img)

def detectar_y_mostrar():
    global frame_dibujado
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        results = model(frame)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                if conf < 0.5:
                    continue

                # Dibujar rectángulo
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Recorte de la placa
                placa_img = frame[y1:y2, x1:x2]

                # OCR
                resultado_ocr = reader.readtext(placa_img)
                if resultado_ocr:
                    for (_, texto_detectado, prob) in resultado_ocr:
                        if prob > 0.4:
                            texto = texto_detectado.strip().upper().replace(" ", "")
                            # Ignorar si el texto es HONDURAS o CENTROAMÉRICA
                            if texto != "HONDURAS" and texto != "CENTROAMÉRICA":
                                # Limpiar y validar el texto detectado
                                texto_limpio = limpiar_texto_placa(texto)
                                if validar_formato_placa(texto_limpio):
                                    print("Texto detectado:", texto_limpio)
                                    acceso = "Sí" if texto_limpio in placas_permitidas else "No"
                                    registrar_acceso(texto_limpio, acceso, placa_img)
                                else:
                                    registrar_acceso("SinTexto", "No", placa_img)
                            else:
                                registrar_acceso("SinTexto", "No", placa_img)
                else:
                    registrar_acceso("SinTexto", "No", placa_img)

        frame_dibujado = frame.copy()
        time.sleep(1)

def mostrar_video():
    if frame_dibujado is not None:
        frame_rgb = cv2.cvtColor(frame_dibujado, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        etiqueta_video.imgtk = imgtk
        etiqueta_video.configure(image=imgtk)
    ventana.after(30, mostrar_video)

# Iniciar hilo
hilo_deteccion = threading.Thread(target=detectar_y_mostrar, daemon=True)
hilo_deteccion.start()

# Mostrar GUI
mostrar_video()
ventana.mainloop()

# Liberar cámara
cap.release()

