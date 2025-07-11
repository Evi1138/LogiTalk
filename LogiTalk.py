import base64
import io
import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image

set_appearance_mode("light")
set_default_color_theme("blue")


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('600x400')
        self.title("Chat Client")
        self.username = "Artem"

        self.menu_frame = CTkFrame(self, width=60, height=400)
        self.menu_frame.place(x=0, y=0)
        self.menu_frame.pack_propagate(False)

        self.is_show_menu = False
        self.speed_animate_menu = -20
        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)

        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=60, y=0)

        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.place(x=60, y=360)

        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.send_button.place(x=550, y=360)

        self.open_img_button = CTkButton(self, text='📂', width=50, height=40, command=self.open_image)
        self.open_img_button.place(x=495, y=360)

        self.after(0, self.adaptive_ui)

        self.add_message("Демонстрація зображення:",
                         CTkImage(Image.open('Знімок екрана 2025-06-06 192209.png'), size=(300, 300)))

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

    def toggle_show_menu(self):
        self.is_show_menu = not self.is_show_menu
        self.speed_animate_menu *= -1
        self.btn.configure(text='◀️' if self.is_show_menu else '▶️')
        self.show_menu()
        if self.is_show_menu:
            self.label = CTkLabel(self.menu_frame, text='Імʼя')
            self.label.pack(pady=30)
            self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
            self.entry.pack()
            self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
            self.save_button.pack()
        else:
            if hasattr(self, 'label'): self.label.destroy()
            if hasattr(self, 'entry'): self.entry.destroy()
            if hasattr(self, 'save_button'): self.save_button.destroy()

    def show_menu(self):
        self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
        if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() >= 60 and not self.is_show_menu:
            self.after(10, self.show_menu)

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"Ваш новий нік: {self.username}")

    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        chat_width = self.winfo_width() - self.menu_frame.winfo_width() - 20
        chat_height = self.winfo_height() - 60
        self.chat_field.place(x=self.menu_frame.winfo_width(), y=0)
        self.chat_field.configure(width=chat_width, height=chat_height)
        self.message_entry.place(x=self.menu_frame.winfo_width(), y=self.winfo_height() - 40)
        self.message_entry.configure(width=chat_width - 110)
        self.open_img_button.place(x=self.winfo_width() - 105, y=self.winfo_height() - 40)
        self.send_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.after(50, self.adaptive_ui)


    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color='grey')
        message_frame.pack(pady=5, anchor='w')
        wraplength_size = self.winfo_width() - self.menu_frame.winfo_width() - 40
        if not img:
            CTkLabel(message_frame, text=message, wraplength=wraplength_size,
                     text_color='black', justify='left').pack(padx=10, pady=5)
        else:
            CTkLabel(message_frame, text=message, wraplength=wraplength_size,
                     text_color='black', image=img, compound='top',
                     justify='left').pack(padx=10, pady=5)

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                pass
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]
        if msg_type == "TEXT" and len(parts) >= 3:
            author, message = parts[1], parts[2]
            self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE" and len(parts) >= 4:
            author, filename, b64_img = parts[1], parts[2], parts[3]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                ctk_img = CTkImage(pil_img, size=(300, 300))
                self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
            except Exception as e:
                self.add_message(f"Помилка відображення зображення: {e}")
        else:
            self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())
            self.add_message('', CTkImage(light_image=Image.open(file_name), size=(300, 300)))
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()



















