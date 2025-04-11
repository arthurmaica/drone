import cv2
import numpy as np
import csv
import datetime

# Inicializar arquivo CSV
csv_filename = "detecoes.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Data", "Hora", "Objeto", "Confiança"])

# Carregar a rede YOLO otimizada
print("Carregando a rede YOLO...")
net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Carregar classes do COCO
print("Carregando as classes do COCO...")
classes = open("coco.names").read().strip().split("\n")

# Abrir a stream de vídeo
stream_url = "http://172.16.151.6:8080/?action=stream"
print(f"Conectando à stream: {stream_url}")
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print("Erro ao abrir a stream de vídeo!")
    exit()

cv2.namedWindow('YOLO Detecção', cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erro ao capturar frame!")
        break

    # Preparar imagem para YOLO
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (320, 320), swapRB=True, crop=False)
    net.setInput(blob)
    detections = net.forward(net.getUnconnectedOutLayersNames())

    height, width = frame.shape[:2]
    detected_objects = []

    # Processar detecções
    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > 0.1:  # Limite de confiança reduzido para detectar mais objetos
                center_x, center_y, w, h = (obj[0:4] * np.array([width, height, width, height])).astype("int")
                x, y = int(center_x - w / 2), int(center_y - h / 2)

                # Desenhar a caixa ao redor do objeto detectado
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{classes[class_id]} {confidence:.2f}", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                detected_objects.append((classes[class_id], confidence))

    # Registrar as detecções no CSV
    if detected_objects:
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            timestamp = datetime.datetime.now()
            for obj, conf in detected_objects:
                writer.writerow([timestamp.date(), timestamp.time(), obj, f"{conf:.2f}"])

    # Mostrar a imagem processada
    cv2.imshow('YOLO Detecção', frame)

    # Pressione 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

