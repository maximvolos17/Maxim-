import socket  # Для створення з'єднання з сервером
import threading  # Для роботи в окремому потоці (не блокувати інтерфейс)
import tkinter as tk  # Бібліотека для GUI
from tkinter import simpledialog, messagebox, scrolledtext  # Додаткові компоненти інтерфейсу
from datetime import datetime  # Для відображення часу повідомлень

HOST = '127.0.0.1'  # IP-адреса сервера (локальний)
PORT = 65432        # Порт для підключення

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")  # Назва вікна

        # 📜 Область чату (тільки для читання)
        self.chat_area = scrolledtext.ScrolledText(master, state='disabled')
        self.chat_area.pack(padx=10, pady=5, fill='both', expand=True)

        # 🎨 Стилі для повідомлень: свої — сині, чужі — зелені
        self.chat_area.tag_config("me", foreground="blue")
        self.chat_area.tag_config("others", foreground="green")

        # ✍️ Мітка, яка показує, хто зараз друкує
        self.typing_label = tk.Label(master, text="", fg="gray")
        self.typing_label.pack(padx=10, pady=(0, 5), anchor='w')

        # 🧾 Поле вводу повідомлення
        self.entry = tk.Entry(master)
        self.entry.pack(padx=10, pady=5, fill='x')
        self.entry.bind("<Return>", self.send_message)  # Enter = надіслати
        self.entry.bind("<KeyRelease>", self.on_typing)  # При наборі — оновлення статусу друку

        # 📨 Кнопка надсилання
        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=5)

        # 🔌 Підключення до сервера
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except:
            messagebox.showerror("Connection Error", "Could not connect to server.")  # Помилка підключення
            self.master.quit()
            return 

        # 🧑‍💼 Запит імені користувача
        self.username = simpledialog.askstring("Username", "Enter your username:")
        if not self.username:
            messagebox.showerror("Username Error", "Username cannot be empty.")  # Якщо порожнє ім'я
            self.master.quit()
            return

        # ⏱ Відстеження останнього моменту набору
        self.last_typing_time = datetime.now()
        self.typing = False
        self.master.after(500, self.check_typing_status)  # Перевірка статусу друку кожні 0.5 сек

        # 📥 Старт потоку прийому повідомлень
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()

    # 🚀 Надсилання повідомлення
    def send_message(self, event=None):
        message = self.entry.get()  # Отримати текст з поля вводу
        if message:
            full_message = f"{self.username}: {message}"  # Формат: Ім’я: Повідомлення
            try:
                self.client_socket.send(full_message.encode('utf-8'))  # Надсилання на сервер
                self.entry.delete(0, tk.END)  # Очистити поле після надсилання
            except:
                messagebox.showerror("Send Error", "Could not send message.")  # Помилка надсилання
                self.master.quit()

    # ✍️ Метод, що викликається під час набору повідомлення
    def on_typing(self, event=None):
        self.last_typing_time = datetime.now()  # Оновлюємо час останнього набору
        if not self.typing:
            self.typing = True
            try:
                self.client_socket.send(f"{self.username} is typing...<TYPING>".encode('utf-8'))  # Повідомлення про набір
            except:
                pass

    # ⏳ Метод перевірки — чи ще користувач друкує
    def check_typing_status(self):
        if self.typing and (datetime.now() - self.last_typing_time).seconds > 2:
            self.typing = False
            try:
                self.client_socket.send(f"{self.username} stopped typing<TYPING>".encode('utf-8'))  # Повідомлення: перестав друкувати
            except:
                pass
        self.master.after(500, self.check_typing_status)  # Повторна перевірка кожні 0.5 сек

    # 📥 Отримання повідомлень від сервера
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')  # Отримання повідомлення
                if message.endswith("<TYPING>"):  # Перевірка, чи це повідомлення про набір тексту
                    typing_info = message.replace("<TYPING>", "")
                    if "stopped typing" in typing_info:
                        self.typing_label.config(text="")  # Очистити повідомлення
                    else:
                        self.typing_label.config(text=typing_info)  # Показати: хтось друкує
                    continue

                if ":" in message:
                    username, msg = message.split(":", 1)  # Розділити ім’я та текст
                    tag = "me" if username == self.username else "others"  # Визначити стиль повідомлення
                    current_time = datetime.now().strftime("%H:%M:%S")  # Поточний час
                    display_message = f"[{current_time}] {username}:{msg}"  # Формат повідомлення

                    self.chat_area.config(state='normal')  # Увімкнути поле
                    self.chat_area.insert(tk.END, display_message + '\n', tag)  # Додати повідомлення
                    self.chat_area.config(state='disabled')  # Знову вимкнути редагування
                    self.chat_area.yview(tk.END)  # Прокрутка вниз

                    if tag == "others":
                        self.master.bell()  # Звук при отриманні чужого повідомлення
            except:
                messagebox.showerror("Receive Error", "Connection lost.")  # Помилка при втраті зв'язку
                self.client_socket.close()
                break

# ▶️ Запуск програми
if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
