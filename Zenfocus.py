import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import webbrowser
from datetime import date

# --- Configuration ---
COLORS = {
    "bg_window": "#1c1c1c",
    "bg_sidebar": "#252525",
    "bg_card": "#333333",
    "accent": "#7aa095",
    "accent_hover": "#5d7a71",
    "text_main": "#ffffff",
    "text_dim": "#a5a5a5",
    "danger": "#e57373",
}

DATA_FILE = "zenfocus_data.json"
DEFAULT_NOTES = "Use this space to clear your mind..."


class ZenFocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Setup Window
        self.title("ZenFocus Pro")
        self.geometry("700x500")
        self.configure(fg_color=COLORS["bg_window"])
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 2. Initialize State Variables 
        self.current_view = "Timer"
        self.timer_running = False
        self.timer_seconds = 25 * 60
        self.initial_time = 25 * 60
        self.timer_mode = "Focus"
        self.sessions_completed = 0
        self.tasks = []
        self.notes_content = DEFAULT_NOTES
        self.links = []
        self.last_date = ""

        # 3. Load Data
        self.load_data()

        # 4. Setup UI Layout
        self.setup_sidebar()

        # Main content area
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True)

        # 5. Show Initial View
        self.show_timer_view()

    # --- Data Persistence ---

    def load_data(self):
        """Loads data into 'self' attributes."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)

                    self.sessions_completed = data.get("sessions_completed", 0)
                    self.tasks = data.get("tasks", [])
                    self.notes_content = data.get("notes_content", DEFAULT_NOTES)
                    self.links = data.get("links", [])
                    self.last_date = data.get("last_date", "")

                    # Daily Reset Logic
                    today = str(date.today())
                    if self.last_date != today:
                        self.sessions_completed = 0
                        self.last_date = today

                    self.timer_seconds = self.initial_time
            except Exception as e:
                print(f"Error loading: {e}")

    def save_data(self):
        """Bundles 'self' attributes into a dictionary just for saving."""
        # Capture notes if we are currently looking at them
        if self.current_view == "Notes" and hasattr(self, 'text_notes'):
            self.notes_content = self.text_notes.get("1.0", "end-1c")

        data_to_save = {
            "sessions_completed": self.sessions_completed,
            "tasks": self.tasks,
            "notes_content": self.notes_content,
            "links": self.links,
            "last_date": self.last_date
        }

        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(f"Error saving: {e}")

    def on_closing(self):
        self.save_data()
        self.destroy()

    # --- UI Helpers ---

    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(sidebar, text="ZenFocus", font=("Roboto", 20, "bold"),
                     text_color=COLORS["accent"]).pack(pady=(30, 30))

        # Helper to make sidebar buttons
        def create_btn(text, icon, view_name):
            ctk.CTkButton(sidebar, text=f"{icon}  {text}", anchor="w", fg_color="transparent",
                          text_color=COLORS["text_main"], hover_color=COLORS["bg_card"],
                          height=40, font=("Roboto", 14),
                          command=lambda: self.change_view(view_name)).pack(fill="x", padx=10, pady=5)

        create_btn("Timer", "⏱", "Timer")
        create_btn("Tasks", "✅", "Tasks")
        create_btn("Notes", "📝", "Notes")
        create_btn("Links", "🔗", "Links")

    def change_view(self, view_name):
        if self.current_view == "Notes":
            self.save_data()  # Save notes before switching

        self.current_view = view_name

        if view_name == "Timer":
            self.show_timer_view()
        elif view_name == "Tasks":
            self.show_tasks_view()
        elif view_name == "Notes":
            self.show_notes_view()
        elif view_name == "Links":
            self.show_links_view()

    # --- Timer Logic & View ---

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def update_timer_ui(self):
        self.lbl_timer.configure(text=self.format_time(self.timer_seconds))
        self.progress_bar.set(self.timer_seconds / self.initial_time)

    def timer_countdown(self):
        if self.timer_running and self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.update_timer_ui()
            self.after(1000, self.timer_countdown) # 'after' is a method of the class now
        elif self.timer_seconds == 0:
            self.timer_running = False
            self.btn_toggle.configure(text="Start Focus", fg_color=COLORS["accent"])

            if self.timer_mode == "Focus":
                self.sessions_completed += 1
                self.lbl_stats.configure(text=f"Sessions Completed: {self.sessions_completed}")
                self.save_data()
                messagebox.showinfo("ZenFocus", "Focus session complete!")
            else:
                messagebox.showinfo("ZenFocus", "Break over!")

            self.reset_timer()

    def toggle_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.btn_toggle.configure(text="Pause", fg_color=COLORS["text_dim"])
            self.timer_countdown()
        else:
            self.timer_running = False
            self.btn_toggle.configure(text="Resume", fg_color=COLORS["accent"])

    def reset_timer(self):
        self.timer_running = False
        self.timer_seconds = self.initial_time
        self.btn_toggle.configure(text="Start", fg_color=COLORS["accent"])
        self.update_timer_ui()
        self.progress_bar.set(1.0)

    def set_mode(self, mode, minutes):
        self.timer_mode = mode
        self.initial_time = minutes * 60
        self.reset_timer()
        self.lbl_mode.configure(text=mode)

    def show_timer_view(self):
        self.clear_main_area()

        ctk.CTkLabel(self.main_area, text="⏱ Focus Timer", font=("Roboto", 24, "bold")).pack(pady=(30, 10))

        self.lbl_stats = ctk.CTkLabel(self.main_area, text=f"Sessions Completed: {self.sessions_completed}",
                                      text_color=COLORS["text_dim"])
        self.lbl_stats.pack(pady=(0, 20))

        card = ctk.CTkFrame(self.main_area, fg_color=COLORS["bg_card"], corner_radius=15)
        card.pack(padx=20, pady=10, fill="x")

        self.lbl_mode = ctk.CTkLabel(card, text=self.timer_mode, font=("Roboto", 16), text_color=COLORS["accent"])
        self.lbl_mode.pack(pady=(15, 0))

        self.lbl_timer = ctk.CTkLabel(card, text=self.format_time(self.timer_seconds), font=("Roboto Mono", 60, "bold"))
        self.lbl_timer.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(card, progress_color=COLORS["accent"], height=10)
        self.progress_bar.set(self.timer_seconds / self.initial_time)
        self.progress_bar.pack(padx=30, pady=(0, 20), fill="x")

        btn_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_toggle = ctk.CTkButton(btn_frame, text="Start Focus" if not self.timer_running else "Pause",
                                        font=("Roboto", 14, "bold"), height=40, fg_color=COLORS["accent"],
                                        hover_color=COLORS["accent_hover"], command=self.toggle_timer)
        self.btn_toggle.grid(row=0, column=0, padx=5)

        ctk.CTkButton(btn_frame, text="Reset", font=("Roboto", 14), height=40, fg_color="transparent",
                      border_width=1, border_color=COLORS["text_dim"], command=self.reset_timer).grid(row=0, column=1,
                                                                                                      padx=5)

        mode_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        mode_frame.pack(pady=10)

        modes = [("Focus", 25), ("Short Break", 5), ("Long Break", 15)]
        for i, (m, t) in enumerate(modes):
            ctk.CTkButton(mode_frame, text=m, width=90, fg_color=COLORS["bg_card"],
                          command=lambda m=m, t=t: self.set_mode(m, t)).grid(row=0, column=i, padx=3)

    # --- Tasks Logic & View ---

    def add_task(self, event=None):
        text = self.entry_task.get()
        if text:
            self.tasks.append({'text': text, 'completed': False})
            self.show_tasks_view()  # Refresh view
            self.save_data()

    def remove_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self.show_tasks_view()
            self.save_data()

    def toggle_task(self, index, var):
        if 0 <= index < len(self.tasks):
            self.tasks[index]['completed'] = var.get()
            self.save_data()

    def show_tasks_view(self):
        self.clear_main_area()

        ctk.CTkLabel(self.main_area, text="✅ Tasks", font=("Roboto", 24, "bold")).pack(pady=(30, 20))

        input_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        input_frame.pack(padx=20, fill="x")

        self.entry_task = ctk.CTkEntry(input_frame, placeholder_text="Add a new task...", height=40)
        self.entry_task.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_task.bind("<Return>", self.add_task)

        ctk.CTkButton(input_frame, text="+", width=40, height=40, fg_color=COLORS["accent"],
                      command=self.add_task).pack(side="right")

        scroll_area = ctk.CTkScrollableFrame(self.main_area, fg_color=COLORS["bg_card"], label_text="To-Do List")
        scroll_area.pack(padx=20, pady=20, fill="both", expand=True)

        for i, task in enumerate(self.tasks):
            frame = ctk.CTkFrame(scroll_area, fg_color=COLORS["bg_window"])
            frame.pack(fill="x", pady=2, padx=5)

            chk_var = tk.BooleanVar(value=task['completed'])
            chk = ctk.CTkCheckBox(frame, text=task['text'], font=("Roboto", 14), fg_color=COLORS["accent"],
                                  variable=chk_var, command=lambda i=i, v=chk_var: self.toggle_task(i, v))
            chk.pack(side="left", padx=10, pady=10)

            ctk.CTkButton(frame, text="×", width=30, fg_color="transparent", text_color=COLORS["danger"],
                          command=lambda i=i: self.remove_task(i)).pack(side="right", padx=5)

    # --- Notes View ---

    def show_notes_view(self):
        self.clear_main_area()
        ctk.CTkLabel(self.main_area, text="📝 Quick Notes", font=("Roboto", 24, "bold")).pack(pady=(30, 20))

        self.text_notes = ctk.CTkTextbox(self.main_area, font=("Roboto", 14), fg_color=COLORS["bg_card"],
                                         corner_radius=10)
        self.text_notes.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.text_notes.insert("1.0", self.notes_content)

    # --- Links Logic & View ---

    def add_link(self):
        name = self.entry_link_name.get()
        url = self.entry_link_url.get()
        if name and url:
            if not url.startswith(('http', 'ftp')): url = 'https://' + url
            self.links.append({'name': name, 'url': url})
            self.show_links_view()
            self.save_data()
        else:
            messagebox.showwarning("Input Error", "Enter name and URL")

    def remove_link(self, index):
        del self.links[index]
        self.show_links_view()
        self.save_data()

    def show_links_view(self):
        self.clear_main_area()
        ctk.CTkLabel(self.main_area, text="🔗 Productive Links", font=("Roboto", 24, "bold")).pack(pady=(30, 20))

        input_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        input_frame.pack(padx=20, fill="x", pady=(0, 10))

        self.entry_link_name = ctk.CTkEntry(input_frame, placeholder_text="Name", width=150, height=40)
        self.entry_link_name.pack(side="left", padx=(0, 5), fill="x", expand=True)

        self.entry_link_url = ctk.CTkEntry(input_frame, placeholder_text="URL", height=40)
        self.entry_link_url.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(input_frame, text="Add", width=80, height=40, fg_color=COLORS["accent"],
                      command=self.add_link).pack(side="right")

        scroll_area = ctk.CTkScrollableFrame(self.main_area, fg_color=COLORS["bg_card"], label_text="Bookmarks")
        scroll_area.pack(padx=20, pady=(10, 20), fill="both", expand=True)

        for i, link in enumerate(self.links):
            frame = ctk.CTkFrame(scroll_area, fg_color=COLORS["bg_window"])
            frame.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(frame, text=link['name'], font=("Roboto", 14, "bold")).pack(side="left", padx=10, pady=10)

            ctk.CTkButton(frame, text="×", width=30, fg_color="transparent", text_color=COLORS["danger"],
                          command=lambda i=i: self.remove_link(i)).pack(side="right", padx=5)

            ctk.CTkButton(frame, text="Open", width=80, fg_color=COLORS["accent"],
                          command=lambda u=link['url']: webbrowser.open_new_tab(u)).pack(side="right", padx=10)


# --- Entry Point ---
if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("green")

    # Create the App instance
    app = ZenFocusApp()
    # Run the loop
    app.mainloop()
