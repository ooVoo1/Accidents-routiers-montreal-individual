import customtkinter as ctk
import pandas as pd
from tkinter import messagebox

class MapMaker(ctk.CTkFrame):
    def __init__(self, master, handler):
        super().__init__(master)
        