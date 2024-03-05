import tkinter as tk
from tkinter import ttk
import requests
import logging
from pyzkfp import ZKFP2
from time import sleep
from threading import Thread
import pickle
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class FingerprintScanner:
    def __init__(self):
        self.logger = logging.getLogger('fps')
        fh = logging.FileHandler('logs.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)
        self.templates = []
        self.initialize_zkfp2()
        self.capture = None
        self.register = False
        self.fid = 1
        self.keep_alive = True

    def initialize_zkfp2(self):
        self.zkfp2 = ZKFP2()
        self.zkfp2.Init()
        self.logger.info(f"{(i := self.zkfp2.GetDeviceCount())} Devices found. Connecting to the first device.")
        self.zkfp2.OpenDevice(0)
        self.zkfp2.Light("green")

    def capture_handler(self):
        try:
            tmp, img = self.capture
            fid, score = self.zkfp2.DBIdentify(tmp)
            if fid:
                self.logger.info(f"successfully identified the user: {fid}, Score: {score}")
                self.zkfp2.Light('green')
                self.capture = None
                return
            if not self.register:
                for filename in os.listdir('.'):
                    if filename.endswith('.pkl'):
                        with open(filename, 'rb') as f:
                            saved_template = pickle.load(f)
                            match = self.zkfp2.DBMatch(tmp, saved_template)
                            if match:
                                self.logger.info(f"Usuario identificado correctamente: {filename[:-4]}, Score: {score}")
                                obtener_estudiante(filename[:8])
                                self.zkfp2.Light('green')
                                self.capture = None
                                return
                self.zkfp2.Light('red')
                print("NO SE ENCONTRO NINGUN USUARIO CON ESTA HUELLA")
                self.register = input("Do you want to register a new user? [y/n]: ").lower() == 'y'
            if self.register:
                if len(self.templates) < 3:
                    if not self.templates or self.zkfp2.DBMatch(self.templates[-1], tmp) > 0:
                        self.zkfp2.Light('green')
                        self.templates.append(tmp)
                        message = f"Finger {len(self.templates)} registered successfully! " + \
                                  (f"{3-len(self.templates)} presses left." if 3-len(self.templates) > 0 else '')
                        self.logger.info(message)
                if len(self.templates) == 3:
                    regTemp, regTempLen = self.zkfp2.DBMerge(*self.templates)
                    self.zkfp2.DBAdd(self.fid, regTemp)
                    regTemp = list(regTemp)
                    dni = input("Por favor, ingrese su DNI: ")
                    with open(f'{dni}.pkl', 'wb') as f:
                        pickle.dump(regTemp, f)
                    self.templates.clear()
                    self.register = False
                    self.fid += 1
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.zkfp2.Terminate()
            exit(0)
        self.capture = None

    def _capture_handler(self):
        try:
            self.capture_handler()
        except Exception as e:
            self.logger.error(e)
            self.capture = None

    def listenToFingerprints(self):
        try:
            while self.keep_alive:
                capture = self.zkfp2.AcquireFingerprint()
                if capture and not self.capture:
                    self.capture = capture
                    Thread(target=self._capture_handler, daemon=True).start()
                sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.zkfp2.Terminate()
            exit(0)


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


def obtener_estudiante(dni_param, proceso_param = 27):
    
    # dni = entrada_texto.get()
    # proceso_seleccionado_label = combo_procesos.get()
    # proceso_seleccionado = None
    # for proceso in procesos_disponibles:
    #     if proceso['label'] == proceso_seleccionado_label:
    #         proceso_seleccionado = proceso['value']
    #         break
    url = f"http://localhost:3500/general/estudiantes/consultar-datos-dni-por-proceso/{dni_param}/{proceso_param}"
    print(url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            datos_estudiante = response.json()
            print(f"Estudiante {datos_estudiante[0]['AP_PATERNO']} {datos_estudiante[0]['AP_MATERNO']} {datos_estudiante[0]['NOMBRES']} - {datos_estudiante[0]['CARRERA']} - {datos_estudiante[0]['DNI']}")
            # etiqueta = tk.Label(ventana, text=f"Apellido Paterno: {datos_estudiante[0]['AP_PATERNO']}")
            # etiqueta.pack()
            # etiqueta = tk.Label(ventana, text=f"Apellido Materno: {datos_estudiante[0]['AP_MATERNO']}")
            # etiqueta.pack()
            # etiqueta = tk.Label(ventana, text=f"Nombres: {datos_estudiante[0]['NOMBRES']}")
            # etiqueta.pack()
            # etiqueta = tk.Label(ventana, text=f"Proceso: {datos_estudiante[0]['NOMBRE_PROCESO']}")
            # etiqueta.pack()
            # etiqueta = tk.Label(ventana, text=f"Carrera: {datos_estudiante[0]['CARRERA']}")
            # etiqueta.pack()
            # etiqueta = tk.Label(ventana, text=f"DNI: {datos_estudiante[0]['DNI']}")
            # etiqueta.pack()
        else:
            print("Error al obtener los datos del estudiante. Código de estado:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error de conexión:", e)


# ventana = tk.Tk()
# ventana.title("ADMISION UNDAC HUELLAS")
# entrada_texto = tk.Entry(ventana)
# entrada_texto.pack()
# procesos_disponibles = obtener_procesos()
# labels_procesos = [proceso['label'] for proceso in procesos_disponibles]
# combo_procesos = ttk.Combobox(ventana, values=labels_procesos)
# combo_procesos.pack()
# boton = tk.Button(ventana, text="Obtener estudiante", command=obtener_estudiante)
# boton.pack()
fingerprint_scanner = FingerprintScanner()
fingerprint_scanner.listenToFingerprints()
# ventana.mainloop()