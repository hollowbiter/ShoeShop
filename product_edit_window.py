import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import re
from PIL import Image, ImageTk
import config

class ProductEditWindow(tk.Toplevel):
    def __init__(self, app, parent_window, article=None):
        super().__init__(app)
        self.app = app
        self.parent = parent_window
        self.article = article
        self.title("Редактирование товара" if article else "Добавление товара")
        self.geometry("800x900")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(app)
        self.grab_set()

        if hasattr(app, "edit_window") and app.edit_window and app.edit_window.winfo_exists():
            messagebox.showwarning("Предупреждение", "Окно редактирования уже открыто")
            self.destroy()
            return
        app.edit_window = self

        self.load_combobox_data()
        self.create_widgets()
        if article:
            self.load_product_data()

    def load_combobox_data(self):
        cursor = self.app.db.conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        self.categories = [row["name"] for row in cursor.fetchall()]
        cursor.execute("SELECT name FROM manufacturers ORDER BY name")
        self.manufacturers = [row["name"] for row in cursor.fetchall()]
        cursor.execute("SELECT name FROM suppliers ORDER BY name")
        self.suppliers = [row["name"] for row in cursor.fetchall()]

    def create_widgets(self):
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Артикул:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_article = tk.Entry(main_frame, state=config.STATE_READONLY if self.article else config.STATE_NORMAL)
        self.entry_article.grid(row=0, column=1, sticky="ew", pady=2)
        if not self.article:
            self.entry_article.insert(0, self.generate_article())

        tk.Label(main_frame, text="Наименование:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_name = tk.Entry(main_frame)
        self.entry_name.grid(row=1, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Категория:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.combo_category = ttk.Combobox(main_frame, values=self.categories, state=config.STATE_NORMAL)
        self.combo_category.grid(row=2, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Производитель:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.combo_manufacturer = ttk.Combobox(main_frame, values=self.manufacturers, state=config.STATE_NORMAL)
        self.combo_manufacturer.grid(row=3, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Поставщик:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.combo_supplier = ttk.Combobox(main_frame, values=self.suppliers, state=config.STATE_NORMAL)
        self.combo_supplier.grid(row=4, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Цена:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.entry_price = tk.Entry(main_frame)
        self.entry_price.grid(row=5, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Единица измерения:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.entry_unit = tk.Entry(main_frame)
        self.entry_unit.grid(row=6, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Количество на складе:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.entry_quantity = tk.Entry(main_frame)
        self.entry_quantity.grid(row=7, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Скидка (%):").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.entry_discount = tk.Entry(main_frame)
        self.entry_discount.grid(row=8, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Описание:").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.text_description = tk.Text(main_frame, height=5, width=40)
        self.text_description.grid(row=9, column=1, sticky="ew", pady=2)

        tk.Label(main_frame, text="Фото:").grid(row=10, column=0, sticky=tk.W, pady=2)
        self.photo_path = tk.StringVar()
        tk.Entry(main_frame, textvariable=self.photo_path, state=config.STATE_READONLY).grid(row=10, column=1, sticky="ew", pady=2)
        tk.Button(main_frame, text="Выбрать файл", command=self.select_photo).grid(row=10, column=2, padx=5)

        self.preview_label = tk.Label(main_frame, text="Предпросмотр")
        self.preview_label.grid(row=11, column=1, pady=5)

        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=12, column=0, columnspan=3, pady=10)
        tk.Button(btn_frame, text="Сохранить", command=self.save_product, bg=config.COLOR_ACCENT).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.on_close, bg=config.COLOR_EXTRA_BG).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def generate_article(self):
        cursor = self.app.db.conn.cursor()
        cursor.execute("SELECT article FROM products")
        existing = [row['article'] for row in cursor.fetchall()]
        max_num = 0
        for art in existing:
            match = re.search(r'[A-Za-z](\d{3})', art)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        next_num = max_num + 1
        new_article = f"A{next_num:03d}T4"
        while new_article in existing:
            next_num += 1
            new_article = f"A{next_num:03d}T4"
        return new_article

    def load_product_data(self):
        cursor = self.app.db.conn.cursor()
        cursor.execute("""
            SELECT p.*, cat.name as category_name, man.name as manufacturer_name, sup.name as supplier_name
            FROM products p
            LEFT JOIN categories cat ON p.category_id = cat.id
            LEFT JOIN manufacturers man ON p.manufacturer_id = man.id
            LEFT JOIN suppliers sup ON p.supplier_id = sup.id
            WHERE p.article = ?
        """, (self.article,))
        prod = cursor.fetchone()
        if prod:
            self.entry_article.config(state=config.STATE_NORMAL)
            self.entry_article.delete(0, tk.END)
            self.entry_article.insert(0, prod["article"])
            self.entry_article.config(state=config.STATE_READONLY)
            self.entry_name.insert(0, prod["name"] or "")
            self.combo_category.set(prod["category_name"] or "")
            self.combo_manufacturer.set(prod["manufacturer_name"] or "")
            self.combo_supplier.set(prod["supplier_name"] or "")
            self.entry_price.insert(0, prod["price"] or "")
            self.entry_unit.insert(0, prod["unit"] or "")
            self.entry_quantity.insert(0, prod["quantity"] or "")
            self.entry_discount.insert(0, prod["discount"] or "")
            self.text_description.insert(config.TEXT_START, prod["description"] or "")
            self.photo_path.set(prod["photo"] or "")
            self.update_preview()

    def select_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.photo_path.set(file_path)
            self.update_preview()

    def update_preview(self):
        path = self.photo_path.get()
        if path and os.path.exists(path):
            img = Image.open(path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
        else:
            self.preview_label.config(image="", text="Нет изображения")

    def _parse_and_validate_numbers(self, price_str, qty_str, disc_str):
        price = float(price_str)
        quantity = int(qty_str) if qty_str else 0
        discount = float(disc_str) if disc_str else 0
        if price < 0 or quantity < 0 or not (0 <= discount <= 100):
            raise ValueError
        return price, quantity, discount

    def _process_saved_image(self, article, photo_src):
        if not (photo_src and os.path.exists(photo_src)):
            return None
            
        ext = os.path.splitext(photo_src)[1]
        dest_path = os.path.join(config.IMAGE_FOLDER, f"{article}{ext}")
        
        if self.article:
            cursor = self.app.db.conn.cursor()
            cursor.execute("SELECT photo FROM products WHERE article=?", (self.article,))
            old_photo = cursor.fetchone()
            if old_photo and old_photo["photo"] and os.path.exists(old_photo["photo"]):
                os.remove(old_photo["photo"])
                
        img = Image.open(photo_src)
        img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        img.save(dest_path)
        return dest_path

    def _get_foreign_key(self, table, name):
        if not name:
            return None
        cursor = self.app.db.conn.cursor()
        queries = {
            "categories": ("SELECT id FROM categories WHERE name=?", "INSERT INTO categories (name) VALUES (?)"),
            "manufacturers": ("SELECT id FROM manufacturers WHERE name=?", "INSERT INTO manufacturers (name) VALUES (?)"),
            "suppliers": ("SELECT id FROM suppliers WHERE name=?", "INSERT INTO suppliers (name) VALUES (?)")
        }
        sel_q, ins_q = queries[table]
        cursor.execute(sel_q, (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute(ins_q, (name,))
        return cursor.lastrowid

    def save_product(self):
        article = self.entry_article.get().strip()
        name = self.entry_name.get().strip()
        category = self.combo_category.get().strip()
        manufacturer = self.combo_manufacturer.get().strip()
        supplier = self.combo_supplier.get().strip()
        price_str = self.entry_price.get().strip()
        unit = self.entry_unit.get().strip()
        qty_str = self.entry_quantity.get().strip()
        disc_str = self.entry_discount.get().strip()
        description = self.text_description.get(config.TEXT_START, tk.END).strip()
        photo_src = self.photo_path.get().strip()

        if not article or not name or not price_str:
            messagebox.showerror(config.TITLE_ERROR, "Заполните обязательные поля (артикул, наименование, цена)")
            return
            
        try:
            price, quantity, discount = self._parse_and_validate_numbers(price_str, qty_str, disc_str)
        except ValueError:
            messagebox.showerror(config.TITLE_ERROR, "Убедитесь, что цена и количество — положительные числа, а скидка от 0 до 100.")
            return

        final_photo_path = self._process_saved_image(article, photo_src)

        cat_id = self._get_foreign_key("categories", category)
        man_id = self._get_foreign_key("manufacturers", manufacturer)
        sup_id = self._get_foreign_key("suppliers", supplier)

        cursor = self.app.db.conn.cursor()
        if self.article:
            cursor.execute("""
                UPDATE products SET name=?, unit=?, price=?, category_id=?, manufacturer_id=?, supplier_id=?, discount=?, quantity=?, description=?, photo=?
                WHERE article=?
            """, (name, unit, price, cat_id, man_id, sup_id, discount, quantity, description, final_photo_path, self.article))
        else:
            cursor.execute("""
                INSERT INTO products (article, name, unit, price, category_id, manufacturer_id, supplier_id, discount, quantity, description, photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (article, name, unit, price, cat_id, man_id, sup_id, discount, quantity, description, final_photo_path))

        self.app.db.conn.commit()
        self.parent.load_products()
        self.on_close()

    def on_close(self):
        self.app.edit_window = None
        self.destroy()