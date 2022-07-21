from tkinter import *
import customtkinter
import tkinter.filedialog as fd
from tkinter import ttk
import numpy as np
import json
import ast
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import board_setup

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()

        win_wid = self.winfo_screenwidth()
        win_ht = self.winfo_screenheight()

        self.title("PCB Heat Analysis")
        self.geometry(f"{win_wid}x{win_ht}+0+0")
        self.process = -1

        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        # ============ create two frames ============

        # configure grid layout (2x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.view_process()

        self.btn_board_setup.select()

        self.create_board_setup()
        self.create_sim_setup()
        self.create_results_frame()

        self.view_board_setup()
        self.view_board_settings()

    def view_process(self):
        self.frame_process = customtkinter.CTkFrame(master=self,
                                                    height=10)
        self.frame_process.grid(row=0, column=0, columnspan=2, sticky="nswe")

        # ========== frame_process ===========
        # configure grid layout (3x1)
        self.frame_process.rowconfigure(0, weight=1)
        self.frame_process.columnconfigure((0, 1, 2), weight=1)

        self.radio_var = IntVar(value=0)

        self.btn_board_setup = customtkinter.CTkRadioButton(master=self.frame_process,
                                                            variable=self.radio_var,
                                                            text='Board Setup',
                                                            value=0,
                                                            command=self.view_board_setup)
        self.btn_board_setup.grid(row=2, column=0, pady=10, padx=20, sticky="nswe")

        self.btn_sim_setup = customtkinter.CTkRadioButton(master=self.frame_process,
                                                          variable=self.radio_var,
                                                          text='Simulation Setup',
                                                          value=1,
                                                          command=self.view_sim_setup)
        self.btn_sim_setup.grid(row=2, column=1, pady=10, padx=20, sticky="nswe")
        self.btn_sim_setup.configure(state=DISABLED)

        self.btn_results = customtkinter.CTkRadioButton(master=self.frame_process,
                                                        variable=self.radio_var,
                                                        text='Results',
                                                        value=2,
                                                        command=self.view_results)
        self.btn_results.grid(row=2, column=2, pady=10, padx=20, sticky="nswe")
        self.btn_results.configure(state=DISABLED)

    def button_event(self):
        print("Button pressed")

    # board settings
    def create_board_setup(self):
        self.board_menu = customtkinter.CTkFrame(master=self,
                                                 width=180,
                                                 corner_radius=0)
        self.board_menu.grid_rowconfigure(0, minsize=10)
        self.board_menu.grid_rowconfigure((1, 2, 3), weight=1)

        self.btn_board_settings = customtkinter.CTkButton(master=self.board_menu,
                                                          text="Board Settings",
                                                          fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                          command=self.view_board_settings)
        self.btn_board_settings.pack(pady=10)

        self.btn_layer_settings = customtkinter.CTkButton(master=self.board_menu,
                                                          text="Layer Settings",
                                                          fg_color=None,  # <- custom tuple-color
                                                          command=self.view_layer_settings)
        self.btn_layer_settings.pack(pady=10)

        self.btn_board_component_settings = customtkinter.CTkButton(master=self.board_menu,
                                                                    text="Board Components",
                                                                    fg_color=None,  # <- custom tuple-color
                                                                    command=self.view_board_component_settings)
        self.btn_board_component_settings.pack(pady=10)

        self.board_edit = customtkinter.CTkFrame(master=self)
        self.board_edit.grid_rowconfigure(1, weight=1)
        self.create_board_settings()
        self.create_edit_layer_settings()
        self.create_board_components_settings()
        self.create_board_save_load_frame()

    def create_board_settings(self):
        self.board_settings_frame = customtkinter.CTkFrame(master=self.board_edit)

        self.board_settings_frame.grid_columnconfigure(0, minsize=220)
        self.board_settings_frame.grid_columnconfigure(1, minsize=180)
        self.board_settings_frame.grid_columnconfigure(2, minsize=80)

        self.lbl_board_cond_material = customtkinter.CTkLabel(master=self.board_settings_frame,
                                                              text="Conductor Material:",
                                                              text_font=(
                                                                  "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_cond_material.grid(row=0, column=0, padx=5, pady=5, sticky="we")
        cond_material_options = [
            "Copper",
            "Aluminum",
            "Gold",
            "Silver"
        ]
        self.cond_material_clicked = StringVar()
        self.cond_material_clicked.set(cond_material_options[0])
        self.opt_board_cond_material = OptionMenu(self.board_settings_frame, self.cond_material_clicked,
                                                  *cond_material_options, command=self.update_board_settings)
        self.opt_board_cond_material.grid(row=0, column=1, pady=5, padx=5, sticky="we")

        self.lbl_board_diel_material = customtkinter.CTkLabel(master=self.board_settings_frame,
                                                              text="Dielectric Material:",
                                                              text_font=(
                                                                  "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_diel_material.grid(row=1, column=0, padx=5, pady=5, sticky="we")
        diel_material_options = [
            "Fr-4"
        ]
        self.diel_material_clicked = StringVar()
        self.diel_material_clicked.set(diel_material_options[0])
        self.opt_board_diel_material = OptionMenu(self.board_settings_frame, self.diel_material_clicked,
                                                  *diel_material_options, command=self.update_board_settings)
        self.opt_board_diel_material.grid(row=1, column=1, pady=5, padx=5, sticky="we")

        self.lbl_board_plating_thickness = customtkinter.CTkLabel(master=self.board_settings_frame,
                                                                  text="Plating Thickness [oz]:",
                                                                  text_font=(
                                                                      "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_plating_thickness.grid(row=2, column=0, padx=5, pady=5, sticky="we")
        thickness_options = [
            '0.5',
            '1.0',
            '2.0'
        ]
        self.plating_thickness_clicked = StringVar()
        self.plating_thickness_clicked.set(thickness_options[0])
        self.opt_board_plating_thickness = OptionMenu(self.board_settings_frame, self.plating_thickness_clicked,
                                                      *thickness_options, command=self.update_board_settings)
        self.opt_board_plating_thickness.grid(row=2, column=1, pady=5, padx=5, sticky="we")

        self.lbl_board_drill_file = customtkinter.CTkLabel(master=self.board_settings_frame,
                                                           text="Drill File:",
                                                           text_font=(
                                                               "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_drill_file.grid(row=3, column=0, padx=5, pady=5, sticky="we")
        self.ent_drill_file_location = customtkinter.CTkEntry(master=self.board_settings_frame, width=120)
        self.ent_drill_file_location.grid(row=3, column=1, padx=5, pady=5, sticky="we")
        self.btn_browse_drill_file = customtkinter.CTkButton(master=self.board_settings_frame,
                                                             text="File...",
                                                             command=self.onDrillOpen)
        self.btn_browse_drill_file.grid(row=3, column=2, pady=5, padx=5, sticky="we")

        self.lbl_board_keepout_file = customtkinter.CTkLabel(master=self.board_settings_frame,
                                                             text="Keepout File:",
                                                             text_font=(
                                                                 "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_keepout_file.grid(row=4, column=0, padx=5, pady=5, sticky="we")
        self.ent_keepout_file_location = customtkinter.CTkEntry(master=self.board_settings_frame, width=120)
        self.ent_keepout_file_location.grid(row=4, column=1, padx=5, pady=5, sticky="we")
        self.btn_browse_keepout_file = customtkinter.CTkButton(master=self.board_settings_frame,
                                                               text="File...",
                                                               command=self.onKeepOutOpen)
        self.btn_browse_keepout_file.grid(row=4, column=2, pady=5, padx=5, sticky="we")

    def onDrillOpen(self):
        name = fd.askopenfilename(title="Drill File", filetypes=(("Drill files", "*.txt"), ("all files", "*.*")))
        self.ent_drill_file_location.insert(0, name)

    def onKeepOutOpen(self):
        name = fd.askopenfilename(title="Keepout File", filetypes=(("Keepout files", "*.GKO"), ("all files", "*.*")))
        self.ent_keepout_file_location.insert(0, name)

    def create_edit_layer_settings(self):
        self.layer_settings_frame = customtkinter.CTkFrame(master=self.board_edit)

        self.layer_settings_frame.grid_columnconfigure(0, minsize=220)
        self.layer_settings_frame.grid_columnconfigure(1, minsize=180)
        self.layer_settings_frame.grid_columnconfigure(2, minsize=80)

        self.layer_tree = ttk.Treeview(master=self.layer_settings_frame)
        self.layer_tree['columns'] = ("Name", "Type", "Thickness", "Gerber File")
        self.layer_tree.column("#0", width=0, stretch=NO)
        self.layer_tree.column("Name", anchor=W, width=80)
        self.layer_tree.column("Type", anchor=W, width=50)
        self.layer_tree.column("Thickness", anchor=CENTER, width=45)
        self.layer_tree.column("Gerber File", anchor=E, width=260)
        self.layer_tree.heading("#0", text="", anchor=W)
        self.layer_tree.heading("Name", text="Name", anchor=W)
        self.layer_tree.heading("Type", text="Type", anchor=W)
        self.layer_tree.heading("Thickness", text="Thickness", anchor=W)
        self.layer_tree.heading("Gerber File", text="Gerber File", anchor=CENTER)
        self.layer_tree.bind('<ButtonRelease-1>', self.layer_tree_select_item)
        self.layer_tree.grid(row=0, column=0, columnspan=3, sticky="nswe", pady=5, padx=5)

        self.btn_layer_add = customtkinter.CTkButton(master=self.layer_settings_frame, text="Add",
                                                     command=self.onLayerAdd)
        self.btn_layer_add.grid(row=1, column=0, pady=5, padx=5, sticky="we")

        self.btn_layer_remove = customtkinter.CTkButton(master=self.layer_settings_frame, text="Remove",
                                                        command=self.onLayerRemove)
        self.btn_layer_remove.grid(row=1, column=1, pady=5, padx=5, sticky="we")

        self.btn_layer_save = customtkinter.CTkButton(master=self.layer_settings_frame, text="Update",
                                                      command=self.onLayerUpdate)
        self.btn_layer_save.grid(row=1, column=2, pady=5, padx=5, sticky="we")

        self.lbl_layer_edit = customtkinter.CTkLabel(master=self.layer_settings_frame,
                                                     text="Layer Properties:",
                                                     text_font=(
                                                         "Roboto Medium", -16))  # font name and size in px
        self.lbl_layer_edit.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="we")

        self.lbl_layer_name = customtkinter.CTkLabel(master=self.layer_settings_frame,
                                                     text="Name:",
                                                     text_font=(
                                                         "Roboto Medium", -16))  # font name and size in px
        self.lbl_layer_name.grid(row=4, column=0, padx=5, pady=5, sticky="we")
        self.ent_layer_name = customtkinter.CTkEntry(master=self.layer_settings_frame, width=120)
        self.ent_layer_name.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        self.lbl_layer_type = customtkinter.CTkLabel(master=self.layer_settings_frame,
                                                     text="Type:",
                                                     text_font=(
                                                         "Roboto Medium", -16))  # font name and size in px
        self.lbl_layer_type.grid(row=5, column=0, padx=5, pady=5, sticky="we")
        layer_type_options = [
            "Conductor",
            "Dielectric"
        ]
        self.layer_type_clicked = StringVar()
        self.layer_type_clicked.set(layer_type_options[0])
        self.opt_layer_type = OptionMenu(self.layer_settings_frame, self.layer_type_clicked,
                                         *layer_type_options)
        self.opt_layer_type.grid(row=5, column=1, pady=5, padx=5, sticky="we")

        self.lbl_layer_thickness = customtkinter.CTkLabel(master=self.layer_settings_frame,
                                                          text="Thickness [mil]:",
                                                          text_font=(
                                                              "Roboto Medium", -16))  # font name and size in px
        self.lbl_layer_thickness.grid(row=6, column=0, padx=5, pady=5, sticky="we")
        self.ent_layer_thickness = customtkinter.CTkEntry(master=self.layer_settings_frame, width=120)
        self.ent_layer_thickness.grid(row=6, column=1, padx=5, pady=5, sticky="we")

        self.lbl_layer_gerber_file = customtkinter.CTkLabel(master=self.layer_settings_frame,
                                                            text="Gerber File:",
                                                            text_font=(
                                                                "Roboto Medium", -16))  # font name and size in px
        self.lbl_layer_gerber_file.grid(row=7, column=0, padx=5, pady=5, sticky="we")
        self.ent_gerber_file_location = customtkinter.CTkEntry(master=self.layer_settings_frame, width=120)
        self.ent_gerber_file_location.grid(row=7, column=1, padx=5, pady=5, sticky="we")
        self.btn_layer_gerber_file = customtkinter.CTkButton(master=self.layer_settings_frame, text="File...",
                                                             command=self.onGerberOpen)
        self.btn_layer_gerber_file.grid(row=7, column=2, pady=5, padx=5, sticky="we")

    def onGerberOpen(self):
        name = fd.askopenfilename(title="Gerber File", filetypes=(
            ("Gerber files", ".GTL G1 G2 G3 G4 G5 G6 G7 G8 G9 G10 GBL"), ("all files", "*.*")))
        self.ent_gerber_file_location.insert(0, name)

    def onLayerAdd(self):
        self.layer_tree.insert(parent='', index='end', text='', values=(
            self.ent_layer_name.get(), self.layer_type_clicked.get(), self.ent_layer_thickness.get(),
            self.ent_gerber_file_location.get()))

        self.ent_layer_name.delete(0, END)
        self.ent_layer_thickness.delete(0, END)
        self.ent_gerber_file_location.delete(0, END)

    def onLayerRemove(self):
        records = self.layer_tree.selection()
        if len(records) != 0:
            for record in records:
                self.layer_tree.delete(record)

    def onLayerUpdate(self):
        selected_no = self.layer_tree.focus()
        if selected_no != '':
            self.layer_tree.item(selected_no, text='', values=(
                self.ent_layer_name.get(), self.layer_type_clicked.get(), self.ent_layer_thickness.get(),
                self.ent_gerber_file_location.get()))

    def layer_tree_select_item(self, event):
        selected_no = self.layer_tree.focus()
        if selected_no != '':
            selected_vals = self.layer_tree.item(selected_no, 'values')

            self.ent_layer_name.delete(0, END)
            self.ent_layer_thickness.delete(0, END)
            self.ent_gerber_file_location.delete(0, END)

            self.ent_layer_name.insert(0, selected_vals[0])
            self.layer_type_clicked.set(selected_vals[1])
            self.ent_layer_thickness.insert(0, selected_vals[2])
            self.ent_gerber_file_location.insert(0, selected_vals[3])

    def create_board_components_settings(self):
        self.board_components_frame = customtkinter.CTkFrame(master=self.board_edit)

        self.board_components_frame.grid_columnconfigure(0, minsize=220)
        self.board_components_frame.grid_columnconfigure(1, minsize=180)
        self.board_components_frame.grid_columnconfigure(2, minsize=80)

        self.board_components_tree = ttk.Treeview(master=self.board_components_frame)
        self.board_components_tree['columns'] = ("Name", "Side", "Width", "Length", "X Position", "Y Position")
        self.board_components_tree.column("#0", width=0, stretch=NO)
        self.board_components_tree.column("Name", anchor=W, width=80)
        self.board_components_tree.column("Side", anchor=W, width=50)
        self.board_components_tree.column("Width", anchor=CENTER, width=40)
        self.board_components_tree.column("Length", anchor=CENTER, width=40)
        self.board_components_tree.column("X Position", anchor=CENTER, width=60)
        self.board_components_tree.column("Y Position", anchor=CENTER, width=60)
        self.board_components_tree.heading("#0", text="", anchor=W)
        self.board_components_tree.heading("Name", text="Name", anchor=W)
        self.board_components_tree.heading("Side", text="Side", anchor=W)
        self.board_components_tree.heading("Width", text="Width", anchor=W)
        self.board_components_tree.heading("Length", text="Length", anchor=W)
        self.board_components_tree.heading("X Position", text="X Position", anchor=CENTER)
        self.board_components_tree.heading("Y Position", text="Y Position", anchor=CENTER)
        self.board_components_tree.bind('<ButtonRelease-1>', self.board_components_select_item)
        self.board_components_tree.grid(row=0, column=0, columnspan=3, sticky="nswe", pady=5, padx=5)

        self.btn_board_components_add = customtkinter.CTkButton(master=self.board_components_frame, text="Add",
                                                                command=self.onBoardComponentAdd)
        self.btn_board_components_add.grid(row=1, column=0, pady=5, padx=5, sticky="we")

        self.btn_board_components_remove = customtkinter.CTkButton(master=self.board_components_frame, text="Remove",
                                                                   command=self.onBoardComponentRemove)
        self.btn_board_components_remove.grid(row=1, column=1, pady=5, padx=5, sticky="we")

        self.btn_board_components_save = customtkinter.CTkButton(master=self.board_components_frame, text="Update",
                                                                 command=self.onBoardComponentUpdate)
        self.btn_board_components_save.grid(row=1, column=2, pady=5, padx=5, sticky="we")

        self.lbl_board_components_edit = customtkinter.CTkLabel(master=self.board_components_frame,
                                                                text="Component Properties:",
                                                                text_font=(
                                                                    "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_components_edit.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="we")

        self.lbl_board_components_name = customtkinter.CTkLabel(master=self.board_components_frame,
                                                                text="Name:",
                                                                text_font=("Roboto Medium", -16))
        self.lbl_board_components_name.grid(row=3, column=0, padx=5, pady=5, sticky="we")
        self.ent_board_components_name = customtkinter.CTkEntry(master=self.board_components_frame, width=120)
        self.ent_board_components_name.grid(row=3, column=1, padx=5, pady=5, sticky="we")

        self.lbl_board_component_side = customtkinter.CTkLabel(master=self.board_components_frame,
                                                               text="Board Side:",
                                                               text_font=(
                                                                   "Roboto Medium", -16))  # font name and size in px
        self.lbl_board_component_side.grid(row=4, column=0, padx=5, pady=5, sticky="we")
        board_component_side_options = [
            "Top",
            "Bottom"
        ]
        self.board_component_side_clicked = StringVar()
        self.board_component_side_clicked.set(board_component_side_options[0])
        self.opt_board_component_side = OptionMenu(self.board_components_frame, self.board_component_side_clicked,
                                                   *board_component_side_options,
                                                   command=self.update_board_component_settings)
        self.opt_board_component_side.grid(row=4, column=1, pady=5, padx=5, sticky="we")

        self.lbl_board_components_width = customtkinter.CTkLabel(master=self.board_components_frame,
                                                                 text="Width:",
                                                                 text_font=("Roboto Medium", -16))
        self.lbl_board_components_width.grid(row=5, column=0, padx=5, pady=5, sticky="we")

        self.ent_board_components_width = customtkinter.CTkEntry(master=self.board_components_frame, width=120)
        self.ent_board_components_width.grid(row=5, column=1, padx=5, pady=5, sticky="we")

        self.lbl_board_components_length = customtkinter.CTkLabel(master=self.board_components_frame,
                                                                  text="Length:",
                                                                  text_font=("Roboto Medium", -16))
        self.lbl_board_components_length.grid(row=6, column=0, padx=5, pady=5, sticky="we")

        self.ent_board_components_length = customtkinter.CTkEntry(master=self.board_components_frame, width=120)
        self.ent_board_components_length.grid(row=6, column=1, padx=5, pady=5, sticky="we")

        self.lbl_board_components_x_pos = customtkinter.CTkLabel(master=self.board_components_frame,
                                                                 text="X Position:",
                                                                 text_font=("Roboto Medium", -16))
        self.lbl_board_components_x_pos.grid(row=7, column=0, padx=5, pady=5, sticky="we")

        self.ent_board_components_x_pos = customtkinter.CTkEntry(master=self.board_components_frame, width=120)
        self.ent_board_components_x_pos.grid(row=7, column=1, padx=5, pady=5, sticky="we")

        self.lbl_board_components_y_pos = customtkinter.CTkLabel(master=self.board_components_frame,
                                                                 text="Y Position:",
                                                                 text_font=("Roboto Medium", -16))
        self.lbl_board_components_y_pos.grid(row=8, column=0, padx=5, pady=5, sticky="we")

        self.ent_board_components_y_pos = customtkinter.CTkEntry(master=self.board_components_frame, width=120)
        self.ent_board_components_y_pos.grid(row=8, column=1, padx=5, pady=5, sticky="we")

    def onBoardComponentAdd(self):
        self.board_components_tree.insert(parent='', index='end', text='', values=(
            self.ent_board_components_name.get(), self.board_component_side_clicked.get(),
            self.ent_board_components_width.get(), self.ent_board_components_length.get(),
            self.ent_board_components_x_pos.get(), self.ent_board_components_y_pos.get()))

        self.ent_board_components_name.delete(0, END)
        self.ent_board_components_width.delete(0, END)
        self.ent_board_components_length.delete(0, END)
        self.ent_board_components_x_pos.delete(0, END)
        self.ent_board_components_y_pos.delete(0, END)

    def onBoardComponentRemove(self):
        records = self.board_components_tree.selection()
        if len(records) != 0:
            for record in records:
                self.board_components_tree.delete(record)

    def onBoardComponentUpdate(self):
        selected_no = self.board_components_tree.focus()
        if selected_no != '':
            self.board_components_tree.item(selected_no, text='', values=(
                self.ent_board_components_name.get(), self.board_component_side_clicked.get(),
                self.ent_board_components_width.get(), self.ent_board_components_length.get(),
                self.ent_board_components_x_pos.get(), self.ent_board_components_y_pos.get()))

    def board_components_select_item(self, event):
        selected_no = self.board_components_tree.focus()
        if selected_no != '':
            selected_vals = self.board_components_tree.item(selected_no, 'values')

            self.ent_board_components_name.delete(0, END)
            self.ent_board_components_width.delete(0, END)
            self.ent_board_components_length.delete(0, END)
            self.ent_board_components_x_pos.delete(0, END)
            self.ent_board_components_y_pos.delete(0, END)

            self.ent_board_components_name.insert(0, selected_vals[0])
            self.board_component_side_clicked.set(selected_vals[1])
            self.ent_board_components_width.insert(0, selected_vals[2])
            self.ent_board_components_length.insert(0, selected_vals[3])
            self.ent_board_components_x_pos.insert(0, selected_vals[4])
            self.ent_board_components_y_pos.insert(0, selected_vals[5])

    def update_board_component_settings(self, event):
        pass

    def create_board_save_load_frame(self):
        self.board_save_load_frame = customtkinter.CTkFrame(master=self.board_edit)
        self.board_save_load_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)

        self.btn_board_load = customtkinter.CTkButton(master=self.board_save_load_frame,
                                                      text="Load Board",
                                                      fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                      command=self.OnBoardLoad)
        self.btn_board_load.grid(row=0, column=0, sticky="we", padx=5, pady=5)

        self.btn_board_save = customtkinter.CTkButton(master=self.board_save_load_frame,
                                                      text="Save Board",
                                                      fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                      command=self.OnBoardSave)
        self.btn_board_save.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        self.btn_start_sim_setup = customtkinter.CTkButton(master=self.board_save_load_frame,
                                                           text="Setup Simulation",
                                                           fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                           command=self.OnStartSimSetup)
        self.btn_start_sim_setup.grid(row=0, column=2, sticky="we", padx=5, pady=5)

    def OnBoardLoad(self):
        board_load_name = fd.askopenfilename(title="Board Setup File",
                                             filetypes=(("Board Setup files", "*.pcb"), ("all files", "*.*")))

        with open(board_load_name, "r") as infile:
            board_setting_data = infile.read()
            board_settings = ast.literal_eval(json.loads(board_setting_data))

            self.cond_material_clicked.set(board_settings.get('conductor_material'))
            self.diel_material_clicked.set(board_settings.get('dielectric_material'))
            self.plating_thickness_clicked.set(board_settings.get('plating_thickness'))
            self.ent_drill_file_location.delete(0, END)
            self.ent_keepout_file_location.delete(0, END)
            self.ent_drill_file_location.insert(0, board_settings.get('drill_file'))
            self.ent_keepout_file_location.insert(0, board_settings.get('keepout_file'))

            # need to delete all from tree
            for record in self.layer_tree.get_children():
                self.layer_tree.delete(record)
            layers_setting = board_settings.get('layers')
            for layer_setting in layers_setting:
                if layer_setting.get('gerber_file') is None:
                    self.layer_tree.insert(parent='', index='end', text='', values=(
                        layer_setting.get('name'),
                        layer_setting.get('layer_type'),
                        layer_setting.get('thickness')
                    ))
                else:
                    self.layer_tree.insert(parent='', index='end', text='', values=(
                        layer_setting.get('name'),
                        layer_setting.get('layer_type'),
                        layer_setting.get('thickness'),
                        layer_setting.get('gerber_file')
                    ))

            # need to delete all from tree
            for record in self.board_components_tree.get_children():
                self.board_components_tree.delete(record)
            board_components_settings = board_settings.get('components')
            for board_component_setting in board_components_settings:
                self.board_components_tree.insert(parent='', index='end', text='', values=(
                    board_component_setting.get('name'),
                    board_component_setting.get('side'),
                    board_component_setting.get('width'),
                    board_component_setting.get('length'),
                    board_component_setting.get('x_position'),
                    board_component_setting.get('y_position')
                ))

    def compile_board_settings(self):
        layers_setup = list()
        board_components_setup = list()

        # Get layer settings
        for layer_setting in self.layer_tree.get_children():
            selected_vals = self.layer_tree.item(layer_setting, 'values')
            this_layer_setup = board_setup.LayerSetup(selected_vals[0],
                                                      selected_vals[1],
                                                      selected_vals[2],
                                                      selected_vals[3])
            layers_setup.append(this_layer_setup)

        # Get component settings
        for component_settings in self.board_components_tree.get_children():
            selected_vals = self.board_components_tree.item(component_settings, 'values')
            this_component_setup = board_setup.ComponentSetup(selected_vals[0],
                                                              selected_vals[1],
                                                              selected_vals[2],
                                                              selected_vals[3],
                                                              selected_vals[4],
                                                              selected_vals[5])
            board_components_setup.append(this_component_setup)

        # Board setup
        board_settings = board_setup.BoardSetup(self.cond_material_clicked.get(),
                                                self.diel_material_clicked.get(),
                                                self.plating_thickness_clicked.get(),
                                                self.ent_drill_file_location.get(),
                                                self.ent_keepout_file_location.get(),
                                                layers_setup,
                                                board_components_setup)

        return board_settings

    def OnBoardSave(self):
        board_save_name = fd.asksaveasfilename(defaultextension='.pcb', filetypes=[("PCB files", '*.pcb')],
                                               title="Board Setup File")
        # need to take all the gui widgets, build setup classes and export into json
        if board_save_name != '':
            board_settings = self.compile_board_settings()

            with open(board_save_name, "w") as outfile:
                outfile.write(json.dumps(board_setup.BoardEncoder().encode(board_settings)))


    def OnStartSimSetup(self):
        self.board_layer_names = list()

        for layer in self.layer_tree.get_children():
            layer_values = self.layer_tree.item(layer, 'values')
            self.board_layer_names.append(layer_values[0])

        self.board_component_names = list()
        for board_component in self.board_components_tree.get_children():
            component_values = self.board_components_tree.item(board_component, 'values')
            self.board_component_names.append(component_values[0])

        self.create_sim_settings_frame()
        self.create_sim_tuning_frame()
        self.create_loads_settings_frame()
        self.create_components_settings_frame()
        self.view_sim_settings()

        self.btn_sim_setup.configure(state=NORMAL)
        self.btn_sim_setup.select()
        self.view_sim_setup()

    def update_board_settings(self, event):
        pass

    def view_board_setup(self):
        self.sim_menu.grid_remove()
        self.sim_edit.grid_remove()
        self.results_menu.grid_remove()
        self.results_edit.grid_remove()
        self.board_menu.grid(row=1, column=0, sticky="nswe")
        self.board_edit.grid(row=1, column=1, sticky="nswe", padx=20, pady=20)

    def view_board_settings(self):
        self.layer_settings_frame.grid_remove()
        self.board_components_frame.grid_remove()
        self.board_settings_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)

        self.btn_board_settings.configure(fg_color=("gray75", "gray30"))
        self.btn_layer_settings.configure(fg_color=None)
        self.btn_board_component_settings.configure(fg_color=None)

    def view_layer_settings(self):
        self.board_settings_frame.grid_remove()
        self.board_components_frame.grid_remove()
        self.layer_settings_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)

        self.btn_layer_settings.configure(fg_color=("gray75", "gray30"))
        self.btn_board_settings.configure(fg_color=None)
        self.btn_board_component_settings.configure(fg_color=None)

    def view_board_component_settings(self):
        self.board_settings_frame.grid_remove()
        self.layer_settings_frame.grid_remove()
        self.board_components_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)

        self.btn_board_component_settings.configure(fg_color=("gray75", "gray30"))
        self.btn_layer_settings.configure(fg_color=None)
        self.btn_board_settings.configure(fg_color=None)

    # simulation settings
    def create_sim_setup(self):
        self.sim_menu = customtkinter.CTkFrame(master=self,
                                               width=180,
                                               corner_radius=0)

        self.sim_menu.grid_rowconfigure(0, minsize=10)
        self.sim_menu.grid_rowconfigure((1, 2), weight=1)

        self.btn_sim_settings = customtkinter.CTkButton(master=self.sim_menu,
                                                        text="Simulation Settings",
                                                        fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                        command=self.view_sim_settings)
        self.btn_sim_settings.pack(pady=10)

        self.btn_sim_tuning = customtkinter.CTkButton(master=self.sim_menu,
                                                        text="Tuning Settings",
                                                        fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                        command=self.view_sim_tuning)
        self.btn_sim_tuning.pack(pady=10)

        self.btn_loads_settings = customtkinter.CTkButton(master=self.sim_menu,
                                                          text="Load Settings",
                                                          fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                          command=self.view_loads_settings)
        self.btn_loads_settings.pack(pady=10)

        self.btn_component_settings = customtkinter.CTkButton(master=self.sim_menu,
                                                              text="Component Settings",
                                                              fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                              command=self.view_components_settings)
        self.btn_component_settings.pack(pady=10)

        self.sim_edit = customtkinter.CTkFrame(master=self)
        self.sim_edit.grid_rowconfigure(1, weight=1)
        self.sim_edit.grid_columnconfigure(0, weight=1)
        self.create_sim_save_load_frame()

    def create_sim_settings_frame(self):
        self.sim_settings_frame = customtkinter.CTkFrame(master=self.sim_edit)

        self.sim_settings_frame.grid_columnconfigure(0, minsize=250)
        self.sim_settings_frame.grid_columnconfigure(1, minsize=180)

        self.lbl_sim_resolution = customtkinter.CTkLabel(master=self.sim_settings_frame,
                                                         text="Resolution [mil]:",
                                                         text_font=(
                                                             "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_resolution.grid(row=0, column=0, padx=5, pady=5, sticky="we")

        self.sim_res_tkr = Spinbox(master=self.sim_settings_frame, from_=1, to=1000)
        self.sim_res_tkr.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_ambient = customtkinter.CTkLabel(master=self.sim_settings_frame,
                                                      text="Ambient Temp [C]:",
                                                      text_font=(
                                                          "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_ambient.grid(row=1, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_ambient = customtkinter.CTkEntry(master=self.sim_settings_frame, width=120)
        self.ent_sim_ambient.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_board_orient = customtkinter.CTkLabel(master=self.sim_settings_frame,
                                                           text="Board Orientation:",
                                                           text_font=(
                                                               "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_board_orient.grid(row=2, column=0, padx=5, pady=5, sticky="we")

        sim_board_orient_options = [
            "X-axis, Y-axis Zero",
            "X-axis -90",
            "X-axis +90",
            "Y-axis -90",
            "Y-axis +90"
        ]
        self.sim_board_orient_clicked = StringVar()
        self.sim_board_orient_clicked.set(sim_board_orient_options[0])
        self.opt_sim_board_orient = OptionMenu(self.sim_settings_frame, self.sim_board_orient_clicked,
                                               *sim_board_orient_options, command=self.update_sim_settings)
        self.opt_sim_board_orient.grid(row=2, column=1, pady=5, padx=5, sticky="we")

    def create_sim_tuning_frame(self):
        self.sim_tuning_frame = customtkinter.CTkFrame(master=self.sim_edit)

        self.lbl_sim_cond_k_in_plane = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                      text="Conductor 'k', in-plane:",
                                                      text_font=(
                                                          "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_cond_k_in_plane.grid(row=0, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_cond_k_in_plane = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_cond_k_in_plane.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_cond_k_thru_plane = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                              text="Conductor 'k', through-plane:",
                                                              text_font=(
                                                                  "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_cond_k_thru_plane.grid(row=1, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_cond_k_thru_plane = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_cond_k_thru_plane.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_diel_k_in_plane = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                              text="Dielectric 'k', in-plane:",
                                                              text_font=(
                                                                  "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_diel_k_in_plane.grid(row=2, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_diel_k_in_plane = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_diel_k_in_plane.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_diel_k_thru_plane = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                                text="Dielectric 'k', through-plane:",
                                                                text_font=(
                                                                    "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_diel_k_thru_plane.grid(row=3, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_diel_k_thru_plane = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_diel_k_thru_plane.grid(row=3, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_conv_coef = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                              text="PCB Convection Coefficient:",
                                                              text_font=(
                                                                  "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_conv_coef.grid(row=4, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_conv_coef = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_conv_coef.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_rad_coef = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                                text="PCB Radiation Coefficient:",
                                                                text_font=(
                                                                    "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_rad_coef.grid(row=5, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_rad_coef = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_rad_coef.grid(row=5, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_rad_pow = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                       text="PCB Radiation Power:",
                                                       text_font=(
                                                           "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_rad_pow.grid(row=6, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_rad_pow = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_rad_pow.grid(row=6, column=1, padx=5, pady=5, sticky="we")

        self.lbl_sim_comp_htc = customtkinter.CTkLabel(master=self.sim_tuning_frame,
                                                      text="Component HTC Coefficient:",
                                                      text_font=(
                                                          "Roboto Medium", -16))  # font name and size in px
        self.lbl_sim_comp_htc.grid(row=7, column=0, padx=5, pady=5, sticky="we")

        self.ent_sim_comp_htc = customtkinter.CTkEntry(master=self.sim_tuning_frame, width=120)
        self.ent_sim_comp_htc.grid(row=7, column=1, padx=5, pady=5, sticky="we")

    def create_loads_settings_frame(self):
        self.sim_loads_frame = customtkinter.CTkFrame(master=self.sim_edit)

        self.sim_loads_frame.grid_columnconfigure(0, minsize=250)
        self.sim_loads_frame.grid_columnconfigure(1, minsize=210)
        self.sim_loads_frame.grid_columnconfigure(2, minsize=80)

        self.loads_tree = ttk.Treeview(master=self.sim_loads_frame)
        self.loads_tree['columns'] = ("Name", "Layer", "Current", "X Start", "Y Start", "X End", "Y End")
        self.loads_tree.column("#0", width=0, stretch=NO)
        self.loads_tree.column("Name", anchor=W, width=80)
        self.loads_tree.column("Layer", anchor=W, width=60)
        self.loads_tree.column("Current", anchor=CENTER, width=40)
        self.loads_tree.column("X Start", anchor=CENTER, width=40)
        self.loads_tree.column("Y Start", anchor=CENTER, width=40)
        self.loads_tree.column("X End", anchor=CENTER, width=40)
        self.loads_tree.column("Y End", anchor=CENTER, width=40)
        self.loads_tree.heading("#0", text="", anchor=W)
        self.loads_tree.heading("Name", text="Name", anchor=W)
        self.loads_tree.heading("Layer", text="Layer", anchor=W)
        self.loads_tree.heading("Current", text="Current", anchor=CENTER)
        self.loads_tree.heading("X Start", text="X Start", anchor=CENTER)
        self.loads_tree.heading("Y Start", text="Y Start", anchor=CENTER)
        self.loads_tree.heading("X End", text="X End", anchor=CENTER)
        self.loads_tree.heading("Y End", text="Y End", anchor=CENTER)
        self.loads_tree.bind('<ButtonRelease-1>', self.loads_tree_select_item)
        self.loads_tree.grid(row=0, column=0, columnspan=3, sticky="nswe", pady=5, padx=5)

        self.btn_loads_add = customtkinter.CTkButton(master=self.sim_loads_frame, text="Add",
                                                     command=self.onLoadAdd)
        self.btn_loads_add.grid(row=1, column=0, pady=5, padx=5, sticky="we")

        self.btn_loads_remove = customtkinter.CTkButton(master=self.sim_loads_frame, text="Remove",
                                                        command=self.onLoadRemove)
        self.btn_loads_remove.grid(row=1, column=1, pady=5, padx=5, sticky="we")

        self.btn_load_save = customtkinter.CTkButton(master=self.sim_loads_frame, text="Update",
                                                     command=self.onLoadUpdate)
        self.btn_load_save.grid(row=1, column=2, pady=5, padx=5, sticky="we")

        self.lbl_load_edit = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                    text="Load Properties:",
                                                    text_font=(
                                                        "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_edit.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="we")

        self.lbl_load_name = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                    text="Name:",
                                                    text_font=(
                                                        "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_name.grid(row=4, column=0, padx=5, pady=5, sticky="we")
        self.ent_load_name = customtkinter.CTkEntry(master=self.sim_loads_frame, width=120)
        self.ent_load_name.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        self.lbl_load_layer = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                     text="Layer:",
                                                     text_font=(
                                                         "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_layer.grid(row=5, column=0, padx=5, pady=5, sticky="we")
        load_layer_options = self.board_layer_names
        self.load_layer_clicked = StringVar()
        self.load_layer_clicked.set(load_layer_options[0])
        self.opt_load_layer = OptionMenu(self.sim_loads_frame, self.load_layer_clicked,
                                         *load_layer_options,
                                         command=self.update_board_component_settings)
        self.opt_load_layer.grid(row=5, column=1, pady=5, padx=5, sticky="we")

        self.lbl_load_current = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                       text="Current:",
                                                       text_font=(
                                                           "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_current.grid(row=6, column=0, padx=5, pady=5, sticky="we")

        self.ent_load_current = customtkinter.CTkEntry(master=self.sim_loads_frame, width=120)
        self.ent_load_current.grid(row=6, column=1, padx=5, pady=5, sticky="we")

        self.lbl_load_x_start = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                       text="X Start Location:",
                                                       text_font=(
                                                           "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_x_start.grid(row=7, column=0, padx=5, pady=5, sticky="we")

        self.ent_load_x_start = customtkinter.CTkEntry(master=self.sim_loads_frame, width=120)
        self.ent_load_x_start.grid(row=7, column=1, padx=5, pady=5, sticky="we")

        self.lbl_load_y_start = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                       text="Y Start Location:",
                                                       text_font=(
                                                           "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_y_start.grid(row=8, column=0, padx=5, pady=5, sticky="we")

        self.ent_load_y_start = customtkinter.CTkEntry(master=self.sim_loads_frame, width=120)
        self.ent_load_y_start.grid(row=8, column=1, padx=5, pady=5, sticky="we")

        self.lbl_load_x_end = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                     text="X End Location:",
                                                     text_font=(
                                                         "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_x_end.grid(row=9, column=0, padx=5, pady=5, sticky="we")

        self.ent_load_x_end = customtkinter.CTkEntry(master=self.sim_loads_frame, width=120)
        self.ent_load_x_end.grid(row=9, column=1, padx=5, pady=5, sticky="we")

        self.lbl_load_y_end = customtkinter.CTkLabel(master=self.sim_loads_frame,
                                                     text="Y End Location:",
                                                     text_font=(
                                                         "Roboto Medium", -16))  # font name and size in px
        self.lbl_load_y_end.grid(row=10, column=0, padx=5, pady=5, sticky="we")

        self.ent_load_y_end = customtkinter.CTkEntry(master=self.sim_loads_frame, width=120)
        self.ent_load_y_end.grid(row=10, column=1, padx=5, pady=5, sticky="we")

    def onLoadAdd(self):
        self.loads_tree.insert(parent='', index='end', text='', values=(
            self.ent_load_name.get(), self.load_layer_clicked.get(), self.ent_load_current.get(),
            self.ent_load_x_start.get(), self.ent_load_y_start.get(),
            self.ent_load_x_end.get(), self.ent_load_y_end.get()))

        self.ent_load_name.delete(0, END)
        self.ent_load_current.delete(0, END)
        self.ent_load_x_start.delete(0, END)
        self.ent_load_y_start.delete(0, END)
        self.ent_load_x_end.delete(0, END)
        self.ent_load_y_end.delete(0, END)

    def onLoadRemove(self):
        records = self.loads_tree.selection()
        if len(records) != 0:
            for record in records:
                self.loads_tree.delete(record)

    def onLoadUpdate(self):
        selected_no = self.loads_tree.focus()
        if selected_no != '':
            self.loads_tree.item(selected_no, text='', values=(
                self.ent_load_name.get(), self.load_layer_clicked.get(), self.ent_load_current.get(),
                self.ent_load_x_start.get(), self.ent_load_y_start.get(),
                self.ent_load_x_end.get(), self.ent_load_y_end.get()))

    def loads_tree_select_item(self, event):
        selected_no = self.loads_tree.focus()
        if selected_no != '':
            selected_vals = self.loads_tree.item(selected_no, 'values')

            self.ent_load_name.delete(0, END)
            self.ent_load_current.delete(0, END)
            self.ent_load_x_start.delete(0, END)
            self.ent_load_y_start.delete(0, END)
            self.ent_load_x_end.delete(0, END)
            self.ent_load_y_end.delete(0, END)

            self.ent_load_name.insert(0, selected_vals[0])
            self.load_layer_clicked.set(selected_vals[1])
            self.ent_load_current.insert(0, selected_vals[2])
            self.ent_load_x_start.insert(0, selected_vals[3])
            self.ent_load_y_start.insert(0, selected_vals[4])
            self.ent_load_x_end.insert(0, selected_vals[5])
            self.ent_load_y_end.insert(0, selected_vals[6])

    def create_components_settings_frame(self):
        self.sim_components_frame = customtkinter.CTkFrame(master=self.sim_edit)

        self.sim_components_frame.grid_columnconfigure(0, minsize=220)
        self.sim_components_frame.grid_columnconfigure(1, minsize=180)
        self.sim_components_frame.grid_columnconfigure(2, minsize=80)

        self.component_heat_tree = ttk.Treeview(master=self.sim_components_frame)
        self.component_heat_tree['columns'] = ("Component", "Heat")
        self.component_heat_tree.column("#0", width=0, stretch=NO)
        self.component_heat_tree.column("Component", anchor=W, width=80)
        self.component_heat_tree.column("Heat", anchor=CENTER, width=80)
        self.component_heat_tree.heading("Component", text="Component Name", anchor=W)
        self.component_heat_tree.heading("Heat", text="Heat [W]", anchor=CENTER)
        self.component_heat_tree.bind('<ButtonRelease-1>', self.component_heat_tree_select_item)
        self.component_heat_tree.grid(row=0, column=0, columnspan=3, sticky="nswe", pady=5, padx=5)

        self.btn_component_heat_add = customtkinter.CTkButton(master=self.sim_components_frame, text="Add",
                                                              command=self.onComponentHeatAdd)
        self.btn_component_heat_add.grid(row=1, column=0, pady=5, padx=5, sticky="we")

        self.btn_component_heat_remove = customtkinter.CTkButton(master=self.sim_components_frame, text="Remove",
                                                                 command=self.onComponentHeatRemove)
        self.btn_component_heat_remove.grid(row=1, column=1, pady=5, padx=5, sticky="we")

        self.btn_component_heat_save = customtkinter.CTkButton(master=self.sim_components_frame, text="Update",
                                                               command=self.onComponentHeatUpdate)
        self.btn_component_heat_save.grid(row=1, column=2, pady=5, padx=5, sticky="we")

        self.lbl_component_heat_edit = customtkinter.CTkLabel(master=self.sim_components_frame,
                                                              text="Component Heat Properties:",
                                                              text_font=(
                                                                  "Roboto Medium", -16))  # font name and size in px
        self.lbl_component_heat_edit.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="we")

        self.lbl_component_name = customtkinter.CTkLabel(master=self.sim_components_frame,
                                                         text="Component:",
                                                         text_font=(
                                                             "Roboto Medium", -16))  # font name and size in px
        self.lbl_component_name.grid(row=3, column=0, padx=5, pady=5, sticky="we")
        if len(self.board_component_names) > 0:
            component_name_options = self.board_component_names
        else:
            component_name_options = ["None"]
            self.btn_component_heat_add.configure(state=DISABLED)
            self.btn_component_heat_remove.configure(state=DISABLED)
            self.btn_component_heat_save.configure(state=DISABLED)
        self.component_name_clicked = StringVar()
        self.component_name_clicked.set(component_name_options[0])
        self.opt_component_name = OptionMenu(self.sim_components_frame, self.component_name_clicked,
                                             *component_name_options)
        self.opt_component_name.grid(row=3, column=1, pady=5, padx=5, sticky="we")

        self.lbl_component_heat = customtkinter.CTkLabel(master=self.sim_components_frame,
                                                         text="Heat [W]:",
                                                         text_font=(
                                                             "Roboto Medium", -16))  # font name and size in px
        self.lbl_component_heat.grid(row=4, column=0, padx=5, pady=5, sticky="we")
        self.ent_component_heat = customtkinter.CTkEntry(master=self.sim_components_frame, width=120)
        self.ent_component_heat.grid(row=4, column=1, padx=5, pady=5, sticky="we")

    def onComponentHeatAdd(self):
        self.component_heat_tree.insert(parent='', index='end', text='', values=(
            self.component_name_clicked.get(), self.ent_component_heat.get()))

        self.ent_component_heat.delete(0, END)

    def onComponentHeatRemove(self):
        records = self.component_heat_tree.selection()
        if len(records) != 0:
            for record in records:
                self.component_heat_tree.delete(record)

    def onComponentHeatUpdate(self):
        selected_no = self.component_heat_tree.focus()
        if selected_no != '':
            self.component_heat_tree.item(selected_no, text='', values=(
                self.component_name_clicked.get(), self.ent_component_heat.get()))

    def component_heat_tree_select_item(self, event):
        selected_no = self.component_heat_tree.focus()
        if selected_no != '':
            selected_vals = self.component_heat_tree.item(selected_no, 'values')

            self.ent_component_heat.delete(0, END)

            self.component_name_clicked.set(selected_vals[0])
            self.ent_component_heat.insert(0, selected_vals[1])

    def create_sim_save_load_frame(self):
        self.sim_save_load_frame = customtkinter.CTkFrame(master=self.sim_edit)
        self.sim_save_load_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)

        self.btn_sim_load = customtkinter.CTkButton(master=self.sim_save_load_frame,
                                                    text="Load Simulation",
                                                    fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                    command=self.OnSimLoad)
        self.btn_sim_load.grid(row=0, column=0, sticky="nwse", padx=5, pady=5)

        self.btn_sim_save = customtkinter.CTkButton(master=self.sim_save_load_frame,
                                                    text="Save Simulation",
                                                    fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                    command=self.OnSimSave)
        self.btn_sim_save.grid(row=0, column=1, sticky="nwse", padx=5, pady=5)

        self.btn_sim_run = customtkinter.CTkButton(master=self.sim_save_load_frame,
                                                   text="Run Simulation",
                                                   fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                   command=self.OnSimRun)
        self.btn_sim_run.grid(row=0, column=2, sticky="nwse", padx=5, pady=5)

    def OnSimLoad(self):
        sim_load_name = fd.askopenfilename(title="Simulation Setup File",
                                           filetypes=(("Simulation Setup files", "*.sim"), ("all files", "*.*")))

        with open(sim_load_name, "r") as infile:
            sim_setting_data = infile.read()
            sim_settings = ast.literal_eval(json.loads(sim_setting_data))
            tuning_settings = sim_settings.get('tuning')
            self.sim_res_tkr.delete(0, END)
            self.sim_res_tkr.insert(0, sim_settings.get('resolution'))
            self.ent_sim_ambient.delete(0, END)
            self.ent_sim_ambient.insert(0, sim_settings.get('ambient'))
            self.sim_board_orient_clicked.set(sim_settings.get('orientation'))

            self.ent_sim_cond_k_in_plane.delete(0, END)
            self.ent_sim_cond_k_in_plane.insert(0, tuning_settings.get('cond_k_inplane'))
            self.ent_sim_cond_k_thru_plane.delete(0, END)
            self.ent_sim_cond_k_thru_plane.insert(0, tuning_settings.get('cond_k_thruplane'))
            self.ent_sim_diel_k_in_plane.delete(0, END)
            self.ent_sim_diel_k_in_plane.insert(0, tuning_settings.get('diel_k_inplane'))
            self.ent_sim_diel_k_thru_plane.delete(0, END)
            self.ent_sim_diel_k_thru_plane.insert(0, tuning_settings.get('diel_k_thruplane'))
            self.ent_sim_conv_coef.delete(0, END)
            self.ent_sim_conv_coef.insert(0, tuning_settings.get('conv_coef'))
            self.ent_sim_rad_coef.delete(0, END)
            self.ent_sim_rad_coef.insert(0, tuning_settings.get('rad_coef'))
            self.ent_sim_rad_pow.delete(0, END)
            self.ent_sim_rad_pow.insert(0, tuning_settings.get('rad_pow'))
            self.ent_sim_comp_htc.delete(0, END)
            self.ent_sim_comp_htc.insert(0, tuning_settings.get('component_htc'))

            for record in self.loads_tree.get_children():
                self.loads_tree.delete(record)
            loads_setting = sim_settings.get('loads')
            for load_setting in loads_setting:
                self.loads_tree.insert(parent='', index='end', text='', values=(
                    load_setting.get('name'),
                    load_setting.get('layer'),
                    load_setting.get('current'),
                    load_setting.get('x_start'),
                    load_setting.get('y_start'),
                    load_setting.get('x_end'),
                    load_setting.get('y_end')
                ))

            for record in self.component_heat_tree.get_children():
                self.component_heat_tree.delete(record)
            component_heats_settings = sim_settings.get('component_heats')
            for component_heat_setting in component_heats_settings:
                self.component_heat_tree.insert(parent='', index='end', text='', values=(
                    component_heat_setting.get('component_name'),
                    component_heat_setting.get('heat')
                ))

    def compile_sim_settings(self):
        loads_setup = list()
        component_heats_setup = list()

        # Get load settings
        for load_setting in self.loads_tree.get_children():
            selected_vals = self.loads_tree.item(load_setting, 'values')
            this_load_setup = board_setup.LoadSetup(selected_vals[0],
                                                    selected_vals[1],
                                                    selected_vals[2],
                                                    selected_vals[3],
                                                    selected_vals[4],
                                                    selected_vals[5],
                                                    selected_vals[6])
            loads_setup.append(this_load_setup)

        # Get component heat settings
        for component_heat_settings in self.component_heat_tree.get_children():
            selected_vals = self.component_heat_tree.item(component_heat_settings, 'values')
            this_component_heat_setup = board_setup.ComponentHeatSetup(selected_vals[0],
                                                                       selected_vals[1])
            component_heats_setup.append(this_component_heat_setup)

        tuning_setup = board_setup.TuningSetup(self.ent_sim_cond_k_in_plane.get(),
                                               self.ent_sim_cond_k_thru_plane.get(),
                                               self.ent_sim_diel_k_in_plane.get(),
                                               self.ent_sim_diel_k_thru_plane.get(),
                                               self.ent_sim_conv_coef.get(),
                                               self.ent_sim_rad_coef.get(),
                                               self.ent_sim_rad_pow.get(),
                                               self.ent_sim_comp_htc.get())

        # Board setup
        sim_settings = board_setup.SimulationSetup(self.sim_res_tkr.get(),
                                                   self.ent_sim_ambient.get(),
                                                   self.sim_board_orient_clicked.get(),
                                                   tuning_setup,
                                                   loads_setup,
                                                   component_heats_setup)

        return sim_settings

    def OnSimSave(self):
        sim_save_name = fd.asksaveasfilename(defaultextension='.sim', filetypes=[("sim settings files", '*.sim')],
                                             title="Simulation Settings File")
        if sim_save_name != '':
            sim_settings = self.compile_sim_settings()

            with open(sim_save_name, "w") as outfile:
                outfile.write(json.dumps(board_setup.BoardEncoder().encode(sim_settings)))

    def OnSimRun(self):
        board_settings = self.compile_board_settings()
        sim_settings = self.compile_sim_settings()

        self.heat_analysis = board_setup.run_simulation(board_settings, sim_settings)
        self.layer_cnt = len(self.heat_analysis.board.layers)

        self.create_result_figure_frame()

        self.btn_results.configure(state=NORMAL)
        self.btn_results.select()
        self.view_results()

    def update_sim_settings(self, event=0):
        pass

    def view_sim_setup(self):
        if self.btn_sim_setup.__getattribute__('state') == NORMAL:
            self.board_menu.grid_remove()
            self.board_edit.grid_remove()
            self.results_menu.grid_remove()
            self.results_edit.grid_remove()
            self.sim_menu.grid(row=1, column=0, sticky="nswe")
            self.sim_edit.grid(row=1, column=1, sticky="nswe", padx=20, pady=20)

    def view_sim_settings(self):
        self.sim_settings_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)
        self.sim_tuning_frame.grid_remove()
        self.sim_loads_frame.grid_remove()
        self.sim_components_frame.grid_remove()

        self.btn_sim_settings.configure(fg_color=("gray75", "gray30"))
        self.btn_sim_tuning.configure(fg_color=None)
        self.btn_loads_settings.configure(fg_color=None)
        self.btn_component_settings.configure(fg_color=None)

    def view_sim_tuning(self):
        self.sim_settings_frame.grid_remove()
        self.sim_tuning_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)
        self.sim_loads_frame.grid_remove()
        self.sim_components_frame.grid_remove()

        self.btn_sim_settings.configure(fg_color=None)
        self.btn_sim_tuning.configure(fg_color=("gray75", "gray30"))
        self.btn_loads_settings.configure(fg_color=None)
        self.btn_component_settings.configure(fg_color=None)

    def view_loads_settings(self):
        self.sim_settings_frame.grid_remove()
        self.sim_tuning_frame.grid_remove()
        self.sim_loads_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)
        self.sim_components_frame.grid_remove()

        self.btn_sim_settings.configure(fg_color=None)
        self.btn_sim_tuning.configure(fg_color=None)
        self.btn_loads_settings.configure(fg_color=("gray75", "gray30"))
        self.btn_component_settings.configure(fg_color=None)

    def view_components_settings(self):
        self.sim_settings_frame.grid_remove()
        self.sim_tuning_frame.grid_remove()
        self.sim_loads_frame.grid_remove()
        self.sim_components_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)

        self.btn_sim_settings.configure(fg_color=None)
        self.btn_sim_tuning.configure(fg_color=None)
        self.btn_loads_settings.configure(fg_color=None)
        self.btn_component_settings.configure(fg_color=("gray75", "gray30"))

    # results settings
    def create_results_frame(self):
        self.results_menu = customtkinter.CTkFrame(master=self,
                                                   width=180,
                                                   corner_radius=0)

        self.results_menu.grid_rowconfigure(0, minsize=10)
        self.results_menu.grid_rowconfigure((1, 2, 3, 4), weight=1)

        self.btn_results_conductor = customtkinter.CTkButton(master=self.results_menu,
                                                             text="Conductor Traces",
                                                             fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                             command=self.OnResultConductor)
        self.btn_results_conductor.pack(pady=10)

        self.btn_results_losses = customtkinter.CTkButton(master=self.results_menu,
                                                          text="Conduction Losses",
                                                          fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                          command=self.OnResultLosses)
        self.btn_results_losses.pack(pady=10)

        self.btn_results_temperature = customtkinter.CTkButton(master=self.results_menu,
                                                               text="Temperature",
                                                               fg_color=("gray75", "gray30"),  # <- custom tuple-color
                                                               command=self.OnResultsTemperature)
        self.btn_results_temperature.pack(pady=10)
        self.results_edit = customtkinter.CTkFrame(master=self)
        self.results_edit.grid_rowconfigure(0, weight=1)
        self.results_edit.grid_columnconfigure(0, weight=1)

    def create_result_figure_frame(self):
        self.results_figure_frame = customtkinter.CTkFrame(master=self.results_edit)
        self.results_figure_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nwse")
        self.results_figure_frame.rowconfigure(0, weight=1)
        self.results_figure_frame.columnconfigure(0, weight=1)

        self.result_layer_text = "Layer: "
        self.lbl_results_layer = customtkinter.CTkLabel(master=self.results_edit,
                                                        text=self.result_layer_text,
                                                        text_font=(
                                                            "Roboto Medium", -16))  # font name and size in px
        self.lbl_results_layer.grid(row=1, column=0, padx=5, pady=5, sticky="we")

        self.slider_layer = customtkinter.CTkSlider(master=self.results_edit,
                                                    from_=0,
                                                    to=self.layer_cnt - 1,
                                                    number_of_steps=self.layer_cnt - 1,
                                                    command=self.results_plot_update)
        self.results_state = 2
        self.slider_layer.set(0)
        self.slider_layer.grid(row=2, column=0, pady=10, padx=20, sticky="we")

        self.OnResultsTemperature()
        self.results_plot_update()

    def results_plot_update(self, event=None):
        which_layer = int(self.slider_layer.get())
        layer_name = self.heat_analysis.board.layers[which_layer].name

        self.lbl_results_layer.configure(text='Layer: ' + layer_name)

        self.result_figure = Figure()

        ax = self.result_figure.add_subplot()
        axes = [
            np.asarray(range(0,
                             self.heat_analysis.board.simulation.resolution * self.heat_analysis.board.mat_ht + 1,
                             self.heat_analysis.board.simulation.resolution)),
            np.asarray(range(0,
                             self.heat_analysis.board.simulation.resolution * self.heat_analysis.board.mat_wid + 1,
                             self.heat_analysis.board.simulation.resolution))]
        if self.results_state == 0:
            plot = ax.pcolormesh(axes[1], axes[0],
                                 np.transpose(np.where(self.heat_analysis.board.layers[which_layer].cond_mat > 0, 1, 0)),
                                 cmap='summer')
        elif self.results_state == 1:
            plot = ax.pcolormesh(axes[1], axes[0], np.transpose(self.heat_analysis.board.layers[which_layer].Q_mat), cmap='Wistia')
        elif self.results_state == 2:
            c_map_colors = ["darkblue", "dodgerblue", "yellowgreen", "orange", "red", "salmon", "mistyrose"]
            heat_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("heatcmap", c_map_colors)

            plot = ax.pcolormesh(axes[1], axes[0],  np.rot90(self.heat_analysis.temp_mat[which_layer]), cmap=heat_cmap)
            self.result_figure.colorbar(plot)
        ax.set_aspect('equal')
        ax.set_xlabel('X Position [mil]')
        ax.set_ylabel('Y Position [mil]')

        figure_canvas = FigureCanvasTkAgg(self.result_figure, master=self.results_figure_frame)
        self.results_figure_frame.bind("<Configure>", self.resize_window)

        figure_canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    def resize_window(self, event=None):
        win_wid = self.results_figure_frame.winfo_width()
        win_ht = self.results_edit.winfo_height()
        self.result_figure.set_size_inches(win_wid, win_ht)

    def OnResultConductor(self):
        self.btn_results_conductor.configure(fg_color=("gray75", "gray30"))
        self.btn_results_losses.configure(fg_color=None)
        self.btn_results_temperature.configure(fg_color=None)
        self.results_state = 0
        self.results_plot_update()

    def OnResultLosses(self):
        self.btn_results_conductor.configure(fg_color=None)
        self.btn_results_losses.configure(fg_color=("gray75", "gray30"))
        self.btn_results_temperature.configure(fg_color=None)
        self.results_state = 1
        self.results_plot_update()

    def OnResultsTemperature(self):
        self.btn_results_conductor.configure(fg_color=None)
        self.btn_results_losses.configure(fg_color=None)
        self.btn_results_temperature.configure(fg_color=("gray75", "gray30"))
        self.results_state = 2
        self.results_plot_update()

    def view_results(self):
        self.board_menu.grid_remove()
        self.board_edit.grid_remove()
        self.sim_menu.grid_remove()
        self.sim_edit.grid_remove()
        self.results_menu.grid(row=1, column=0, sticky="nswe")
        self.results_edit.grid(row=1, column=1, sticky="nswe", padx=20, pady=20)

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
