import os
import time
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageTk, ImageSequence, ImageDraw, ImageChops, ImageFilter, ImageFont
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from tkinterdnd2 import DND_FILES, TkinterDnD
import cv2
import numpy as np
import platform
import subprocess
import zipfile
import csv
import urllib.request
import urllib.parse

# Output folder
OUTPUT_FOLDER = "arshiya"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


class QRCodeStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro QR Code Studio - Ultimate V2.0")
        self.root.geometry("1000x680")
        self.root.resizable(False, False)

        # Variables
        self.image_path = None
        self.is_gif = False
        self.last_qr = None
        self.last_qr_is_gif = False
        self.last_qr_frames = None
        self.gif_durations = []
        self.last_svg_matrix = None
        
        # Styling Variables
        self.qr_fg_color = "#000000"
        self.qr_bg_color = "#FFFFFF"
        self.gradient_color = "#FF00FF"

        self.dark_mode = False
        self.style = ttk.Style()

        # Set default option database for combobox dropdown lists (helps with dark mode)
        self.root.option_add("*TCombobox*Listbox.background", "#ffffff")
        self.root.option_add("*TCombobox*Listbox.foreground", "#000000")
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#2196F3")
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        # --- UI Setup ---
        self.setup_ui()
        self.apply_theme() # Apply initial light theme forcefully
        
        # Drag & Drop binding
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def setup_ui(self):
        # Top Bar
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill="x", padx=10, pady=5)
        
        tk.Label(top_bar, text="Pro QR Code Studio", font=("Arial", 18, "bold")).pack(side="left", padx=10)
        
        self.dark_btn = tk.Button(top_bar, text="🌙 Dark Mode", command=self.toggle_dark_mode, font=("Arial", 10, "bold"))
        self.dark_btn.pack(side="right", padx=10)

        # Main Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.studio_tab = tk.Frame(self.notebook)
        self.batch_tab = tk.Frame(self.notebook)
        
        self.notebook.add(self.studio_tab, text="🎨 QR Studio")
        self.notebook.add(self.batch_tab, text="🚀 Batch Generator")
        
        self.setup_studio_tab()
        self.setup_batch_tab()

    # ================= THEME LOGIC =================
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def _safe_config(self, widget, **kwargs):
        """Applies configuration options one by one to prevent TclErrors from stopping the whole config."""
        for key, value in kwargs.items():
            try:
                widget.config({key: value})
            except tk.TclError:
                pass

    def apply_theme(self):
        if self.dark_mode:
            bg, fg = "#2b2b2b", "#ffffff"
            entry_bg = "#3c3c3c"
            btn_bg, btn_fg = "#4a4a4a", "#ffffff"
            status_fg = "#5599ff"
            gray_fg = "#a0a0a0" # Lighter gray for dark mode visibility
            self.dark_btn.config(text="☀️ Light Mode", bg=btn_bg, fg=btn_fg)
        else:
            bg, fg = "#f0f0f0", "#000000"
            entry_bg = "#ffffff"
            btn_bg, btn_fg = "#e1e1e1", "#000000"
            status_fg = "blue"
            gray_fg = "gray"
            self.dark_btn.config(text="🌙 Dark Mode", bg=btn_bg, fg=btn_fg)

        self.root.configure(bg=bg)
        
        # ttk styles
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=btn_bg, foreground=btn_fg)
        
        # Keep Comboboxes default so text doesn't disappear on Windows
        self.style.configure("TCombobox", fieldbackground="#ffffff", foreground="#000000", background=btn_bg, arrowcolor=fg)
        self.style.map("TCombobox", 
                       fieldbackground=[("readonly", "#ffffff")],
                       foreground=[("readonly", "#000000")],
                       background=[("active", btn_bg)])
        
        self.style.configure("TNotebook", background=bg, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=btn_bg, foreground=fg, padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", bg)], foreground=[("selected", fg)])

        self._style_widgets(self.root, bg, fg, entry_bg, btn_bg, btn_fg)
        
        # Fix specific custom things safely
        try:
            self.preview_label.config(bg=entry_bg, fg=gray_fg)
            self.status_label.config(fg=status_fg)
            self.batch_status.config(fg=status_fg)
            self.drop_label.config(fg=gray_fg)
            if self.image_label.cget('text') == "No image selected": self.image_label.config(fg=gray_fg)
            if self.csv_label.cget('text') == "No CSV selected": self.csv_label.config(fg=gray_fg)
            if self.batch_img_label.cget('text') == "No image selected": self.batch_img_label.config(fg=gray_fg)
        except AttributeError:
            pass

    def _style_widgets(self, widget, bg, fg, entry_bg, btn_bg, btn_fg):
        for child in widget.winfo_children():
            is_color_btn = (child == getattr(self, 'fg_btn', None) or 
                             child == getattr(self, 'bg_btn', None) or 
                             child == getattr(self, 'grad_btn', None))
            
            # Skip ttk widgets as they are handled by ttk.Style
            if isinstance(child, (ttk.Widget,)):
                self._style_widgets(child, bg, fg, entry_bg, btn_bg, btn_fg)
                continue
                
            if isinstance(child, tk.LabelFrame):
                self._safe_config(child, bg=bg, fg=fg)
            elif isinstance(child, tk.Label):
                self._safe_config(child, bg=bg, fg=fg)
            elif isinstance(child, tk.Frame):
                self._safe_config(child, bg=bg)
            elif isinstance(child, tk.Button):
                if is_color_btn:
                    self._safe_config(child, fg="white" if self._is_dark(child.cget('bg')) else "black")
                elif child.cget('bg').lower() in ["#4caf50", "#2196f3", "#ff9800", "#607d8b"]:
                    self._safe_config(child, fg="white")
                else:
                    self._safe_config(child, bg=btn_bg, fg=btn_fg)
            elif isinstance(child, tk.Entry):
                self._safe_config(child, bg=entry_bg, fg=fg, insertbackground=fg, readonlybackground=entry_bg)
            elif isinstance(child, tk.Text):
                self._safe_config(child, bg=entry_bg, fg=fg, insertbackground=fg)
            elif isinstance(child, tk.Scale):
                self._safe_config(child, bg=bg, fg=fg, troughcolor=entry_bg, highlightbackground=bg)
            elif isinstance(child, tk.Checkbutton):
                self._safe_config(child, bg=bg, fg=fg, selectcolor=entry_bg, activebackground=bg, activeforeground=fg)
            elif isinstance(child, tk.Canvas):
                self._safe_config(child, bg=bg, highlightbackground=bg)
                
            self._style_widgets(child, bg, fg, entry_bg, btn_bg, btn_fg)

    # ================= STUDIO TAB =================
    def setup_studio_tab(self):
        main_frame = tk.Frame(self.studio_tab)
        main_frame.pack(fill="both", expand=True, padx=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, anchor="n", padx=(0, 10))

        self.generate_button = tk.Button(left_frame, text="⚡ Generate QR Code", command=self.generate_qr,
                                         bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), pady=10)
        self.generate_button.pack(fill="x", pady=(0, 10))

        scroll_canvas = tk.Canvas(left_frame, width=400, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=scroll_canvas.yview)
        self.scrollable_frame = tk.Frame(scroll_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        )
        scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.bind_all("<MouseWheel>", lambda e: scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        self.populate_options()
        self.setup_right_frame(right_frame)

    def populate_options(self):
        parent = self.scrollable_frame

        # 1. QR Type & Content
        frame_content = tk.LabelFrame(parent, text="1. Content", padx=10, pady=5)
        frame_content.pack(fill="x", pady=2)

        tk.Label(frame_content, text="QR Type:").pack(anchor="w")
        self.qr_type_var = tk.StringVar(value="URL")
        type_box = ttk.Combobox(frame_content, textvariable=self.qr_type_var, state="readonly", width=20)
        type_box['values'] = ("URL", "Plain Text", "WiFi", "Contact (vCard)")
        type_box.pack(anchor="w", pady=2)
        type_box.bind("<<ComboboxSelected>>", self.update_content_fields)

        self.content_inputs = tk.Frame(frame_content)
        self.content_inputs.pack(fill="x", pady=5)
        self.update_content_fields()
        
        self.shorten_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_content, text="🔗 Smart Shorten Link (is.gd)", variable=self.shorten_var).pack(anchor="w", pady=2)

        # 2. Center Image
        frame_img = tk.LabelFrame(parent, text="2. Center Image / GIF", padx=10, pady=5)
        frame_img.pack(fill="x", pady=2)
        
        self.drop_label = tk.Label(frame_img, text="⬇ Drop Image / GIF Here ⬇\nor", fg="gray", font=("Arial", 9, "italic"))
        self.drop_label.pack(pady=2)
        
        self.image_button = tk.Button(frame_img, text="Browse Image / GIF", command=self.select_image, width=25)
        self.image_button.pack(pady=2)
        self.image_label = tk.Label(frame_img, text="No image selected", fg="gray", font=("Arial", 9))
        self.image_label.pack(pady=2)

        # 3. Center Styling
        frame_center = tk.LabelFrame(parent, text="3. Center Styling", padx=10, pady=5)
        frame_center.pack(fill="x", pady=2)

        tk.Label(frame_center, text="Image Size (%):").grid(row=0, column=0, sticky="w", pady=2)
        self.center_size_var = tk.IntVar(value=22)
        tk.Scale(frame_center, from_=10, to=35, orient=tk.HORIZONTAL, variable=self.center_size_var, length=150).grid(row=0, column=1, sticky="w")

        tk.Label(frame_center, text="Image Shape:").grid(row=1, column=0, sticky="w", pady=2)
        self.shape_var = tk.StringVar(value="Square")
        ttk.Combobox(frame_center, textvariable=self.shape_var, state="readonly", width=18, 
                     values=["Original", "Square", "Circle", "Rounded Square"]).grid(row=1, column=1, sticky="w")

        tk.Label(frame_center, text="Center BG:").grid(row=2, column=0, sticky="w", pady=2)
        self.bg_var = tk.StringVar(value="White")
        self.bg_box = ttk.Combobox(frame_center, textvariable=self.bg_var, state="readonly", width=18, 
                                   values=["None (Transparent)", "White", "Black", "Custom..."])
        self.bg_box.grid(row=2, column=1, sticky="w")
        self.bg_box.bind("<<ComboboxSelected>>", self.on_bg_change)

        self.drop_shadow_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_center, text="Enable Drop Shadow", variable=self.drop_shadow_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        # 4. QR Code Styling
        frame_qr = tk.LabelFrame(parent, text="4. QR Code Styling", padx=10, pady=5)
        frame_qr.pack(fill="x", pady=2)

        tk.Label(frame_qr, text="QR Size (px):").grid(row=0, column=0, sticky="w", pady=2)
        self.size_var = tk.IntVar(value=800)
        tk.Scale(frame_qr, from_=400, to=2000, orient=tk.HORIZONTAL, variable=self.size_var, length=150).grid(row=0, column=1, sticky="w")

        tk.Label(frame_qr, text="QR Shape:").grid(row=1, column=0, sticky="w", pady=2)
        self.module_var = tk.StringVar(value="Square")
        ttk.Combobox(frame_qr, textvariable=self.module_var, state="readonly", width=18, 
                     values=["Square", "Rounded", "Circle"]).grid(row=1, column=1, sticky="w")

        tk.Label(frame_qr, text="QR Colors:").grid(row=2, column=0, sticky="w", pady=5)
        color_frame = tk.Frame(frame_qr)
        color_frame.grid(row=2, column=1, sticky="w")
        
        self.fg_btn = tk.Button(color_frame, text="QR Color", command=self.pick_fg_color, bg=self.qr_fg_color, fg="white", width=8)
        self.fg_btn.pack(side="left", padx=2)
        
        self.bg_btn = tk.Button(color_frame, text="BG Color", command=self.pick_bg_color, bg=self.qr_bg_color, fg="black", width=8)
        self.bg_btn.pack(side="left", padx=2)

        self.gradient_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_qr, text="Gradient", variable=self.gradient_var, command=self.toggle_gradient).grid(row=3, column=0, sticky="w")
        self.grad_btn = tk.Button(frame_qr, text="Color 2", command=self.pick_grad_color, state=tk.DISABLED, width=8)
        self.grad_btn.grid(row=3, column=1, sticky="w", pady=2)

        # 5. CTA Frame
        frame_cta = tk.LabelFrame(parent, text="5. Call to Action Frame", padx=10, pady=5)
        frame_cta.pack(fill="x", pady=2)
        
        tk.Label(frame_cta, text="Frame Text:").grid(row=0, column=0, sticky="w", pady=2)
        self.cta_var = tk.StringVar(value="None")
        cta_box = ttk.Combobox(frame_cta, textvariable=self.cta_var, state="readonly", width=18, 
                               values=["None", "SCAN ME", "SCAN TO PAY", "SCAN FOR MENU", "Custom..."])
        cta_box.grid(row=0, column=1, sticky="w")
        cta_box.bind("<<ComboboxSelected>>", self.on_cta_change)
        
        self.cta_custom_label = tk.Label(frame_cta, text="Custom Text:")
        self.cta_custom_entry = tk.Entry(frame_cta, width=20)

    def on_cta_change(self, event=None):
        if self.cta_var.get() == "Custom...":
            self.cta_custom_label.grid(row=1, column=0, sticky="w", pady=2)
            self.cta_custom_entry.grid(row=1, column=1, sticky="w")
        else:
            self.cta_custom_label.grid_forget()
            self.cta_custom_entry.grid_forget()

    def setup_right_frame(self, right_frame):
        preview_frame = tk.LabelFrame(right_frame, text="Preview", padx=10, pady=10)
        preview_frame.pack(fill="both", expand=True)
        
        self.preview_label = tk.Label(preview_frame, text="Preview will appear here", fg="gray", relief="sunken", bd=1)
        self.preview_label.pack(fill="both", expand=True)

        action_frame = tk.Frame(right_frame)
        action_frame.pack(pady=10)

        self.download_button = tk.Button(action_frame, text="⬇ Save As...", command=self.download_qr,
                                         state=tk.DISABLED, bg="#2196F3", fg="white", font=("Arial", 11, "bold"), width=13)
        self.download_button.grid(row=0, column=0, padx=5)

        self.scan_button = tk.Button(action_frame, text="📷 Scan QR", command=self.scan_qr_code,
                                     bg="#FF9800", fg="white", font=("Arial", 11, "bold"), width=13)
        self.scan_button.grid(row=0, column=1, padx=5)

        self.folder_button = tk.Button(action_frame, text="📁 Open Folder", command=self.open_folder,
                                       bg="#607D8B", fg="white", font=("Arial", 11, "bold"), width=13)
        self.folder_button.grid(row=0, column=2, padx=5)

        self.status_label = tk.Label(right_frame, text="", fg="blue", wraplength=450, font=("Arial", 9))
        self.status_label.pack(pady=5)

    def update_content_fields(self, event=None):
        for widget in self.content_inputs.winfo_children():
            widget.destroy()
            
        qtype = self.qr_type_var.get()
        if qtype == "URL":
            tk.Label(self.content_inputs, text="URL:").pack(anchor="w")
            self.url_entry = tk.Entry(self.content_inputs, width=55)
            self.url_entry.pack(pady=2)
            self.url_entry.insert(0, "https://")
        elif qtype == "Plain Text":
            tk.Label(self.content_inputs, text="Text:").pack(anchor="w")
            self.text_input = tk.Text(self.content_inputs, width=55, height=3)
            self.text_input.pack(pady=2)
        elif qtype == "WiFi":
            tk.Label(self.content_inputs, text="SSID (Network Name):").pack(anchor="w")
            self.wifi_ssid = tk.Entry(self.content_inputs, width=55)
            self.wifi_ssid.pack(pady=2)
            tk.Label(self.content_inputs, text="Password:").pack(anchor="w")
            self.wifi_pass = tk.Entry(self.content_inputs, width=55)
            self.wifi_pass.pack(pady=2)
            tk.Label(self.content_inputs, text="Encryption:").pack(anchor="w")
            self.wifi_enc = ttk.Combobox(self.content_inputs, values=["WPA", "WEP", "None"], state="readonly", width=10)
            self.wifi_enc.set("WPA")
            self.wifi_enc.pack(anchor="w", pady=2)
        elif qtype == "Contact (vCard)":
            tk.Label(self.content_inputs, text="Full Name:").pack(anchor="w")
            self.vcard_name = tk.Entry(self.content_inputs, width=55)
            self.vcard_name.pack(pady=2)
            tk.Label(self.content_inputs, text="Phone:").pack(anchor="w")
            self.vcard_phone = tk.Entry(self.content_inputs, width=55)
            self.vcard_phone.pack(pady=2)
            tk.Label(self.content_inputs, text="Email:").pack(anchor="w")
            self.vcard_email = tk.Entry(self.content_inputs, width=55)
            self.vcard_email.pack(pady=2)
            
        # Reapply theme to style newly created widgets
        self.apply_theme()

    def get_qr_data(self):
        qtype = self.qr_type_var.get()
        raw_data = ""
        if qtype == "URL":
            raw_data = self.url_entry.get().strip()
            if self.shorten_var.get() and raw_data:
                self.status_label.config(text="🔗 Shortening link...")
                self.root.update()
                raw_data = self.shorten_url(raw_data)
                self.status_label.config(text="✓ Link shortened!")
        elif qtype == "Plain Text":
            raw_data = self.text_input.get("1.0", tk.END).strip()
        elif qtype == "WiFi":
            ssid = self.wifi_ssid.get().strip()
            password = self.wifi_pass.get().strip()
            enc = self.wifi_enc.get()
            raw_data = f"WIFI:T:{enc};S:{ssid};P:{password};;"
        elif qtype == "Contact (vCard)":
            name = self.vcard_name.get().strip()
            phone = self.vcard_phone.get().strip()
            email = self.vcard_email.get().strip()
            raw_data = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL:{phone}\nEMAIL:{email}\nEND:VCARD"
        return raw_data

    def shorten_url(self, url):
        try:
            api_url = f"https://is.gd/create.php?format=simple&url={urllib.parse.quote(url)}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            return urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
        except:
            return url # Fallback to long URL if API fails

    # ================= BATCH TAB =================
    def setup_batch_tab(self):
        tk.Label(self.batch_tab, text="Batch QR Generator", font=("Arial", 18, "bold")).pack(pady=10)
        tk.Label(self.batch_tab, text="Upload a CSV file (Column 1: Link, Column 2: Filename).\nGenerates a ZIP file of QR codes.", font=("Arial", 10), fg="gray").pack(pady=5)

        batch_frame = tk.LabelFrame(self.batch_tab, text="Settings", padx=20, pady=20)
        batch_frame.pack(pady=10)

        tk.Button(batch_frame, text="1. Select CSV File", command=self.select_csv, width=25, bg="#2196F3", fg="white", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=10)
        self.csv_label = tk.Label(batch_frame, text="No CSV selected", fg="gray")
        self.csv_label.grid(row=0, column=1, sticky="w")

        tk.Button(batch_frame, text="2. Select Center Image (Optional)", command=self.select_batch_image, width=25, font=("Arial", 11, "bold")).grid(row=1, column=0, padx=10, pady=10)
        self.batch_img_label = tk.Label(batch_frame, text="No image selected", fg="gray")
        self.batch_img_label.grid(row=1, column=1, sticky="w")

        tk.Label(batch_frame, text="Image Size (%):").grid(row=2, column=0, sticky="e")
        self.batch_size_var = tk.IntVar(value=20)
        tk.Scale(batch_frame, from_=10, to=30, orient=tk.HORIZONTAL, variable=self.batch_size_var, length=100).grid(row=2, column=1, sticky="w")

        tk.Button(self.batch_tab, text="🚀 Generate ZIP", command=self.run_batch, bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), padx=20, pady=10).pack(pady=20)
        self.batch_status = tk.Label(self.batch_tab, text="", fg="blue")
        self.batch_status.pack()

    def select_csv(self):
        filepath = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.csv_path = filepath
            self.csv_label.config(text=os.path.basename(filepath), fg="green")

    def select_batch_image(self):
        filepath = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if filepath:
            self.batch_img_path = filepath
            self.batch_img_label.config(text=os.path.basename(filepath), fg="green")

    def run_batch(self):
        if not hasattr(self, 'csv_path'):
            messagebox.showerror("Error", "Please select a CSV file.")
            return

        zip_path = filedialog.asksaveasfilename(title="Save ZIP As", defaultextension=".zip", filetypes=[("ZIP File", "*.zip")], initialdir=os.path.abspath(OUTPUT_FOLDER))
        if not zip_path: return

        self.batch_status.config(text="Processing... This may take a moment.")
        self.root.update()

        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, row in enumerate(rows):
                    if len(row) < 1: continue
                    link = row[0].strip()
                    filename = row[1].strip() if len(row) > 1 else f"qr_{i+1}"
                    if not filename.endswith('.png'): filename += '.png'

                    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=4)
                    qr.add_data(link)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
                    
                    if hasattr(self, 'batch_img_path'):
                        center_size = int(800 * self.batch_size_var.get() / 100)
                        center_img = Image.open(self.batch_img_path).convert("RGBA").resize((center_size, center_size), Image.LANCZOS)
                        bg = Image.new("RGBA", (center_size+24, center_size+24), (255,255,255,255))
                        pos = ((800 - center_size) // 2, (800 - center_size) // 2)
                        bg_pos = ((800 - (center_size+24)) // 2, (800 - (center_size+24)) // 2)
                        img = img.resize((800, 800), Image.NEAREST)
                        img.paste(bg, bg_pos, bg)
                        img.paste(center_img, pos, center_img)

                    img = img.resize((800, 800), Image.LANCZOS)
                    
                    import io
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zipf.writestr(filename, img_byte_arr.getvalue())

            self.batch_status.config(text=f"✓ Success! {len(rows)} QR codes saved to ZIP.")
            messagebox.showinfo("Success", f"Batch generated successfully!\nSaved to:\n{zip_path}")
        except Exception as e:
            self.batch_status.config(text="✗ Error during batch processing.")
            messagebox.showerror("Error", str(e))

    # ================= CORE LOGIC =================
    def toggle_gradient(self):
        if self.gradient_var.get():
            self.grad_btn.config(state=tk.NORMAL)
        else:
            self.grad_btn.config(state=tk.DISABLED)

    def on_drop(self, event):
        file_path = event.data.strip()
        if file_path.startswith('{') and file_path.endswith('}'): file_path = file_path[1:-1]
            
        valid_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        if not any(file_path.lower().endswith(ext) for ext in valid_exts):
            messagebox.showerror("Error", "Please drop a valid image or GIF file.")
            return
            
        self.image_path = file_path
        self.is_gif = file_path.lower().endswith('.gif')
        label_text = f"✓ {os.path.basename(file_path)}"
        if self.is_gif: label_text += "  (GIF)"
        self.image_label.config(text=label_text, fg="green")
        self.drop_label.config(text="✓ Image Loaded!\nDrag & Drop to replace")

    def select_image(self):
        file_path = filedialog.askopenfilename(title="Select Image or GIF", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All files", "*.*")])
        if file_path:
            self.image_path = file_path
            self.is_gif = file_path.lower().endswith('.gif')
            label_text = f"✓ {os.path.basename(file_path)}"
            if self.is_gif: label_text += "  (GIF)"
            self.image_label.config(text=label_text, fg="green")
            self.drop_label.config(text="✓ Image Loaded!\nDrag & Drop to replace")

    def pick_fg_color(self):
        color = colorchooser.askcolor(title="Choose QR Code Color", initialcolor=self.qr_fg_color)
        if color[1]:
            self.qr_fg_color = color[1]
            self.fg_btn.config(bg=self.qr_fg_color, fg="white" if self._is_dark(self.qr_fg_color) else "black")

    def pick_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background Color", initialcolor=self.qr_bg_color)
        if color[1]:
            self.qr_bg_color = color[1]
            self.bg_btn.config(bg=self.qr_bg_color, fg="white" if self._is_dark(self.qr_bg_color) else "black")

    def pick_grad_color(self):
        color = colorchooser.askcolor(title="Choose Gradient Color", initialcolor=self.gradient_color)
        if color[1]:
            self.gradient_color = color[1]
            self.grad_btn.config(bg=self.gradient_color, fg="white" if self._is_dark(self.gradient_color) else "black")

    def _is_dark(self, hex_color):
        if not hex_color.startswith('#') or len(hex_color) != 7: return False
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        return (r * 0.299 + g * 0.587 + b * 0.114) < 128

    def on_bg_change(self, event):
        if self.bg_var.get() == "Custom...":
            color = colorchooser.askcolor(title="Choose background color")
            if color[1]: self.bg_var.set(color[1])
            else: self.bg_var.set("White")

    def generate_qr(self):
        data = self.get_qr_data()
        if not data:
            messagebox.showerror("Error", "Please enter data for the QR code")
            return

        if self.center_size_var.get() > 25:
            if not messagebox.askyesno("Warning", "Center image size is >25%. This might make the QR code hard to scan.\n\nContinue anyway?"):
                return

        self.status_label.config(text="Generating QR code... please wait")
        self.root.update()

        try:
            if self.is_gif:
                frames = self.create_gif_qr(data)
                self.last_qr_frames = frames
                self.last_qr_is_gif = True
                preview = frames[0].copy().convert("RGB")
                preview.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(preview)
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo
                self.status_label.config(text=f"✓ Generated GIF QR Code with {len(frames)} frames")
            else:
                qr_img = self.create_static_qr(data)
                self.last_qr = qr_img
                self.last_qr_is_gif = False
                preview = qr_img.copy()
                preview.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(preview)
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo
                self.status_label.config(text="✓ Generated QR Code")

            self.download_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate QR code:\n{str(e)}")
            self.status_label.config(text="✗ Generation failed")

    def apply_cta_frame(self, qr_img):
        cta_choice = self.cta_var.get()
        if cta_choice == "None":
            return qr_img
            
        text = cta_choice
        if cta_choice == "Custom...":
            text = self.cta_custom_entry.get().strip() or "SCAN ME"
            
        try:
            font = ImageFont.truetype("arial.ttf", int(qr_img.width * 0.07))
        except:
            font = ImageFont.load_default()
            
        pad = int(qr_img.width * 0.04)
        bar_h = int(qr_img.width * 0.12)
        
        new_w = qr_img.width + pad * 2
        new_h = qr_img.height + pad * 2 + bar_h
        
        frame_img = Image.new("RGBA", (new_w, new_h), self.qr_bg_color)
        draw = ImageDraw.Draw(frame_img)
        
        frame_img.paste(qr_img, (pad, pad), qr_img)
        draw.rectangle([0, 0, new_w-1, new_h-1], outline=self.qr_fg_color, width=int(qr_img.width*0.01))
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = (new_w - text_w) // 2
        text_y = qr_img.height + pad + (bar_h - text_h) // 2
        draw.text((text_x, text_y), text, fill=self.qr_fg_color, font=font)
        
        return frame_img

    def create_qr_base(self, url, qr_size):
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        self.last_svg_matrix = qr.modules
        
        matrix = qr.modules
        matrix_size = len(matrix)
        box_size = 10
        base_size = matrix_size * box_size
        
        img = Image.new("RGBA", (base_size, base_size), self.qr_bg_color)
        shape = self.module_var.get()
        
        qr_mask = Image.new("L", (base_size, base_size), 0)
        draw_mask = ImageDraw.Draw(qr_mask)
        
        for y in range(matrix_size):
            for x in range(matrix_size):
                if matrix[y][x]:
                    x0, y0 = x * box_size, y * box_size
                    x1, y1 = x0 + box_size, y0 + box_size
                    if shape == "Rounded":
                        draw_mask.rounded_rectangle([x0, y0, x1, y1], radius=box_size//3, fill=255)
                    elif shape == "Circle":
                        padding = box_size // 6
                        draw_mask.ellipse([x0+padding, y0+padding, x1-padding, y1-padding], fill=255)
                    else:
                        draw_mask.rectangle([x0, y0, x1, y1], fill=255)

        if self.gradient_var.get():
            grad = Image.new("RGB", (base_size, base_size), self.qr_fg_color)
            top = Image.new("RGB", (base_size, base_size), self.gradient_color)
            grad_mask = Image.new("L", (1, base_size))
            for y in range(base_size):
                grad_mask.putpixel((0, y), int(255 * (y / base_size)))
            grad_mask = grad_mask.resize((base_size, base_size))
            grad.paste(top, (0,0), grad_mask)
            img.paste(grad, (0,0), qr_mask)
        else:
            fill_img = Image.new("RGBA", (base_size, base_size), self.qr_fg_color)
            img.paste(fill_img, (0,0), qr_mask)
                        
        img = img.resize((qr_size, qr_size), Image.LANCZOS)
        return img

    def apply_shape_mask(self, img, shape, size):
        if shape == "Original": return img
            
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        if shape == "Circle": draw.ellipse((0, 0, size, size), fill=255)
        elif shape == "Rounded Square": draw.rounded_rectangle((0, 0, size, size), radius=size // 5, fill=255)
        else: draw.rectangle((0, 0, size, size), fill=255)

        if img.mode == 'RGBA':
            original_alpha = img.split()[3]
            combined_alpha = ImageChops.multiply(original_alpha, mask)
            img.putalpha(combined_alpha)
        else:
            img.putalpha(mask)
        return img

    def paste_center(self, qr_img, center_img_rgba, qr_size, center_size, shape, bg_choice):
        if bg_choice != "None (Transparent)":
            bg_padding = 12
            bg_size = center_size + (bg_padding * 2)
            if bg_choice == "White": bg_color = (255, 255, 255, 255)
            elif bg_choice == "Black": bg_color = (0, 0, 0, 255)
            elif bg_choice.startswith("#"):
                h = bg_choice.lstrip('#')
                rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                bg_color = (*rgb, 255)
            else: bg_color = (255, 255, 255, 255)

            bg = Image.new("RGBA", (bg_size, bg_size), bg_color)
            bg_shape = shape if shape != "Original" else "Square"
            bg = self.apply_shape_mask(bg, bg_shape, bg_size)
            bg_pos = ((qr_size - bg_size) // 2, (qr_size - bg_size) // 2)
            qr_img.paste(bg, bg_pos, bg)

        pos = ((qr_size - center_size) // 2, (qr_size - center_size) // 2)
        
        if self.drop_shadow_var.get():
            shadow = Image.new("RGBA", center_img_rgba.size, (0,0,0,0))
            shadow_alpha = center_img_rgba.split()[3]
            shadow_black = Image.new("RGBA", center_img_rgba.size, (0,0,0,180))
            shadow.paste(shadow_black, mask=shadow_alpha)
            shadow = shadow.filter(ImageFilter.GaussianBlur(5))
            qr_img.paste(shadow, (pos[0]+4, pos[1]+5), shadow)
            
        qr_img.paste(center_img_rgba, pos, center_img_rgba)

    def create_static_qr(self, url):
        qr_size = self.size_var.get()
        center_size = int(qr_size * self.center_size_var.get() / 100)
        shape = self.shape_var.get()
        bg_choice = self.bg_var.get()

        qr_img = self.create_qr_base(url, qr_size)
        
        if self.image_path:
            center_img = Image.open(self.image_path).convert("RGBA")
            center_img = center_img.resize((center_size, center_size), Image.LANCZOS)
            center_img = self.apply_shape_mask(center_img, shape, center_size)
            self.paste_center(qr_img, center_img, qr_size, center_size, shape, bg_choice)
            
        qr_img = self.apply_cta_frame(qr_img)
        return qr_img

    def create_gif_qr(self, url):
        qr_size = self.size_var.get()
        center_size = int(qr_size * self.center_size_var.get() / 100)
        shape = self.shape_var.get()
        bg_choice = self.bg_var.get()

        gif = Image.open(self.image_path)
        frames = []
        durations = []

        for frame in ImageSequence.Iterator(gif):
            durations.append(frame.info.get('duration', 100))
            qr_img = self.create_qr_base(url, qr_size)
            frame_img = frame.copy().convert("RGBA").resize((center_size, center_size), Image.LANCZOS)
            frame_img = self.apply_shape_mask(frame_img, shape, center_size)
            self.paste_center(qr_img, frame_img, qr_size, center_size, shape, bg_choice)
            
            qr_img = self.apply_cta_frame(qr_img)
            frames.append(qr_img)

        self.gif_durations = durations
        return frames

    def export_svg(self, filepath):
        if not self.last_svg_matrix: return
        matrix = self.last_svg_matrix
        size = len(matrix)
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">'
        svg += f'<rect width="{size}" height="{size}" fill="{self.qr_bg_color}"/>'
        
        if self.gradient_var.get():
            svg += '<defs><linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">'
            svg += f'<stop offset="0%" style="stop-color:{self.qr_fg_color}"/>'
            svg += f'<stop offset="100%" style="stop-color:{self.gradient_color}"/>'
            svg += '</linearGradient></defs>'
            fill_color = "url(#grad)"
        else:
            fill_color = self.qr_fg_color

        shape = self.module_var.get()
        for y in range(size):
            for x in range(size):
                if matrix[y][x]:
                    if shape == "Rounded":
                        svg += f'<rect x="{x}" y="{y}" width="1" height="1" rx="0.3" ry="0.3" fill="{fill_color}"/>'
                    elif shape == "Circle":
                        svg += f'<circle cx="{x+0.5}" cy="{y+0.5}" r="0.4" fill="{fill_color}"/>'
                    else:
                        svg += f'<rect x="{x}" y="{y}" width="1" height="1" fill="{fill_color}"/>'
        svg += '</svg>'
        
        with open(filepath, "w") as f:
            f.write(svg)

    def export_print_pdf(self, filepath):
        orig_size = self.size_var.get()
        self.size_var.set(2000)
        high_res_qr = self.create_static_qr(self.get_qr_data())
        self.size_var.set(orig_size)
        
        a4_w, a4_h = 2480, 3508
        pdf_img = Image.new("RGB", (a4_w, a4_h), "white")
        
        qr_w, qr_h = high_res_qr.size
        pdf_img.paste(high_res_qr, ((a4_w - qr_w)//2, (a4_h - qr_h)//2), high_res_qr)
        
        draw = ImageDraw.Draw(pdf_img)
        mark_len = 50
        margin = 150
        c_x1 = (a4_w - qr_w)//2 - margin
        c_y1 = (a4_h - qr_h)//2 - margin
        c_x2 = (a4_w + qr_w)//2 + margin
        c_y2 = (a4_h + qr_h)//2 + margin
        
        draw.line([c_x1, c_y1, c_x1+mark_len, c_y1], fill="black", width=3)
        draw.line([c_x1, c_y1, c_x1, c_y1+mark_len], fill="black", width=3)
        draw.line([c_x2, c_y1, c_x2-mark_len, c_y1], fill="black", width=3)
        draw.line([c_x2, c_y1, c_x2, c_y1+mark_len], fill="black", width=3)
        draw.line([c_x1, c_y2, c_x1+mark_len, c_y2], fill="black", width=3)
        draw.line([c_x1, c_y2, c_x1, c_y2-mark_len], fill="black", width=3)
        draw.line([c_x2, c_y2, c_x2-mark_len, c_y2], fill="black", width=3)
        draw.line([c_x2, c_y2, c_x2, c_y2-mark_len], fill="black", width=3)
        
        pdf_img.save(filepath, "PDF", resolution=300.0)

    def download_qr(self):
        filetypes = [("PNG Image", "*.png"), ("SVG Vector", "*.svg"), ("PDF Document", "*.pdf")]
        default_ext = ".png"

        if self.last_qr_is_gif:
            filetypes = [("GIF Image", "*.gif")]
            default_ext = ".gif"

        filepath = filedialog.asksaveasfilename(title="Save QR Code As", filetypes=filetypes, defaultextension=default_ext, initialdir=os.path.abspath(OUTPUT_FOLDER), initialfile=f"qr_code_{time.strftime('%Y%m%d_%H%M%S')}")
        if not filepath: return

        try:
            if filepath.endswith('.svg'):
                if self.image_path:
                    messagebox.showwarning("SVG Note", "SVG export saves only the vector QR code (no center image) for infinite scaling.")
                self.export_svg(filepath)
            elif filepath.endswith('.pdf'):
                if self.last_qr_is_gif:
                    messagebox.showwarning("PDF Note", "PDF export does not support GIFs. Generating static PDF.")
                self.export_print_pdf(filepath)
            elif self.last_qr_is_gif:
                frames_p = [f.convert("RGB").convert("P", palette=Image.ADAPTIVE) for f in self.last_qr_frames]
                frames_p[0].save(filepath, save_all=True, append_images=frames_p[1:], loop=0, duration=self.gif_durations, disposal=2)
            else:
                self.last_qr.save(filepath)
            
            self.status_label.config(text=f"✓ Saved to: {filepath}")
            messagebox.showinfo("Success", f"QR Code saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{str(e)}")

    def open_folder(self):
        path = os.path.abspath(OUTPUT_FOLDER)
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{str(e)}")

    # ================= IMAGE SCAN LOGIC =================
    def scan_qr_code(self):
        scan_preview = messagebox.askyesno("Scan QR", "Do you want to scan the QR code currently displayed in the preview?\n\n(Click 'No' to select an image file from your computer instead.)")
        
        img_to_scan = None
        if scan_preview:
            if not self.last_qr:
                messagebox.showerror("Error", "No QR code has been generated yet to scan.")
                return
            img_array = np.array(self.last_qr.convert('RGB'))
            img_to_scan = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            file_path = filedialog.askopenfilename(title="Select QR Image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.webp")])
            if not file_path: return
            img_to_scan = cv2.imread(file_path)

        self.status_label.config(text="📷 Scanning image... please wait.")
        self.root.update()

        data = self._attempt_cv2_scan(img_to_scan)
        
        if data:
            self._on_qr_scanned(data)
        else:
            self.status_label.config(text="✗ Scan failed.")
            messagebox.showerror("Scan Failed", "Could not read a QR code. Note: The internal scanner may still struggle if the center logo is very large, even though phones can read it perfectly.")

    def _attempt_cv2_scan(self, img):
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data: return data
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        data, _, _ = detector.detectAndDecode(gray)
        if data: return data
        
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        data, _, _ = detector.detectAndDecode(otsu)
        if data: return data
        
        kernel = np.ones((5,5), np.uint8)
        closed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        data, _, _ = detector.detectAndDecode(closed)
        if data: return data
        
        h, w = otsu.shape[:2]
        if max(h, w) < 800:
            otsu_resized = cv2.resize(otsu, (w*2, h*2), interpolation=cv2.INTER_NEAREST)
            data, _, _ = detector.detectAndDecode(otsu_resized)
            if data: return data
            
        return ""

    def _on_qr_scanned(self, data):
        self.qr_type_var.set("URL")
        self.update_content_fields()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, data)
        self.status_label.config(text="✓ Scanned successfully! Link loaded into URL field.")
        messagebox.showinfo("QR Code Scanned", f"Found link:\n{data}")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = QRCodeStudio(root)
    root.mainloop()
