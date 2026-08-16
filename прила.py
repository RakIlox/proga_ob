import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfMerger
import threading

class PDFAppenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Добавление страницы в PDF")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Переменные для путей
        self.folder_path = tk.StringVar()
        self.append_file_path = tk.StringVar()
        self.output_folder_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Готов к работе")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        title_label = tk.Label(self.root, text="Добавление PDF-страницы в конец файлов", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Рамка для настроек
        settings_frame = tk.LabelFrame(self.root, text="Настройки", padx=10, pady=10)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Папка с файлами
        tk.Label(settings_frame, text="Папка с PDF-файлами:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(settings_frame, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=5)
        tk.Button(settings_frame, text="Выбрать", command=self.select_folder).grid(row=0, column=2)
        
        # Файл для добавления
        tk.Label(settings_frame, text="Файл для добавления:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(settings_frame, textvariable=self.append_file_path, width=50).grid(row=1, column=1, padx=5)
        tk.Button(settings_frame, text="Выбрать", command=self.select_append_file).grid(row=1, column=2)
        
        # Папка для результатов
        tk.Label(settings_frame, text="Папка для результатов:").grid(row=2, column=0, sticky="w", pady=5)
        tk.Entry(settings_frame, textvariable=self.output_folder_path, width=50).grid(row=2, column=1, padx=5)
        tk.Button(settings_frame, text="Выбрать", command=self.select_output_folder).grid(row=2, column=2)
        
        # Кнопка запуска
        self.process_button = tk.Button(self.root, text="▶ Начать обработку", 
                                       command=self.start_processing,
                                       font=("Arial", 12, "bold"),
                                       bg="#4CAF50", fg="white",
                                       padx=20, pady=10)
        self.process_button.pack(pady=20)
        
        # Статус
        status_label = tk.Label(self.root, textvariable=self.status_text, 
                               font=("Arial", 10), relief="sunken", anchor="w")
        status_label.pack(fill="x", padx=20, pady=5)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(self.root, orient="horizontal", 
                                        length=400, mode="determinate")
        self.progress.pack(pady=10)
        
        # Текстовое поле для лога
        self.log_text = tk.Text(self.root, height=8, font=("Consolas", 9))
        self.log_text.pack(fill="both", padx=20, pady=10, expand=True)
        
        # Скролл для лога
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
    def select_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с PDF-файлами")
        if folder:
            self.folder_path.set(folder)
            self.log(f"📁 Выбрана папка: {folder}")
    
    def select_append_file(self):
        file = filedialog.askopenfilename(
            title="Выберите PDF-файл для добавления",
            filetypes=[("PDF файлы", "*.pdf")]
        )
        if file:
            self.append_file_path.set(file)
            self.log(f"📄 Выбран файл: {os.path.basename(file)}")
    
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения результатов")
        if folder:
            self.output_folder_path.set(folder)
            self.log(f"📂 Папка для результатов: {folder}")
    
    def log(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()
    
    def start_processing(self):
        # Проверка заполнения всех полей
        if not all([self.folder_path.get(), self.append_file_path.get(), self.output_folder_path.get()]):
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        # Проверка существования файлов
        if not os.path.exists(self.append_file_path.get()):
            messagebox.showerror("Ошибка", "Файл для добавления не найден!")
            return
        
        if not os.path.exists(self.folder_path.get()):
            messagebox.showerror("Ошибка", "Папка с файлами не найдена!")
            return
        
        # Блокируем кнопку и запускаем в отдельном потоке
        self.process_button.config(state="disabled", text="⏳ Обработка...")
        self.progress["value"] = 0
        self.log("="*50)
        self.log("🚀 Начинаю обработку...")
        
        threading.Thread(target=self.process_files, daemon=True).start()
    
    def process_files(self):
        try:
            folder = self.folder_path.get()
            append_file = self.append_file_path.get()
            output_dir = self.output_folder_path.get()
            
            # Создаём папку для результатов
            os.makedirs(output_dir, exist_ok=True)
            
            # Собираем PDF-файлы
            pdf_files = []
            for file in os.listdir(folder):
                if file.lower().endswith('.pdf') and file != os.path.basename(append_file):
                    pdf_files.append(file)
            
            if not pdf_files:
                self.log("❌ В папке не найдено PDF-файлов для обработки")
                self.root.after(0, self.finish_processing)
                return
            
            total_files = len(pdf_files)
            self.log(f"✅ Найдено файлов: {total_files}")
            
            # Обрабатываем файлы
            for i, filename in enumerate(pdf_files, 1):
                input_path = os.path.join(folder, filename)
                output_path = os.path.join(output_dir, filename)
                
                try:
                    # Добавляем страницу
                    merger = PdfMerger()
                    merger.append(input_path)
                    merger.append(append_file)
                    merger.write(output_path)
                    merger.close()
                    
                    # Обновляем прогресс
                    progress = int((i / total_files) * 100)
                    self.root.after(0, self.update_progress, progress)
                    self.log(f"[{i}/{total_files}] ✅ {filename}")
                    
                except Exception as e:
                    self.log(f"[{i}/{total_files}] ❌ Ошибка в {filename}: {e}")
            
            self.log(f"\n✅ Готово! Все файлы сохранены в: {output_dir}")
            self.root.after(0, self.show_completion, total_files)
            
        except Exception as e:
            self.log(f"❌ Критическая ошибка: {e}")
        
        finally:
            self.root.after(0, self.finish_processing)
    
    def update_progress(self, value):
        self.progress["value"] = value
    
    def show_completion(self, total_files):
        messagebox.showinfo("Готово!", 
                           f"Обработано {total_files} файлов!\nРезультаты сохранены в выбранную папку.")
    
    def finish_processing(self):
        self.process_button.config(state="normal", text="▶ Начать обработку")
        self.status_text.set("Готов к работе")

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFAppenderApp(root)
    root.mainloop()
