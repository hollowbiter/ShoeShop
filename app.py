import tkinter as tk
import os
from config import DB_NAME, IMAGE_FOLDER, ICON_FILE
from database import Database
from login_window import LoginWindow
from products_window import ProductsWindow
from orders_window import OrdersWindow

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО Обувь - Вход")
        self.geometry("1200x800")
        self.resizable(True, True)
        if os.path.exists(ICON_FILE):
            self.iconbitmap(ICON_FILE)
        self.db = Database(DB_NAME)
        self.current_user = None
        if not os.path.exists(IMAGE_FOLDER):
            os.makedirs(IMAGE_FOLDER)
        self.show_login()

    def show_login(self):
        self.title("ООО Обувь - Вход")
        self.clear_window()
        LoginWindow(self)

    def show_products(self):
        self.title("ООО Обувь - Товары")
        self.clear_window()
        ProductsWindow(self)

    def show_orders(self):
        self.title("ООО Обувь - Заказы")
        self.clear_window()
        OrdersWindow(self)

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    required_files = [
        "user_import.xlsx",
        "Tovar.xlsx",
        "Заказ_import.xlsx",
        "Пункты выдачи_import.xlsx",
        "picture.png",
    ]
    for f in required_files:
        if not os.path.exists(f):
            print(f"Предупреждение: файл {f} не найден")
    app = App()
    app.mainloop()