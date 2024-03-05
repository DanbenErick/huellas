import tkinter as tk
from tkinter import ttk
import requests


def obtener_procesos():
    try:
        response = requests.get("http://localhost:3500/input-controls/obtener-procesos")
        if response.status_code == 200:
            procesos = response.json()
            return procesos
        else:
            print("Error al obtener los procesos:", response.status_code)
            return []
    except requests.exceptions.RequestException as e:
        print("Error de conexión:", e)
        return []
def obtener_estudiante():
    dni = entrada_texto.get()  # Obtener el DNI ingresado
    

    proceso_seleccionado_label = combo_procesos.get()  # Obtener el proceso seleccionado (label)
    # Buscar el valor correspondiente al label seleccionado
    proceso_seleccionado = None

    for proceso in procesos_disponibles:
      if proceso['label'] == proceso_seleccionado_label:
          proceso_seleccionado = proceso['value']
          break
    url = f"http://localhost:3500/general/estudiantes/consultar-datos-dni-por-proceso/{dni}/{proceso_seleccionado}"  # Construir la URL de la API
    print("DNI:", dni)
    print("Proceso seleccionado (label):", proceso_seleccionado_label)
    print("Proceso seleccionado (value):", proceso_seleccionado)
    try:




        response = requests.get(url)  # Realizar la solicitud GET
        if response.status_code == 200:
            datos_estudiante = response.json()  # Obtener los datos del estudiante en formato JSON
            print("Datos del estudiante:", datos_estudiante)

            etiqueta = tk.Label(ventana, text=f"Apellido Paterno: {datos_estudiante[0]['AP_PATERNO']}")
            etiqueta.pack()
            
            etiqueta = tk.Label(ventana, text=f"Apellido Materno: {datos_estudiante[0]['AP_MATERNO']}")
            etiqueta.pack()

            etiqueta = tk.Label(ventana, text=f"Nombres: {datos_estudiante[0]['NOMBRES']}")
            etiqueta.pack()
            
            etiqueta = tk.Label(ventana, text=f"Proceso: {datos_estudiante[0]['NOMBRE_PROCESO']}")
            etiqueta.pack()

            etiqueta = tk.Label(ventana, text=f"Carrera: {datos_estudiante[0]['CARRERA']}")
            etiqueta.pack()
            
            etiqueta = tk.Label(ventana, text=f"DNI: {datos_estudiante[0]['DNI']}")
            etiqueta.pack()

        else:
            print("Error al obtener los datos del estudiante. Código de estado:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error de conexión:", e)

# Crear la ventana
ventana = tk.Tk()
ventana.title("ADMISION UNDAC HUELLAS")

# Crear un widget de etiqueta (Label)


# Crear un widget de entrada de texto (Entry)
entrada_texto = tk.Entry(ventana)
entrada_texto.pack()

# Obtener procesos desde la API
procesos_disponibles = obtener_procesos()

# Crear una lista solo con las etiquetas (labels) de los procesos
labels_procesos = [proceso['label'] for proceso in procesos_disponibles]

# Crear un combobox (select) con los procesos disponibles
combo_procesos = ttk.Combobox(ventana, values=labels_procesos)
combo_procesos.pack()

# Crear un botón
boton = tk.Button(ventana, text="Obtener estudiante", command=obtener_estudiante)
boton.pack()

# Ejecutar el bucle de eventos
ventana.mainloop()
