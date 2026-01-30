import tkinter as tk
import math


class LoadingOverlay(tk.Frame):
    def __init__(self, parent, colors):
        super().__init__(parent, bg=colors["bg_main"])
        self.colors = colors
        self.angle = 0
        self.is_running = False
        self.job_id = None

        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

        self.canvas = tk.Canvas(
            self,
            width=100,
            height=100,
            bg=self.colors["bg_main"],
            highlightthickness=0
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        self.label = tk.Label(
            self,
            text="Carregando Vocabulário...",
            font=("Segoe UI", 12),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"]
        )
        self.label.place(relx=0.5, rely=0.6, anchor="center")

        self.withdraw()

    def draw_spinner(self):
        self.canvas.delete("all")
        x, y, r = 50, 50, 30
        extent = 120
        start = self.angle

        self.canvas.create_arc(
            x-r, y-r, x+r, y+r,
            start=start, extent=extent,
            style="arc", width=6, outline=self.colors["accent"]
        )

        self.canvas.create_arc(
            x-r, y-r, x+r, y+r,
            start=start+180, extent=extent,
            style="arc", width=6, outline=self.colors["accent_hover"]
        )

        self.angle = (self.angle + 10) % 360

    def animate(self):
        if self.is_running:
            self.draw_spinner()
            self.job_id = self.after(30, self.animate)

    def show(self, message="Processando..."):
        self.label.config(text=message)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.is_running = True
        self.animate()

    def hide(self):
        self.is_running = False
        if self.job_id:
            self.after_cancel(self.job_id)
        self.place_forget()

    def withdraw(self):
        self.place_forget()
