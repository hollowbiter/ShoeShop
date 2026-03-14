import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk
import config
from product_edit_window import ProductEditWindow

class ProductsWindow(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=config.COLOR_MAIN_BG)
        self.app = app
        self.pack(fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(self, bg=config.COLOR_EXTRA_BG, height=40)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.pack_propagate(False)

        if self.app.current_user:
            fio = self.app.current_user["full_name"]
            role = self.app.current_user["role"]
            text = f"{fio} ({role})"
        else:
            text = "Гость"
        tk.Label(top_frame, text=text, bg=config.COLOR_EXTRA_BG, font=config.FONT_DEFAULT).pack(side=tk.RIGHT, padx=10, pady=5)
        tk.Button(top_frame, text="Выход", command=self.logout, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=10, pady=5)

        has_access = self.app.current_user and self.app.current_user["role"] in (config.ROLE_MANAGER, config.ROLE_ADMIN)
        if has_access:
            tk.Button(top_frame, text="Заказы", command=self.app.show_orders, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=10, pady=5)
            self.create_filter_panel()

        if self.app.current_user and self.app.current_user["role"] == config.ROLE_ADMIN:
            tk.Button(top_frame, text="Добавить товар", command=self.add_product, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=10, pady=5)

        self.canvas = tk.Canvas(self, bg=config.COLOR_MAIN_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=config.COLOR_MAIN_BG)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.load_products()

    def create_filter_panel(self):
        filter_frame = tk.Frame(self, bg=config.COLOR_MAIN_BG)
        filter_frame.pack(fill=tk.X, pady=5, padx=10)

        tk.Label(filter_frame, text="Поиск:", bg=config.COLOR_MAIN_BG, font=config.FONT_11).pack(side=tk.LEFT, padx=(5,2))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_products())
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, font=config.FONT_11, width=25, bd=2, relief=tk.SUNKEN)
        search_entry.pack(side=tk.LEFT, padx=(0,15))

        tk.Label(filter_frame, text="Сорт.:", bg=config.COLOR_MAIN_BG, font=config.FONT_11).pack(side=tk.LEFT, padx=(5,2))
        self.sort_var = tk.StringVar(value="Нет")
        self.sort_var.trace('w', lambda *args: self.load_products())
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var, values=["Нет", "По возрастанию", "По убыванию"], state=config.STATE_READONLY, width=15)
        sort_combo.pack(side=tk.LEFT, padx=(0,15))

        tk.Label(filter_frame, text="Поставщик:", bg=config.COLOR_MAIN_BG, font=config.FONT_11).pack(side=tk.LEFT, padx=(5,2))
        self.supplier_var = tk.StringVar(value=config.VALUE_ALL_SUPPLIERS)
        self.supplier_var.trace('w', lambda *args: self.load_products())
        cursor = self.app.db.conn.cursor()
        cursor.execute("SELECT name FROM suppliers ORDER BY name")
        suppliers = [config.VALUE_ALL_SUPPLIERS] + [row['name'] for row in cursor.fetchall()]
        supplier_combo = ttk.Combobox(filter_frame, textvariable=self.supplier_var, values=suppliers, state=config.STATE_READONLY, width=18)
        supplier_combo.pack(side=tk.LEFT, padx=(0,15))

        tk.Label(filter_frame, text="Категория:", bg=config.COLOR_MAIN_BG, font=config.FONT_11).pack(side=tk.LEFT, padx=(5,2))
        self.category_var = tk.StringVar(value=config.VALUE_ALL_CATEGORIES)
        self.category_var.trace('w', lambda *args: self.load_products())
        cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [config.VALUE_ALL_CATEGORIES] + [row['name'] for row in cursor.fetchall()]
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, values=categories, state=config.STATE_READONLY, width=15)
        category_combo.pack(side=tk.LEFT, padx=(0,5))

    def _build_product_query(self):
        query = '''
            SELECT p.*, cat.name as category_name, man.name as manufacturer_name, sup.name as supplier_name
            FROM products p
            LEFT JOIN categories cat ON p.category_id = cat.id
            LEFT JOIN manufacturers man ON p.manufacturer_id = man.id
            LEFT JOIN suppliers sup ON p.supplier_id = sup.id
        '''
        conditions, params = [], []

        if hasattr(self, 'search_var') and self.search_var.get().strip():
            search = self.search_var.get().strip()
            conditions.append('(p.article LIKE ? OR p.name LIKE ? OR p.description LIKE ? OR cat.name LIKE ? OR man.name LIKE ? OR sup.name LIKE ?)')
            params.extend([f'%{search}%'] * 6)

        if hasattr(self, 'supplier_var') and self.supplier_var.get() != config.VALUE_ALL_SUPPLIERS:
            conditions.append("sup.name = ?")
            params.append(self.supplier_var.get())

        if hasattr(self, 'category_var') and self.category_var.get() != config.VALUE_ALL_CATEGORIES:
            conditions.append("cat.name = ?")
            params.append(self.category_var.get())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if hasattr(self, 'sort_var'):
            if self.sort_var.get() == "По возрастанию":
                query += " ORDER BY p.quantity ASC"
            elif self.sort_var.get() == "По убыванию":
                query += " ORDER BY p.quantity DESC"

        return query, params

    def load_products(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        cursor = self.app.db.conn.cursor()
        query, params = self._build_product_query()

        try:
            cursor.execute(query, params)
            products = cursor.fetchall()
        except Exception as e:
            print("Ошибка при выполнении запроса:", e)
            products = []

        for prod in products:
            self.create_product_card(prod)

        self.scrollable_frame.update_idletasks()
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox and bbox[3] <= self.canvas.winfo_height():
            self.canvas.configure(scrollregion=bbox)
            self.scrollbar.pack_forget()
        else:
            self.canvas.configure(scrollregion=bbox)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _get_card_bg(self, quantity, discount):
        if quantity == 0:
            return config.COLOR_OUT_OF_STOCK
        if discount > 15:
            return config.COLOR_DISCOUNT_HIGH
        return config.COLOR_MAIN_BG

    def _setup_image(self, parent, img_path):
        img_frame = tk.Frame(parent, bg=config.COLOR_MAIN_BG, width=120, height=120)
        img_frame.pack(side=tk.LEFT, padx=5, pady=5)
        img_frame.pack_propagate(False)
        
        if img_path and os.path.exists(img_path):
            pil_img = Image.open(img_path)
        else:
            pil_img = Image.open(config.DEFAULT_IMAGE)
            
        pil_img.thumbnail((120, 120), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil_img)
        img_label = tk.Label(img_frame, image=photo, bg=config.COLOR_MAIN_BG)
        img_label.image = photo
        img_label.pack(expand=True, fill=tk.BOTH)

    def _setup_price_labels(self, parent, bg_color, price, discount):
        price_frame = tk.Frame(parent, bg=bg_color)
        price_frame.pack(anchor=tk.W, fill=tk.X, pady=2)
        
        if discount > 0:
            final_price = price * (1 - discount / 100)
            tk.Label(price_frame, text=f"{price:.2f} руб.", fg="red", bg=bg_color, font=config.FONT_OLD_PRICE).pack(side=tk.LEFT, padx=(0, 5))
            tk.Label(price_frame, text=f"{final_price:.2f} руб.", fg="black", bg=bg_color, font=config.FONT_SMALL_BOLD).pack(side=tk.LEFT)
        else:
            tk.Label(price_frame, text=f"{price:.2f} руб.", font=config.FONT_SMALL, bg=bg_color).pack(side=tk.LEFT)

    def _create_discount_badge(self, parent, discount):
        disc_frame = tk.Frame(parent, bg=config.COLOR_MAIN_BG, width=110, height=110, relief=tk.RIDGE, bd=2)
        disc_frame.pack(side=tk.RIGHT, padx=5, pady=5)
        disc_frame.pack_propagate(False)
        inner_frame = tk.Frame(disc_frame, bg=config.COLOR_MAIN_BG)
        inner_frame.pack(expand=True)
        tk.Label(inner_frame, text="Скидка", bg=config.COLOR_MAIN_BG, font=config.FONT_SMALL_BOLD).pack(anchor="center")
        tk.Label(inner_frame, text=f"{int(discount)}%", bg=config.COLOR_MAIN_BG, font=config.FONT_DISCOUNT, fg="red").pack(anchor="center")

    def create_product_card(self, prod):
        bg_color = self._get_card_bg(prod["quantity"], prod["discount"])
        card = tk.Frame(self.scrollable_frame, bg=bg_color, relief=tk.RAISED, bd=1)
        card.pack(fill=tk.X, padx=10, pady=5, ipadx=5, ipady=5)
        
        self._setup_image(card, prod['photo'])

        text_frame = tk.Frame(card, bg=bg_color)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(text_frame, text=f"{prod['category_name'] or ''} | {prod['name'] or ''}", font=config.FONT_BOLD, bg=bg_color, anchor=tk.W).pack(anchor=tk.W, fill=tk.X)

        desc = prod["description"] or ""
        if len(desc) > 100:
            desc = desc[:100] + "..."
        tk.Label(text_frame, text=f"Описание товара: {desc}", bg=bg_color, font=config.FONT_SMALL, wraplength=400, justify=tk.LEFT, anchor=tk.W).pack(anchor=tk.W, fill=tk.X)
        tk.Label(text_frame, text=f"Производитель: {prod['manufacturer_name'] or ''}", bg=bg_color, font=config.FONT_SMALL, anchor=tk.W).pack(anchor=tk.W, fill=tk.X)
        tk.Label(text_frame, text=f"Поставщик: {prod['supplier_name'] or ''}", bg=bg_color, font=config.FONT_SMALL, anchor=tk.W).pack(anchor=tk.W, fill=tk.X)

        self._setup_price_labels(text_frame, bg_color, prod["price"], prod["discount"] or 0)

        tk.Label(text_frame, text=f"Единица измерения: {prod['unit'] or ''}", bg=bg_color, font=config.FONT_SMALL, anchor=tk.W).pack(anchor=tk.W, fill=tk.X)
        tk.Label(text_frame, text=f"Количество на складе: {prod['quantity']}", bg=bg_color, font=config.FONT_SMALL, anchor=tk.W).pack(anchor=tk.W, fill=tk.X)

        if (prod["discount"] or 0) > 0:
            self._create_discount_badge(card, prod["discount"])

        if self.app.current_user and self.app.current_user["role"] == config.ROLE_ADMIN:
            btn_frame = tk.Frame(text_frame, bg=bg_color)
            btn_frame.pack(anchor="e", pady=2, fill=tk.X)
            tk.Button(btn_frame, text="Редактировать", command=lambda p=prod: self.edit_product(p["article"]), bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_frame, text="Удалить", command=lambda p=prod: self.delete_product(p["article"]), bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=2)

    def logout(self):
        self.app.current_user = None
        self.app.show_login()

    def add_product(self):
        ProductEditWindow(self.app, self)

    def edit_product(self, article):
        ProductEditWindow(self.app, self, article)

    def delete_product(self, article):
        cursor = self.app.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE product_article=?", (article,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror(config.TITLE_ERROR, "Нельзя удалить товар, который присутствует в заказах")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить товар {article}?"):
            cursor.execute("DELETE FROM products WHERE article=?", (article,))
            self.app.db.conn.commit()
            self.load_products()