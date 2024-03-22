
import sys; sys.dont_write_bytecode = True # don't create __pycache__
import logging
from pyzkfp import ZKFP2
from PIL import Image, ImageTk


from time import sleep
from threading import Thread

import pickle
import os

import tkinter as tk
from tkinter import ttk
import requests
from io import BytesIO






logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class PopupWindow:
    def __init__(self, master, dni):
        self.master = master
        self.dni = dni
        
        self.popup = tk.Toplevel(master)
        self.popup.title("Usuario Identificado")
        self.popup.geometry("300x200")
        
        self.label = tk.Label(self.popup, text=f"Usuario identificado correctamente.\nDNI: {self.dni}")
        self.label.pack()

        self.button = tk.Button(self.popup, text="Cerrar", command=self.close_popup)
        self.button.pack()

    def close_popup(self):
        self.popup.destroy()

class FingerprintScanner:
    def open_popup(self, dni):
        print(f"ingreso aqui {dni}")
        root = tk.Tk()
        app = MainWindow2(root, dni)
        root.mainloop()
        # popup_window = PopupWindow(self.master, dni)
    def __init__(self, master):
        self.master = master
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

            if self.register == False:
                        # Cargar todas las plantillas guardadas
                        for filename in os.listdir('.'):
                            if filename.endswith('.pkl'):
                                with open(filename, 'rb') as f:
                                    saved_template = pickle.load(f)
                                    # Comparar la huella capturada con la plantilla guardada
                                    match = self.zkfp2.DBMatch(tmp, saved_template)
                                    if match:
                                        self.logger.info(f"Usuario identificado correctamente: {filename[:-4]}, Score: {score}")
                                        self.zkfp2.Light('green')
                                        self.open_popup(filename[:-4])
                                        self.capture = None
                                        return
                                    
                        self.zkfp2.Light('red')
                        print("NO SE ENCONTRO NINGUN USUARIO CON ESTA HUELLA")
                        self.register = input("Do you want to register a new user? [y/n]: ").lower() == 'y'


            if self.register: # registeration logic
                if len(self.templates) < 3:
                    if not self.templates or self.zkfp2.DBMatch(self.templates[-1], tmp) > 0: # check if the finger is the same
                        self.zkfp2.Light('green')
                        self.templates.append(tmp)

                        message = f"Finger {len(self.templates)} registered successfully! " + (f"{3-len(self.templates)} presses left." if 3-len(self.templates) > 0 else '')
                        self.logger.info(message)

                        # blob_image = self.zkfp2.Blob2Base64String(img) # convert the image to base64 string

                if len(self.templates) == 3:
                    regTemp, regTempLen = self.zkfp2.DBMerge(*self.templates)
                    self.zkfp2.DBAdd(self.fid, regTemp)

                    # Convertir el objeto 'Byte[]' a una lista de bytes
                    regTemp = list(regTemp)

                    # Solicitar el DNI al usuario
                    dni = input("Por favor, ingrese su DNI: ")

                    # Guardar la plantilla de la huella digital en un archivo utilizando pickle
                    with open(f'{dni}.pkl', 'wb') as f:
                        pickle.dump(regTemp, f)

                    self.templates.clear()
                    self.register = False
                    self.fid += 1


        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.zkfp2.Terminate()
            exit(0)

        # release the capture
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

class MainWindow2:
    
        
    def __init__(self, root, dni):
        self.root = root
        self.root.title("UNDAC - huellas ")
        # self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.geometry("700x400")

        url = f"http://143.198.105.92:3500/general/estudiantes/consultar-datos-dni-por-proceso/{dni}/{27}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                datos_estudiante = response.json()
                print("estudiantes", datos_estudiante, len(datos_estudiante))
                if(len(datos_estudiante) == 0):
                    self.root.after(0, self.root.destroy)
                    print("Estudiante no inscrito")
                    return
                # print(f"{fg(34)}{ef.bold}{bg.da_green}Estudiante {datos_estudiante[0]['AP_PATERNO']} {datos_estudiante[0]['AP_MATERNO']} {datos_estudiante[0]['NOMBRES']} - {datos_estudiante[0]['CARRERA']} - {datos_estudiante[0]['DNI']}{rs.all}")
                # self.label = tk.Label(self.root, text=f"DNI {dni}")
                # self.label.pack()

                # Crear un Treeview con encabezados
                # self.tree = ttk.Treeview(self.root, columns=("LABEL", "Edad", "País"))
                
                
                
                url = f"http://143.198.105.92:3500/{datos_estudiante[0]['DNI']}/{datos_estudiante[0]['DNI']}.jpeg"
                response = requests.get(url)
                image_data = response.content
                
                image = Image.open(BytesIO(image_data))
                image = image.resize((150, 150))
                self.photo = ImageTk.PhotoImage(image)

                # Crear un widget Label para mostrar la imagen
                self.label_image = tk.Label(root, image=self.photo)
                self.label_image.pack()
                

                # Crear un widget Label para mostrar la imagen
                
                
                # Agregar encabezados
                # self.tree.heading("#0", text="ID")
                # self.tree = ttk.Treeview(self.root, columns=("DNI", "Apellido Paterno", "Apellido Materno", "Nombres", "Carrera"))
                
                # self.tree.heading("DNI", text="DNI")
                # self.tree.heading("Apellido Paterno", text="Apellido Paterno")
                # self.tree.heading("Apellido Materno", text="Apellido Materno")
                # self.tree.heading("Nombres", text="Nombres")
                # self.tree.heading("Carrera", text="Carrera")

                # Agregar filas de ejemplo
                self.label2 = tk.Label(self.root, text=f"{datos_estudiante[0]['NOMBRE_PROCESO']}", font=("Helvetica", 20, "bold"))
                self.label2.pack()
                # self.tree.insert("", "end", text="3", values=(datos_estudiante[0]['DNI'],datos_estudiante[0]['AP_PATERNO'],datos_estudiante[0]['AP_MATERNO'], datos_estudiante[0]['NOMBRES'], datos_estudiante[0]['CARRERA']))
                # self.tree.insert("", "end", text="1", values=("Apellido Paterno", ))
                # self.tree.insert("", "end", text="2", values=("Apellido Materno", ))
                # self.tree.insert("", "end", text="3", values=("Nombres",))
                # self.tree.insert("", "end", text="3", values=("Carrera",))

                # self.tree.pack()

                # self.label2 = tk.Label(self.root, text=f"Apellido Paterno: {datos_estudiante[0]['AP_PATERNO']}")
                # self.label2.pack()
                
                self.DNI = tk.Label(self.root, text=f"{datos_estudiante[0]['DNI']}", font=("Helvetica", 12, "bold"))
                self.DNI.pack()
                
                self.nombreCompleto = tk.Label(self.root, text=f"{datos_estudiante[0]['AP_PATERNO']} {datos_estudiante[0]['AP_MATERNO']} {datos_estudiante[0]['NOMBRES']}", font=("Helvetica", 12, "bold"))
                self.nombreCompleto.pack()
                
                self.nombreCarrera = tk.Label(self.root, text=f"{datos_estudiante[0]['CARRERA']}", font=("Helvetica", 12, "bold"))
                self.nombreCarrera.pack()
                
                # self.label3 = tk.Label(self.root, text=f"Apellido Materno: {datos_estudiante[0]['AP_MATERNO']}")
                # self.label3.pack()

                # self.label4 = tk.Label(self.root, text=f"Nombres: {datos_estudiante[0]['NOMBRES']}")
                # self.label4.pack()
                
                # self.label5 = tk.Label(self.root, text=f"Proceso: {datos_estudiante[0]['NOMBRE_PROCESO']}")
                # self.label5.pack()

                # self.label6 = tk.Label(self.root, text=f"Carrera: {datos_estudiante[0]['CARRERA']}")
                # self.label6.pack()
                
                # self.label7 = tk.Label(self.root, text=f"DNI: {datos_estudiante[0]['DNI']}")
                # self.label7.pack()


                self.button = tk.Button(self.root, text="Comenzar", command=self.start_fingerprint_scanner)
                self.button.pack()
                
                self.root.after(3500, self.root.destroy)
                
                
                # print(f"Estudiante {datos_estudiante[0]['AP_PATERNO']} {datos_estudiante[0]['AP_MATERNO']} {datos_estudiante[0]['NOMBRES']} - {datos_estudiante[0]['CARRERA']} - {datos_estudiante[0]['DNI']}")
            else:
                print("Error al obtener los datos del estudiante. Código de estado:", response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error de conexión:", e)
    def start_fingerprint_scanner(self):
        self.root.destroy()  # Cierra la ventana principal

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Inicio")
        self.root.geometry("300x200")

        self.label = tk.Label(self.root, text="Presiona el botón para comenzar el escaneo de huellas dactilares")
        self.label.pack()

        self.button = tk.Button(self.root, text="Comenzar", command=self.start_fingerprint_scanner)
        self.button.pack()
    def start_fingerprint_scanner(self):
        self.root.destroy()  # Cierra la ventana principal
        fingerprint_scanner = FingerprintScanner(root)  # Crea una instancia del escáner de huellas dactilares
        fingerprint_scanner.listenToFingerprints()  # Inicia el escaneo de huellas dactilares


if __name__ == "__main__":
    # Crear la ventana principal
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

    # Ejecutar el bucle principal de la aplicación
    # fingerprint_scanner = FingerprintScanner()
    # fingerprint_scanner.listenToFingerprints()
