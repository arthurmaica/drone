import tkinter as tk
from tkinter import ttk
import sqlite3
import csv
import os
import subprocess

# Variáveis de controle
protocolo_process = None
script_ativo = False

# Criar banco de dados SQLite
def setup_database():
    conn = sqlite3.connect("detecoes.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            hora TEXT,
            objeto TEXT,
            confianca REAL
        )
    ''')
    conn.commit()
    conn.close()

# Inserir dados no banco de dados
def insert_data_from_csv(csv_filename):
    conn = sqlite3.connect("detecoes.db")
    cursor = conn.cursor()
    with open(csv_filename, newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Pular cabeçalho
        for row in reader:
            cursor.execute("INSERT INTO detections (data, hora, objeto, confianca) VALUES (?, ?, ?, ?)", row)
    conn.commit()
    conn.close()

# Carregar dados para a tabela
def load_data():
    conn = sqlite3.connect("detecoes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections ORDER BY id DESC")  # Ordem invertida
    rows = cursor.fetchall()
    conn.close()
    
    for row in tree.get_children():
        tree.delete(row)
    
    for row in rows:
        tree.insert("", "end", values=row)

def filter_data():
    if script_ativo:  # Verifica se o script está ativo
        tk.messagebox.showwarning("Atenção", "Não é possível filtrar enquanto o script estiver ativo!")
        return
    
    conn = sqlite3.connect("detecoes.db")
    cursor = conn.cursor()
    query = "SELECT * FROM detections WHERE 1=1 "
    params = []
    
    if entry_data.get():
        query += "AND data = ? "
        params.append(entry_data.get())
    if entry_hora.get():
        # Garantir que a hora inserida seja comparada corretamente
        query += "AND hora LIKE ? "  # Utiliza LIKE para permitir a comparação parcial da hora
        params.append(f"{entry_hora.get()}%")  # Adiciona o símbolo % para permitir comparações parciais
    if entry_objeto.get():
        query += "AND objeto LIKE ? "
        params.append(f"%{entry_objeto.get()}%")
    if entry_confianca.get():
        query += "AND confianca >= ? "
        params.append(entry_confianca.get())
    
    query += "ORDER BY id DESC"  # Ordem invertida
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    for row in tree.get_children():
        tree.delete(row)
    for row in rows:
        tree.insert("", "end", values=row)

# Função para monitorar modificações no CSV
def monitor_csv():
    global last_modified_time
    csv_filename = "/home/greice/Downloads/IA + CSV + monitoramento + otimização-20250307T185150Z-001/IA + CSV + monitoramento + otimização/detecoes.csv"  # Caminho completo do arquivo CSV
    try:
        file_modified_time = os.path.getmtime(csv_filename)
        if file_modified_time != last_modified_time:
            insert_data_from_csv(csv_filename)
            load_data()
            last_modified_time = file_modified_time
    except FileNotFoundError:
        pass

    # Chama a função novamente após um intervalo (por exemplo, 1 segundo)
    root.after(1000, monitor_csv)  # Continuar verificando mudanças no CSV

# Função para ligar/desligar o script protocolo_india.py
def toggle_protocolo():
    global protocolo_process, script_ativo
    
    if script_ativo:  # Se o script já está ativo, desliga ele
        if protocolo_process:
            protocolo_process.terminate()  # Termina o processo
        protocolo_process = None
        script_ativo = False
        button_protocolo.config(text="Ligar Monitoramento", bg="green")
        filter_button.config(state="normal")  # Habilita o filtro novamente
    else:  # Se o script não está ativo, liga ele
        protocolo_process = subprocess.Popen(["python3", "protocolo_india.py"])  # Inicia o script
        script_ativo = True
        button_protocolo.config(text="Desligar Monitoramento", bg="red")
        filter_button.config(state="disabled")  # Desabilita o filtro enquanto o script está ativo

# Criar interface gráfica
setup_database()
root = tk.Tk()
root.title("Análise")

frame_filters = tk.Frame(root)
frame_filters.pack(pady=10)

tk.Label(frame_filters, text="Data:").grid(row=0, column=0)
entry_data = tk.Entry(frame_filters)
entry_data.grid(row=0, column=1)

tk.Label(frame_filters, text="Hora:").grid(row=0, column=2)  # Novo filtro de Hora
entry_hora = tk.Entry(frame_filters)
entry_hora.grid(row=0, column=3)

tk.Label(frame_filters, text="Objeto:").grid(row=0, column=4)
entry_objeto = tk.Entry(frame_filters)
entry_objeto.grid(row=0, column=5)

tk.Label(frame_filters, text="Confiança mínima:").grid(row=0, column=6)
entry_confianca = tk.Entry(frame_filters)
entry_confianca.grid(row=0, column=7)

filter_button = tk.Button(frame_filters, text="Filtrar", command=filter_data)
filter_button.grid(row=0, column=8, padx=5)

# Botão para ligar/desligar o script
button_protocolo = tk.Button(root, text="Ligar Monitoramento", command=toggle_protocolo, bg="green", fg="white", font=("Helvetica", 12))
button_protocolo.pack(pady=10)

columns = ("ID", "Data", "Hora", "Objeto", "Confiança")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")
tree.pack(expand=True, fill="both")

# Inicializar a verificação de modificação do CSV
last_modified_time = 0
monitor_csv()  # Inicia o monitoramento do arquivo CSV

load_data()
root.mainloop()
