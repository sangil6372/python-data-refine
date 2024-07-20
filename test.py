from pdf2image import convert_from_path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os


class PDFImageExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Image Extractor")

        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.menu = tk.Menu(root)
        self.root.config(menu=self.menu)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open PDF", command=self.open_pdf)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.cur_x = None
        self.cur_y = None
        self.images = []
        self.original_images = []
        self.current_image = None
        self.tk_image = None
        self.current_page = 0
        self.image_counter = 1
        self.scale_factor = 1.0

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.root.bind("<Left>", self.prev_page)
        self.root.bind("<Right>", self.next_page)

        self.image_folder = os.path.join(os.getcwd(), 'image')
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

    def open_pdf(self):
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not self.pdf_path:
            return
        self.load_images()

    def load_images(self):
        poppler_path = r'C:\Users\박상일\Downloads\Release-24.02.0-0\poppler-24.02.0\Library\bin'
        self.original_images = convert_from_path(self.pdf_path, dpi=300, poppler_path=poppler_path)
        self.images = [img.copy() for img in self.original_images]
        self.current_page = 0
        self.show_image()

    def show_image(self):
        if not self.images:
            return
        self.current_image = self.images[self.current_page]

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        img_width, img_height = self.current_image.size
        self.scale_factor = min(screen_width / img_width, screen_height / img_height)
        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)

        resized_image = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.root.geometry(f"{new_width}x{new_height}")

        self.redraw_rect()  # 화면 갱신할 때마다 사각형을 다시 그림

    def redraw_rect(self):
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.cur_x, self.cur_y, outline='red')

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_move_press(self, event):
        self.cur_x = self.canvas.canvasx(event.x)
        self.cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.cur_x, self.cur_y)

    def on_button_release(self, event):
        if self.rect:
            self.cur_x = self.canvas.canvasx(event.x)
            self.cur_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x, self.start_y, self.cur_x, self.cur_y)
            self.save_image_bbox()

    def save_image_bbox(self):
        if self.current_image is not None:
            canvas_width, canvas_height = self.tk_image.width(), self.tk_image.height()
            original_width, original_height = self.original_images[self.current_page].size

            # 현재 캔버스의 좌표를 원본 이미지의 좌표로 변환
            scale_x = original_width / canvas_width
            scale_y = original_height / canvas_height

            left = min(self.start_x, self.cur_x) * scale_x
            right = max(self.start_x, self.cur_x) * scale_x
            top = min(self.start_y, self.cur_y) * scale_y
            bottom = max(self.start_y, self.cur_y) * scale_y

            # 좌표를 int로 변환
            left = int(left)
            right = int(right)
            top = int(top)
            bottom = int(bottom)

            # 원본 이미지 크기의 바운딩 박스를 그대로 이미지로 저장
            bbox_image = self.original_images[self.current_page].crop((left, top, right, bottom))
            image_path = os.path.join(self.image_folder, f"Im{self.image_counter}.jpg")
            bbox_image.save(image_path)

            # A4 크기의 좌표로 변환하여 출력
            a4_width = 595
            a4_height = 842

            bbox_left = left * (a4_width / original_width)
            bbox_right = right * (a4_width / original_width)
            bbox_top = top * (a4_height / original_height)
            bbox_bottom = bottom * (a4_height / original_height)

            bbox_info = "<|img_start|>" + f"Image: Im{self.image_counter}, bbox: ({bbox_left}, {bbox_top}, {bbox_right}, {bbox_bottom})" + "<|img_end|>"
            print(bbox_info)
            messagebox.showinfo("BBox", bbox_info)
            self.image_counter += 1

    def prev_page(self, event):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_image()

    def next_page(self, event):
        if self.current_page < len(self.images) - 1:
            self.current_page += 1
            self.show_image()


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFImageExtractor(root)
    root.mainloop()