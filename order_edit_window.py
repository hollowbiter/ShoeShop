import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import config

class OrderEditWindow(tk.Toplevel):
    def __init__(self, app, parent_window, order_id=None):
        super().__init__(app)
        self.app = app
        self.parent = parent_window
        self.order_id = order_id
        self.title("Редактирование заказа" if order_id else "Добавление заказа")
        self.geometry("800x700")
        self.resizable(True, True)
        self.transient(app)
        self.grab_set()

        if hasattr(app, "order_edit_window") and app.order_edit_window and app.order_edit_window.winfo_exists():
            messagebox.showwarning("Предупреждение", "Окно редактирования заказа уже открыто")
            self.destroy()
            return
        app.order_edit_window = self

        self.load_combobox_data()
        self.create_widgets()
        if order_id:
            self.load_order_data()

    def load_combobox_data(self):
        cursor = self.app.db.conn.cursor()
        cursor.execute("SELECT id, address FROM addresses ORDER BY id")
        self.addresses = cursor.fetchall()
        cursor.execute("SELECT id, full_name FROM users ORDER BY full_name")
        self.users = cursor.fetchall()
        self.statuses = ["Новый", "Завершен", "Отменен"]

    def create_widgets(self):
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Номер заказа:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_id = tk.Entry(main_frame, state=config.STATE_READONLY if self.order_id else config.STATE_NORMAL)
        self.entry_id.grid(row=0, column=1, sticky="ew", pady=2)
        if not self.order_id:
            cursor = self.app.db.conn.cursor()
            cursor.execute("SELECT MAX(id) FROM orders")
            max_id = cursor.fetchone()[0] or 0
            self.entry_id.insert(0, str(max_id + 1))

        tk.Label(main_frame, text="Дата заказа:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_order_date = tk.Entry(main_frame)
        self.entry_order_date.grid(row=1, column=1, sticky="ew", pady=2)
        self.entry_order_date.insert(0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        tk.Label(main_frame, text="Дата доставки:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_delivery_date = tk.Entry(main_frame)
        self.entry_delivery_date.grid(row=2, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Адрес пункта выдачи:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.combo_address = ttk.Combobox(main_frame, values=[f"{a['id']}: {a['address']}" for a in self.addresses])
        self.combo_address.grid(row=3, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Клиент:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.combo_user = ttk.Combobox(main_frame, values=[f"{u['id']}: {u['full_name']}" for u in self.users])
        self.combo_user.grid(row=4, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Код для получения:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.entry_code = tk.Entry(main_frame)
        self.entry_code.grid(row=5, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Статус:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.combo_status = ttk.Combobox(main_frame, values=self.statuses)
        self.combo_status.grid(row=6, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Состав заказа (артикул, количество; через запятую):").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.text_items = tk.Text(main_frame, height=5, width=40)
        self.text_items.grid(row=7, column=1, sticky="ew", pady=2)

        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Сохранить", command=self.save_order, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.on_close, bg=config.COLOR_EXTRA_BG).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def load_order_data(self):
        cursor = self.app.db.conn.cursor()
        cursor.execute("""
            SELECT o.*, a.address, u.full_name
            FROM orders o
            LEFT JOIN addresses a ON o.address_id = a.id
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        """, (self.order_id,))
        order = cursor.fetchone()
        if order:
            self.entry_id.config(state=config.STATE_NORMAL)
            self.entry_id.delete(0, tk.END)
            self.entry_id.insert(0, order["id"])
            self.entry_id.config(state=config.STATE_READONLY)
            self.entry_order_date.delete(0, tk.END)
            self.entry_order_date.insert(0, order["order_date"] or "")
            self.entry_delivery_date.delete(0, tk.END)
            self.entry_delivery_date.insert(0, order["delivery_date"] or "")
            
            if order["address_id"]:
                self.combo_address.set(f"{order['address_id']}: {order['address']}")
            if order["user_id"]:
                self.combo_user.set(f"{order['user_id']}: {order['full_name']}")
                
            self.entry_code.delete(0, tk.END)
            self.entry_code.insert(0, order["pickup_code"] or "")
            self.combo_status.set(order["status"] or "")

            cursor.execute("SELECT product_article, quantity FROM order_items WHERE order_id=?", (self.order_id,))
            items = cursor.fetchall()
            items_str = ", ".join([f"{it['product_article']}, {it['quantity']}" for it in items])
            self.text_items.insert(config.TEXT_START, items_str)

    def _parse_order_items(self, items_str):
        items = []
        if not items_str:
            return items
            
        parts = [p.strip() for p in items_str.split(',')]
        if len(parts) % 2 != 0:
            raise ValueError("Нечетное количество элементов в составе заказа. Должны быть пары: артикул, количество")
            
        for i in range(0, len(parts), 2):
            article = parts[i]
            try:
                qty = int(parts[i+1])
            except ValueError:
                raise ValueError(f"Количество для артикула {article} должно быть целым числом")
            items.append((article, qty))
            
        return items

    def save_order(self):
        try:
            order_id = int(self.entry_id.get())
        except ValueError:
            messagebox.showerror(config.TITLE_ERROR, "Некорректный номер заказа")
            return
            
        order_date = self.entry_order_date.get().strip()
        delivery_date = self.entry_delivery_date.get().strip()
        address_text = self.combo_address.get().strip()
        user_text = self.combo_user.get().strip()
        code = self.entry_code.get().strip()
        status = self.combo_status.get().strip()
        items_str = self.text_items.get(config.TEXT_START, tk.END).strip()

        address_id = int(address_text.split(":")[0]) if address_text and ":" in address_text else None
        user_id = int(user_text.split(":")[0]) if user_text and ":" in user_text else None

        try:
            items = self._parse_order_items(items_str)
        except ValueError as e:
            messagebox.showerror(config.TITLE_ERROR, str(e))
            return

        cursor = self.app.db.conn.cursor()
        for article, _ in items:
            cursor.execute("SELECT article FROM products WHERE article=?", (article,))
            if not cursor.fetchone():
                messagebox.showerror(config.TITLE_ERROR, f"Товар с артикулом '{article}' не найден в базе")
                return

        cursor = self.app.db.conn.cursor()
        if self.order_id:
            cursor.execute('''
                UPDATE orders SET order_date=?, delivery_date=?, address_id=?, user_id=?, pickup_code=?, status=?
                WHERE id=?
            ''', (order_date, delivery_date, address_id, user_id, code, status, order_id))
            cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
        else:
            cursor.execute('''
                INSERT INTO orders (id, order_date, delivery_date, address_id, user_id, pickup_code, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, order_date, delivery_date, address_id, user_id, code, status))

        for article, qty in items:
            cursor.execute("INSERT INTO order_items (order_id, product_article, quantity) VALUES (?, ?, ?)", (order_id, article, qty))

        self.app.db.conn.commit()
        self.parent.load_orders()
        self.on_close()

    def on_close(self):
        self.app.order_edit_window = None
        self.destroy()