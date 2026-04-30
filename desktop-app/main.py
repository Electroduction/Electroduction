"""
Electroduction Portfolio Desktop Application
A modern desktop application showcasing the Electroduction game and portfolio
"""

import customtkinter as ctk
import requests
from typing import Optional
import threading
import json
from datetime import datetime

# Configure theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ElectroductionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Electroduction Portfolio")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # API endpoint
        self.api_url = "http://localhost:8000"
        self.api_connected = False

        # Create UI
        self.create_sidebar()
        self.create_main_area()

        # Check API connection
        self.check_api_connection()

    def create_sidebar(self):
        """Create sidebar with navigation"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Electroduction",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Portfolio App",
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("🏠 Home", self.show_home),
            ("💼 Projects", self.show_projects),
            ("🎮 Game Stats", self.show_game_stats),
            ("📊 Leaderboard", self.show_leaderboard),
            ("📨 Contact", self.show_contact),
            ("⚙️ Settings", self.show_settings),
        ]

        for i, (text, command) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                font=ctk.CTkFont(size=14),
                height=40,
                anchor="w"
            )
            btn.grid(row=i+2, column=0, padx=20, pady=5, sticky="ew")
            self.nav_buttons.append(btn)

        # Status indicator
        self.status_frame = ctk.CTkFrame(self.sidebar)
        self.status_frame.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Offline",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        self.status_label.pack(pady=5)

    def create_main_area(self):
        """Create main content area"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Content container (will be replaced by each view)
        self.content = ctk.CTkFrame(self.main_frame)
        self.content.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Show home by default
        self.show_home()

    def check_api_connection(self):
        """Check if backend API is accessible"""
        def check():
            try:
                response = requests.get(f"{self.api_url}/api/health", timeout=2)
                if response.ok:
                    self.api_connected = True
                    self.status_label.configure(
                        text="● Online",
                        text_color="green"
                    )
                else:
                    self.api_connected = False
                    self.status_label.configure(
                        text="● Offline",
                        text_color="red"
                    )
            except:
                self.api_connected = False
                self.status_label.configure(
                    text="● Offline",
                    text_color="red"
                )

        # Run in background thread
        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def clear_content(self):
        """Clear current content"""
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_home(self):
        """Show home page"""
        self.clear_content()

        # Configure grid
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Welcome section
        welcome_frame = ctk.CTkFrame(self.content)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            welcome_frame,
            text="Welcome to Electroduction",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(40, 20))

        subtitle = ctk.CTkLabel(
            welcome_frame,
            text="Kenny Situ - Software Developer & Cybersecurity Professional",
            font=ctk.CTkFont(size=18)
        )
        subtitle.pack(pady=10)

        description = ctk.CTkLabel(
            welcome_frame,
            text="A professional portfolio showcasing projects,\ngame development, and technical expertise",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        description.pack(pady=20)

        # Stats grid
        stats_frame = ctk.CTkFrame(welcome_frame)
        stats_frame.pack(pady=30)

        stats = [
            ("Years Experience", "3+"),
            ("Projects", "15+"),
            ("Degrees", "3"),
        ]

        for i, (label, value) in enumerate(stats):
            stat_card = ctk.CTkFrame(stats_frame)
            stat_card.grid(row=0, column=i, padx=15, pady=10)

            value_label = ctk.CTkLabel(
                stat_card,
                text=value,
                font=ctk.CTkFont(size=36, weight="bold")
            )
            value_label.pack(padx=30, pady=(20, 5))

            text_label = ctk.CTkLabel(
                stat_card,
                text=label,
                font=ctk.CTkFont(size=14)
            )
            text_label.pack(padx=30, pady=(0, 20))

    def show_projects(self):
        """Show projects page"""
        self.clear_content()

        # Title
        title = ctk.CTkLabel(
            self.content,
            text="Featured Projects",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)

        # Scrollable frame for projects
        scroll_frame = ctk.CTkScrollableFrame(self.content)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        projects = [
            {
                "name": "Electroduction - AAA Roguelike Game",
                "desc": "Professional-grade roguelike with advanced combat, procedural generation, and particle effects",
                "tech": "Python, Pygame, Game Design"
            },
            {
                "name": "Portfolio Website",
                "desc": "Full-stack website with React frontend and FastAPI backend",
                "tech": "React, FastAPI, Docker"
            },
            {
                "name": "Project Mapper",
                "desc": "Code relationship analyzer with visual mapping",
                "tech": "Python, Tkinter, Visualization"
            },
            {
                "name": "Alpine Heights Store",
                "desc": "Complete e-commerce website implementation",
                "tech": "Web Design, E-commerce"
            },
            {
                "name": "Data Scraper",
                "desc": "Automated web scraping with Selenium",
                "tech": "Python, Selenium, WebDriver"
            },
        ]

        for project in projects:
            project_card = ctk.CTkFrame(scroll_frame)
            project_card.pack(fill="x", padx=10, pady=10)

            name_label = ctk.CTkLabel(
                project_card,
                text=project["name"],
                font=ctk.CTkFont(size=18, weight="bold"),
                anchor="w"
            )
            name_label.pack(fill="x", padx=15, pady=(15, 5))

            desc_label = ctk.CTkLabel(
                project_card,
                text=project["desc"],
                font=ctk.CTkFont(size=14),
                anchor="w",
                wraplength=600
            )
            desc_label.pack(fill="x", padx=15, pady=5)

            tech_label = ctk.CTkLabel(
                project_card,
                text=f"🔧 {project['tech']}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="gray"
            )
            tech_label.pack(fill="x", padx=15, pady=(5, 15))

    def show_game_stats(self):
        """Show game statistics"""
        self.clear_content()

        title = ctk.CTkLabel(
            self.content,
            text="Game Statistics",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)

        if not self.api_connected:
            message = ctk.CTkLabel(
                self.content,
                text="⚠️ Backend API is offline\nStart the backend server to view statistics",
                font=ctk.CTkFont(size=16),
                text_color="orange"
            )
            message.pack(pady=50)
            return

        # Fetch stats
        try:
            response = requests.get(f"{self.api_url}/api/game/stats")
            if response.ok:
                stats = response.json()

                # Stats grid
                stats_frame = ctk.CTkFrame(self.content)
                stats_frame.pack(pady=30)

                stat_items = [
                    ("Total Players", stats.get("total_players", 0)),
                    ("Total Runs", stats.get("total_runs", 0)),
                    ("Highest Level", stats.get("highest_level", 0)),
                    ("Bosses Defeated", stats.get("bosses_defeated", 0)),
                ]

                for i, (label, value) in enumerate(stat_items):
                    row = i // 2
                    col = i % 2

                    stat_card = ctk.CTkFrame(stats_frame)
                    stat_card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

                    value_label = ctk.CTkLabel(
                        stat_card,
                        text=str(value),
                        font=ctk.CTkFont(size=48, weight="bold")
                    )
                    value_label.pack(padx=50, pady=(30, 10))

                    text_label = ctk.CTkLabel(
                        stat_card,
                        text=label,
                        font=ctk.CTkFont(size=16)
                    )
                    text_label.pack(padx=50, pady=(0, 30))
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.content,
                text=f"Error loading stats: {str(e)}",
                text_color="red"
            )
            error_label.pack(pady=50)

    def show_leaderboard(self):
        """Show leaderboard"""
        self.clear_content()

        title = ctk.CTkLabel(
            self.content,
            text="Top Players",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)

        if not self.api_connected:
            message = ctk.CTkLabel(
                self.content,
                text="⚠️ Backend API is offline\nStart the backend server to view leaderboard",
                font=ctk.CTkFont(size=16),
                text_color="orange"
            )
            message.pack(pady=50)
            return

        # Fetch leaderboard
        try:
            response = requests.get(f"{self.api_url}/api/game/leaderboard")
            if response.ok:
                leaderboard = response.json()

                # Create table
                table_frame = ctk.CTkFrame(self.content)
                table_frame.pack(fill="both", expand=True, padx=20, pady=10)

                # Headers
                headers = ["Rank", "Player", "Score", "Level", "Date"]
                for i, header in enumerate(headers):
                    header_label = ctk.CTkLabel(
                        table_frame,
                        text=header,
                        font=ctk.CTkFont(size=14, weight="bold"),
                        width=100
                    )
                    header_label.grid(row=0, column=i, padx=10, pady=10, sticky="w")

                # Data
                for i, entry in enumerate(leaderboard[:10]):
                    rank_label = ctk.CTkLabel(table_frame, text=f"#{i+1}", width=100)
                    rank_label.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")

                    name_label = ctk.CTkLabel(table_frame, text=entry["player_name"], width=100)
                    name_label.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")

                    score_label = ctk.CTkLabel(table_frame, text=str(entry["score"]), width=100)
                    score_label.grid(row=i+1, column=2, padx=10, pady=5, sticky="w")

                    level_label = ctk.CTkLabel(table_frame, text=str(entry["level"]), width=100)
                    level_label.grid(row=i+1, column=3, padx=10, pady=5, sticky="w")

                    date = entry["date"].split("T")[0]
                    date_label = ctk.CTkLabel(table_frame, text=date, width=100)
                    date_label.grid(row=i+1, column=4, padx=10, pady=5, sticky="w")

                if len(leaderboard) == 0:
                    no_data = ctk.CTkLabel(
                        table_frame,
                        text="No scores yet. Be the first!",
                        font=ctk.CTkFont(size=14)
                    )
                    no_data.grid(row=1, column=0, columnspan=5, pady=20)
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.content,
                text=f"Error loading leaderboard: {str(e)}",
                text_color="red"
            )
            error_label.pack(pady=50)

    def show_contact(self):
        """Show contact form"""
        self.clear_content()

        title = ctk.CTkLabel(
            self.content,
            text="Contact",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)

        # Form
        form_frame = ctk.CTkFrame(self.content)
        form_frame.pack(pady=20, padx=50, fill="both")

        # Name
        name_label = ctk.CTkLabel(form_frame, text="Name:", font=ctk.CTkFont(size=14))
        name_label.pack(anchor="w", padx=20, pady=(20, 5))

        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Your name")
        self.name_entry.pack(fill="x", padx=20, pady=(0, 15))

        # Email
        email_label = ctk.CTkLabel(form_frame, text="Email:", font=ctk.CTkFont(size=14))
        email_label.pack(anchor="w", padx=20, pady=5)

        self.email_entry = ctk.CTkEntry(form_frame, placeholder_text="your.email@example.com")
        self.email_entry.pack(fill="x", padx=20, pady=(0, 15))

        # Message
        message_label = ctk.CTkLabel(form_frame, text="Message:", font=ctk.CTkFont(size=14))
        message_label.pack(anchor="w", padx=20, pady=5)

        self.message_text = ctk.CTkTextbox(form_frame, height=150)
        self.message_text.pack(fill="both", padx=20, pady=(0, 15))

        # Submit button
        submit_btn = ctk.CTkButton(
            form_frame,
            text="Send Message",
            command=self.submit_contact,
            font=ctk.CTkFont(size=14),
            height=40
        )
        submit_btn.pack(pady=(10, 20))

        # Status label
        self.contact_status = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.contact_status.pack(pady=5)

    def submit_contact(self):
        """Submit contact form"""
        if not self.api_connected:
            self.contact_status.configure(
                text="❌ Backend offline. Please start the server.",
                text_color="red"
            )
            return

        name = self.name_entry.get()
        email = self.email_entry.get()
        message = self.message_text.get("1.0", "end-1c")

        if not name or not email or not message:
            self.contact_status.configure(
                text="❌ Please fill all fields",
                text_color="red"
            )
            return

        try:
            response = requests.post(
                f"{self.api_url}/api/contact",
                json={"name": name, "email": email, "message": message}
            )

            if response.ok:
                self.contact_status.configure(
                    text="✅ Message sent successfully!",
                    text_color="green"
                )
                self.name_entry.delete(0, "end")
                self.email_entry.delete(0, "end")
                self.message_text.delete("1.0", "end")
            else:
                self.contact_status.configure(
                    text="❌ Failed to send message",
                    text_color="red"
                )
        except Exception as e:
            self.contact_status.configure(
                text=f"❌ Error: {str(e)}",
                text_color="red"
            )

    def show_settings(self):
        """Show settings page"""
        self.clear_content()

        title = ctk.CTkLabel(
            self.content,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)

        settings_frame = ctk.CTkFrame(self.content)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Theme setting
        theme_label = ctk.CTkLabel(
            settings_frame,
            text="Appearance Mode:",
            font=ctk.CTkFont(size=16)
        )
        theme_label.pack(anchor="w", padx=20, pady=(20, 10))

        theme_var = ctk.StringVar(value="Dark")
        theme_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["Dark", "Light", "System"],
            command=self.change_appearance_mode,
            variable=theme_var
        )
        theme_menu.pack(anchor="w", padx=20, pady=(0, 20))

        # API URL setting
        api_label = ctk.CTkLabel(
            settings_frame,
            text="API URL:",
            font=ctk.CTkFont(size=16)
        )
        api_label.pack(anchor="w", padx=20, pady=(20, 10))

        self.api_entry = ctk.CTkEntry(
            settings_frame,
            placeholder_text="http://localhost:8000"
        )
        self.api_entry.insert(0, self.api_url)
        self.api_entry.pack(fill="x", padx=20, pady=(0, 10))

        api_btn = ctk.CTkButton(
            settings_frame,
            text="Update API URL",
            command=self.update_api_url
        )
        api_btn.pack(anchor="w", padx=20, pady=(0, 20))

        # Info
        info_label = ctk.CTkLabel(
            settings_frame,
            text="Electroduction Portfolio v1.0\nBuilt with CustomTkinter",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(side="bottom", pady=20)

    def change_appearance_mode(self, new_mode: str):
        """Change appearance mode"""
        ctk.set_appearance_mode(new_mode.lower())

    def update_api_url(self):
        """Update API URL"""
        new_url = self.api_entry.get()
        if new_url:
            self.api_url = new_url
            self.check_api_connection()

def main():
    """Main entry point"""
    app = ElectroductionApp()
    app.mainloop()

if __name__ == "__main__":
    main()
