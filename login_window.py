import tkinter as tk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import config

class EntryWithContextMenu(tk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.context_menu = tk.Menu(self, tearoff=0)  
    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

class LoginWindow(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=config.COLOR_MAIN_BG)
        self.app = app
        self.pack(fill=tk.BOTH, expand=True)

        if os.path.exists(config.LOGO_FILE):
            logo_img = Image.open(config.LOGO_FILE)
            logo_img = logo_img.resize((150, 150), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(self, image=self.logo, bg=config.COLOR_MAIN_BG).pack(pady=10)

        tk.Label(self, text="Вход в систему", font=config.FONT_TITLE, bg=config.COLOR_MAIN_BG).pack(pady=5)

        frame = tk.Frame(self, bg=config.COLOR_MAIN_BG)
        frame.pack(pady=10)

        tk.Label(frame, text="Логин:", bg=config.COLOR_MAIN_BG, font=config.FONT_DEFAULT).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_login = EntryWithContextMenu(frame, font=config.FONT_ENTRY, width=25, bd=3, relief=tk.RIDGE)
        self.entry_login.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="Пароль:", bg=config.COLOR_MAIN_BG, font=config.FONT_DEFAULT).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_password = EntryWithContextMenu(frame, show="*", font=config.FONT_ENTRY, width=25, bd=3, relief=tk.RIDGE)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=config.COLOR_MAIN_BG)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Войти", command=self.login, bg=config.COLOR_ACCENT, 
          font=config.FONT_ENTRY, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Войти как гость", command=self.guest_login, bg=config.COLOR_EXTRA_BG,
          font=config.FONT_ENTRY, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def login(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()
        cursor = self.app.db.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE login=? AND password=?", (login, password))
        user = cursor.fetchone()
        if user:
            self.app.current_user = dict(user)
            self.app.show_products()
        else:
            messagebox.showerror(config.TITLE_ERROR, "Неверный логин или пароль")

    def guest_login(self):
        self.app.current_user = None
        self.app.show_products()