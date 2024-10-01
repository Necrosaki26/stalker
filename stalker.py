import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import threading
import os
from datetime import datetime

# Ruta al chromedriver
driver_path = '/usr/local/bin/chromedriver'

# Configuración del servicio para Selenium
service = Service(driver_path)

# Inicializa el navegador con Selenium usando Google Chrome
options = webdriver.ChromeOptions()
options.binary_location = '/usr/bin/google-chrome'  # Ruta al binario de Google Chrome

# Directorio para guardar la sesión de WhatsApp
user_data_dir = '/home/centosrancios3.0/.config/google-chrome/User Data'
os.makedirs(user_data_dir, exist_ok=True)  # Crea el directorio si no existe
options.add_argument(f"user-data-dir={user_data_dir}")

driver = webdriver.Chrome(service=service, options=options)

# Abre WhatsApp Web
driver.get('https://web.whatsapp.com')

# Clase para la ventana inicial donde se ingresa el nombre del contacto
class ContactInputWindow(tk.Toplevel):  # Cambiado a tk.Toplevel
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.title("Seleccionar Contacto")
        self.geometry("300x150")
        
        # Etiqueta y campo de entrada para el nombre del contacto
        self.label = tk.Label(self, text="Nombre del contacto:", font=("Arial", 12))
        self.label.pack(pady=10)
        
        self.contact_entry = tk.Entry(self, font=("Arial", 12), width=30)
        self.contact_entry.pack(pady=10)
        
        # Botón para iniciar el monitoreo
        self.start_button = tk.Button(self, text="Iniciar Monitoreo", command=self.start_monitoring)
        self.start_button.pack(pady=10)

    def start_monitoring(self):
        contact_name = self.contact_entry.get().strip()
        if not contact_name:
            messagebox.showerror("Error", "Debes ingresar un nombre de contacto.")
            return
        
        # Verifica si el código QR está visible
        if self.is_qr_visible():
            input("Escanea el código QR y presiona Enter para continuar...")

        # Busca el contacto en WhatsApp
        search_box = self.driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.click()

        # Envía el nombre del contacto carácter por carácter
        for char in contact_name:
            search_box.send_keys(char)
            time.sleep(0.1)  # Pequeña pausa entre caracteres

        search_box.send_keys(Keys.ENTER)

        # Cierra la ventana actual y abre la ventana de monitoreo
        self.destroy()
        monitor_window = OnlineStatusApp(self.driver, contact_name)
        monitor_window.mainloop()

    def is_qr_visible(self):
        try:
            # Intenta encontrar el elemento del código QR
            qr_element = self.driver.find_element(By.XPATH, '//canvas[contains(@class,"qr")]')
            return True  # El QR está visible
        except:
            return False  # El QR no está visible, la sesión está activa

# Clase para la ventana de monitoreo
class OnlineStatusApp(tk.Toplevel):  # Cambiado a tk.Toplevel
    def __init__(self, driver, contact_name):
        super().__init__()
        self.driver = driver
        self.contact_name = contact_name
        self.is_online = False
        self.check_interval = 1  # Intervalo de chequeo en segundos
        
        self.title(f"Monitoreo de {self.contact_name}")
        self.geometry("300x200")
        
        self.status_label = tk.Label(self, text=f"{self.contact_name} no está en línea", font=("Arial", 14))
        self.status_label.pack(pady=20)
        
        self.time_label = tk.Label(self, text="Tiempo en línea: 0:00", font=("Arial", 12))
        self.time_label.pack(pady=10)

        self.record_button = tk.Button(self, text="Finalizar Monitoreo", command=self.confirm_exit)
        self.record_button.pack(pady=10)

        self.online_time = 0  # Tiempo total en línea en segundos
        self.start_time = None  # Hora de inicio
        self.update_status()

    def update_status(self):
        threading.Thread(target=self.check_online_status, daemon=True).start()
    
    def check_online_status(self):
        while True:
            try:
                online_status = self.driver.find_element(By.XPATH, '//span[@title="en línea"]')
                if not self.is_online:
                    self.is_online = True
                    self.online_time = 0  # Reinicia el tiempo en línea
                    self.start_time = time.time()  # Registra la hora de entrada
                    self.status_label.config(text=f"{self.contact_name} está en línea")
                    self.update_timer()  # Inicia el cronómetro
                else:
                    time.sleep(self.check_interval)
            except:
                if self.is_online:
                    self.record_time()  # Guarda la información cuando se va de línea
                    self.is_online = False
                    self.status_label.config(text=f"{self.contact_name} no está en línea")
            time.sleep(self.check_interval)

    def update_timer(self):
        if self.is_online:
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.time_label.config(text=f"Tiempo en línea: {minutes}:{seconds:02d}")
            self.after(1000, self.update_timer)  # Actualiza cada segundo

    def record_time(self):
        end_time = datetime.now()
        total_minutes = self.online_time // 60
        entry_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        exit_time = end_time.strftime("%Y-%m-%d %I:%M:%S %p")
        
        # Guarda la información en un archivo de texto
        with open("online_status.txt", "a") as f:
            f.write(f"Contacto: {self.contact_name}\n")
            f.write(f"Hora de entrada: {entry_time}\n")
            f.write(f"Hora de salida: {exit_time}\n")
            f.write(f"Tiempo total en línea: {total_minutes} minutos\n")
            f.write("-" * 40 + "\n")

    def confirm_exit(self):
        if messagebox.askyesno("Confirmar salida", "¿Quieres volver a usar el programa?"):
            self.driver.quit()
            contact_window = ContactInputWindow(self.driver)
            contact_window.mainloop()
            self.destroy()
        else:
            self.driver.quit()
            self.destroy()

if __name__ == "__main__":
    root = tk.Tk()  # Creación de la raíz principal
    root.withdraw()  # Oculta la ventana principal para evitar que aparezca en blanco
    contact_window = ContactInputWindow(driver)
    contact_window.mainloop()
    
    # Cierra el navegador al cerrar la aplicación
    driver.quit()
