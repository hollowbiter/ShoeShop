import tkinter as tk
from tkinter import ttk, messagebox
import config
from order_edit_window import OrderEditWindow

class OrdersWindow(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=config.COLOR_MAIN_BG)
        self.app = app
        self.pack(fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(self, bg=config.COLOR_EXTRA_BG, height=40)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.pack_propagate(False)

        user_text = "Гость"
        if self.app.current_user:
            user_text = f"{self.app.current_user['full_name']} ({self.app.current_user['role']})"
        
        tk.Label(top_frame, text=user_text, bg=config.COLOR_EXTRA_BG, font=config.FONT_DEFAULT).pack(side=tk.RIGHT, padx=10)
        tk.Button(top_frame, text="Назад к товарам", command=self.app.show_products, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=10, pady=5)
        
        if self.app.current_user and self.app.current_user["role"] == config.ROLE_ADMIN:
            tk.Button(top_frame, text="Добавить заказ", command=self.add_order, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=10, pady=5)

        self.canvas = tk.Canvas(self, bg=config.COLOR_MAIN_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=config.COLOR_MAIN_BG)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_orders()

    def load_orders(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
                SELECT o.id, o.order_date, o.delivery_date, a.address, u.full_name, o.pickup_code, o.status
                FROM orders o
                LEFT JOIN addresses a ON o.address_id = a.id
                LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.id DESC
            """)
            
            rows = cursor.fetchall()
            if not rows:
                tk.Label(self.scrollable_frame, text="Заказов пока нет", bg=config.COLOR_MAIN_BG, font=config.FONT_ENTRY).pack(pady=50)
                return

            for row in rows:
                self.create_order_card(row)
        except Exception as e:
            tk.Label(self.scrollable_frame, text=f"Ошибка базы данных: {e}", fg="red", bg=config.COLOR_MAIN_BG).pack()

    def create_order_card(self, row):
        card = tk.Frame(self.scrollable_frame, bg=config.COLOR_MAIN_BG, relief=tk.RIDGE, bd=2)
        card.pack(fill=tk.X, padx=20, pady=10, ipady=10)

        left_box = tk.Frame(card, bg=config.COLOR_MAIN_BG)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(left_box, text=f"Артикул заказа: {row[0]}", font=config.FONT_BOLD, bg=config.COLOR_MAIN_BG, anchor=tk.W).pack(fill=tk.X)
        tk.Label(left_box, text=f"Статус заказа: {row[6]}", font=config.FONT_11, bg=config.COLOR_MAIN_BG, anchor=tk.W).pack(fill=tk.X)
        
        addr = row[3] if row[3] else "Адрес не указан"
        tk.Label(left_box, text=f"Адрес пункта выдачи: {addr}", font=config.FONT_11, bg=config.COLOR_MAIN_BG, anchor=tk.W, wraplength=600).pack(fill=tk.X)
        tk.Label(left_box, text=f"Дата заказа: {row[1]}", font=config.FONT_11, bg=config.COLOR_MAIN_BG, anchor=tk.W).pack(fill=tk.X)

        right_box = tk.Frame(card, bg=config.COLOR_MAIN_BG, relief=tk.SOLID, bd=1, width=150)
        right_box.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        right_box.pack_propagate(False)

        tk.Label(right_box, text="Дата доставки", font=config.FONT_SMALL, bg=config.COLOR_MAIN_BG).pack(pady=(5, 0))
        tk.Label(right_box, text=f"{row[2]}", font=config.FONT_11_BOLD, bg=config.COLOR_MAIN_BG).pack(expand=True)

        if self.app.current_user and self.app.current_user["role"] == config.ROLE_ADMIN:
            btn_frame = tk.Frame(left_box, bg=config.COLOR_MAIN_BG)
            btn_frame.pack(anchor=tk.W, pady=(10, 0))
            order_id = row[0]
            tk.Button(btn_frame, text="Редактировать", command=lambda i=order_id: OrderEditWindow(self.app, self, i), bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_frame, text="Удалить", command=lambda i=order_id: self.delete_order(i), bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=2)

    def delete_order(self, order_id):
        if messagebox.askyesno("Подтверждение", f"Удалить заказ №{order_id}?"):
            cursor = self.app.db.conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
            self.app.db.conn.commit()
            self.load_orders()

    def add_order(self):
        OrderEditWindow(self.app, self)

    def logout(self):
        self.app.current_user = None
        self.app.show_login()