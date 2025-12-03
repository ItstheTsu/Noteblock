import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import json
import os
import sys
import ctypes  # Para ícone no Windows

# --- Caminho para o ícone ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

icon_path = os.path.join(base_path, "icon.ico")
DATA_FILE = "dataBlock.json"

# --- Força ícone da barra de tarefas no Windows antes de criar a janela ---
if sys.platform == "win32":
    myappid = u"noteBlock.allan.1.0"  # ID único do app
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# ---------------- FUNÇÃO PARA DEFINIR ÍCONE ----------------
def set_window_icon(root, icon_path):
    try:
        root.iconbitmap(icon_path)
    except tk.TclError:
        pass


# ---------------- CLASSE DO BLOCO ----------------
class NoteBlock:
    def __init__(self, parent, app, text="", pinned_restore=False):
        self.parent = parent
        self.app = app
        self.pinned = pinned_restore

        self.frame = tk.Frame(parent, bg="#1e1e1e", bd=2, relief="solid")
        self.frame._instance = self 

        top_bar = tk.Frame(self.frame, bg="#2c2c2c")
        top_bar.pack(fill="x")

        self.pin_btn = tk.Button(
            top_bar,
            text="📌" if self.pinned else "📍",
            bg="#2c2c2c",
            fg="#4caf50" if self.pinned else "#d32f2f",
            bd=0,
            font=("Arial", 14),
            command=self.toggle_pin
        )
        self.pin_btn.pack(side="left", padx=5)

        self.save_btn = tk.Button(
            top_bar,
            text="💾",
            bg="#2c2c2c",
            fg="white",
            bd=0,
            font=("Arial", 12),
            command=self.save
        )
        self.save_btn.pack(side="left", padx=5)

        self.close_btn = tk.Button(
            top_bar,
            text="❌",
            bg="#2c2c2c",
            fg="#d32f2f",
            bd=0,
            font=("Arial", 12),
            command=self.delete
        )
        self.close_btn.pack(side="right", padx=5)

        self.text_widget = tk.Text(
            self.frame,
            height=6,
            bg="#252525",
            fg="#ffffff",
            insertbackground="white",
            wrap="word",
            padx=10,
            pady=10
        )
        self.text_widget.insert("1.0", text)
        self.text_widget.pack(fill="both", expand=True)

        self.insert_initial()

    def insert_initial(self):
        children = [c for c in self.parent.winfo_children() if isinstance(c, tk.Frame)]
        if self.pinned and children:
            self.frame.pack(fill="x", padx=15, pady=10, before=children[0])
        else:
            self.frame.pack(fill="x", padx=15, pady=10)

    def toggle_pin(self):
        self.pinned = not self.pinned
        self.pin_btn.config(
            text="📌" if self.pinned else "📍",
            fg="#4caf50" if self.pinned else "#d32f2f"
        )
        self.frame.pack_forget()
        children = [c for c in self.parent.winfo_children() if isinstance(c, tk.Frame) and c is not self.frame]
        if self.pinned:
            if children:
                self.frame.pack(fill="x", padx=15, pady=10, before=children[0])
            else:
                self.frame.pack(fill="x", padx=15, pady=10)
        else:
            self.frame.pack(fill="x", padx=15, pady=10)
        self.app.save_json()

    def save(self):
        try:
            file_path = fd.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Salvar bloco como..."
            )
        except Exception:
            file_path = None

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.text_widget.get("1.0", "end").rstrip("\n"))
            except Exception:
                pass
        self.app.save_json()

    def delete(self):
        self.frame.destroy()
        self.app.save_json()

    def get_data(self):
        return {
            "text": self.text_widget.get("1.0", "end").strip(),
            "pinned": self.pinned
        }


# ---------------- CLASSE PRINCIPAL ----------------
class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NoteBlock | Made by Allan Correa")
        self.root.geometry("500x620")
        self.root.configure(bg="#121212")
        self.root.attributes("-topmost", True)

        # --- Define ícone ---
        set_window_icon(self.root, icon_path)

        # TOPO FIXO (BOTÃO DE CRIAR)
        top_bar = tk.Frame(self.root, bg="#121212")
        top_bar.pack(fill="x")

        tk.Button(
            top_bar,
            text="Criar bloco (CTRL+N)",
            bg="#2c2c2c",
            fg="white",
            font=("Arial", 12),
            command=self.create_block
        ).pack(padx=10, pady=10, fill="x")

        # ÁREA SCROLLÁVEL
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill="both", expand=True)
        canvas_frame.pack_propagate(False)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#121212",
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        def _on_mousewheel(event):
            delta = 0
            if hasattr(event, 'delta') and event.delta:
                try:
                    delta = int(-1 * (event.delta / 120))
                except Exception:
                    delta = int(-1 * event.delta)
            if delta:
                self.canvas.yview_scroll(delta, 'units')

        def _on_button4(event):
            self.canvas.yview_scroll(-1, 'units')

        def _on_button5(event):
            self.canvas.yview_scroll(1, 'units')

        self.canvas.bind('<Enter>', lambda e: (
            self.canvas.bind_all('<MouseWheel>', _on_mousewheel),
            self.canvas.bind_all('<Button-4>', _on_button4),
            self.canvas.bind_all('<Button-5>', _on_button5)
        ))
        self.canvas.bind('<Leave>', lambda e: (
            self.canvas.unbind_all('<MouseWheel>'),
            self.canvas.unbind_all('<Button-4>'),
            self.canvas.unbind_all('<Button-5>')
        ))

        self.container = tk.Frame(self.canvas, bg="#121212")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")

        self.container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        # KEYBINDS
        self.root.bind("<Control-f>", self.open_search)
        self.root.bind("<Control-n>", lambda e: self.create_block())

        self.load_json()
        self.root.mainloop()

    def create_block(self):
        NoteBlock(self.container, self)
        self.save_json()

    def save_json(self):
        blocks_data = []
        for child in self.container.winfo_children():
            if isinstance(child, tk.Frame) and hasattr(child, "_instance"):
                blocks_data.append(child._instance.get_data())
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(blocks_data, f, indent=4)

    def load_json(self):
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return
        pinned = [b for b in data if b.get("pinned")]
        normal = [b for b in data if not b.get("pinned")]
        for blk in pinned + normal:
            NoteBlock(
                self.container,
                self,
                text=blk.get("text", ""),
                pinned_restore=blk.get("pinned", False)
            )

    def open_search(self, event=None):
        if hasattr(self, '_search_popup') and self._search_popup.winfo_exists():
            try:
                self._search_entry.focus_set()
            except:
                pass
            return

        popup = tk.Frame(self.root, bg="#1e1e1e", bd=1, relief="raised")
        self._search_popup = popup
        popup.place(relx=0.5, rely=0.02, anchor="n")

        tk.Label(popup, text="Buscar:", bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=6, pady=6)

        entry = tk.Entry(popup)
        entry.grid(row=0, column=1, padx=6, pady=6)
        entry.focus_set()
        self._search_entry = entry

        def do_search(event=None):
            query = entry.get().lower()
            for widget in self.container.winfo_children():
                if hasattr(widget, "_instance"):
                    widget._instance.text_widget.tag_remove("search", "1.0", "end")
                if not query:
                    return
                for widget in self.container.winfo_children():
                    if hasattr(widget, "_instance"):
                        block = widget._instance
                        txt = block.text_widget.get("1.0", "end").lower()
                        if query in txt:
                            start = "1.0"
                            while True:
                                pos = block.text_widget.search(query, start, stopindex="end")
                                if not pos:
                                    break
                                end = f"{pos}+{len(query)}c"
                                block.text_widget.tag_add("search", pos, end)
                                start = end
                        block.text_widget.tag_config("search", background="yellow", foreground="black")

        def close_search(event=None):
            for widget in self.container.winfo_children():
                if hasattr(widget, "_instance"):
                    widget._instance.text_widget.tag_remove("search", "1.0", "end")     
            popup.place_forget()     
            popup.destroy()

        entry.bind('<Return>', do_search)  
        popup.bind('<Escape>', close_search)
                
        tk.Button(popup, text="OK", command=do_search).grid(row=0, column=2, padx=4)
        tk.Button(popup, text="Fechar", command=close_search).grid(row=0, column=3, padx=4)

MainApp()