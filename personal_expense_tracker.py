import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import json
import os

APP_TITLE = "Personal Expense Tracker"
CATEGORIES = ["Food", "Transport", "Shopping", "Other"]
DATA_FILE = "expenses_data.json"

class ExpenseTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x720")
        self.configure(bg="#0f172a")

        # Data
        self.expenses = []
        self.budgets = {c: 0.0 for c in CATEGORIES}

        # Try loading saved data
        self.load_data()

        # UI: Notebook (tabs)
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_add = ttk.Frame(notebook)
        self.tab_ledger = ttk.Frame(notebook)
        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_budget = ttk.Frame(notebook)

        notebook.add(self.tab_add, text="Add Expense")
        notebook.add(self.tab_ledger, text="Ledger")
        notebook.add(self.tab_dashboard, text="Dashboard")
        notebook.add(self.tab_budget, text="Budgets")

        self.build_add_tab()
        self.build_ledger_tab()
        self.build_dashboard_tab()
        self.build_budgets_tab()

        # Initial refresh
        self.update_ledger()
        self.update_dashboard()
        self.update_budgets_view()

        # Add menu for saving/loading
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save Now", command=self.save_data)
        filemenu.add_command(label="Load", command=self.load_data)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    # ====================== DATA SAVE/LOAD ======================
    def save_data(self):
        data = {"expenses": self.expenses, "budgets": self.budgets}
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Saved", f"Data saved to {DATA_FILE}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save: {e}")

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                self.expenses = data.get("expenses", [])
                self.budgets = data.get("budgets", {c: 0.0 for c in CATEGORIES})
                messagebox.showinfo("Loaded", f"Data loaded from {DATA_FILE}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load data: {e}")
        else:
            self.expenses = []
            self.budgets = {c: 0.0 for c in CATEGORIES}

    # ====================== ADD EXPENSE TAB ======================
    def build_add_tab(self):
        frame = ttk.Frame(self.tab_add, padding=20)
        frame.pack(fill="both", expand=True)

        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.note_var = tk.StringVar()

        ttk.Label(frame, text="Amount:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.amount_var).grid(row=0, column=1, pady=6, sticky="ew")

        ttk.Label(frame, text="Category:").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Combobox(frame, values=CATEGORIES, textvariable=self.category_var, state="readonly").grid(row=1, column=1, pady=6, sticky="ew")

        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.date_var).grid(row=2, column=1, pady=6, sticky="ew")

        ttk.Label(frame, text="Note:").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.note_var).grid(row=3, column=1, pady=6, sticky="ew")

        frame.columnconfigure(1, weight=1)

        ttk.Button(frame, text="Add Expense", command=self.add_expense).grid(row=4, column=0, columnspan=2, pady=12)
        self.feedback = ttk.Label(frame, text="", foreground="green")
        self.feedback.grid(row=5, column=0, columnspan=2)

    def add_expense(self):
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.feedback.config(text="❌ Enter a valid positive number", foreground="red")
            return

        expense = {"amount": amount, "category": self.category_var.get(),
                   "date": self.date_var.get(), "note": self.note_var.get()}
        self.expenses.append(expense)
        self.feedback.config(text="✅ Expense Added!", foreground="green")

        self.update_ledger()
        self.update_dashboard()
        self.update_budgets_view()
        self.maybe_alert_budget(expense["category"])
        self.save_data()  # auto-save

        self.amount_var.set("")
        self.note_var.set("")

    # ====================== LEDGER TAB ======================
    def build_ledger_tab(self):
        frame = ttk.Frame(self.tab_ledger, padding=20)
        frame.pack(fill="both", expand=True)

        columns = ("date", "amount", "category", "note")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.column("date", width=120)
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("category", width=120)
        self.tree.column("note", width=500)
        self.tree.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(frame, padding=10)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Edit", command=self.edit_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_selected).pack(side="left", padx=5)

    def update_ledger(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for exp in self.expenses:
            self.tree.insert("", "end", values=(exp["date"], f"{exp['amount']:.2f}", exp["category"], exp["note"]))

    def get_selected_index(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.index(selected[0])

    def delete_selected(self):
        idx = self.get_selected_index()
        if idx is not None:
            if messagebox.askyesno("Confirm", "Delete this expense?"):
                self.expenses.pop(idx)
                self.update_ledger()
                self.update_dashboard()
                self.update_budgets_view()
                self.save_data()

    def edit_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        exp = self.expenses[idx]

        win = tk.Toplevel(self)
        win.title("Edit Expense")
        win.geometry("300x250")

        amount_var = tk.StringVar(value=str(exp["amount"]))
        category_var = tk.StringVar(value=exp["category"])
        date_var = tk.StringVar(value=exp["date"])
        note_var = tk.StringVar(value=exp["note"])

        ttk.Label(win, text="Amount").pack()
        ttk.Entry(win, textvariable=amount_var).pack()
        ttk.Label(win, text="Category").pack()
        ttk.Combobox(win, values=CATEGORIES, textvariable=category_var, state="readonly").pack()
        ttk.Label(win, text="Date").pack()
        ttk.Entry(win, textvariable=date_var).pack()
        ttk.Label(win, text="Note").pack()
        ttk.Entry(win, textvariable=note_var).pack()

        def save_changes():
            try:
                new_amt = float(amount_var.get())
                if new_amt <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Amount must be positive")
                return
            exp.update({"amount": new_amt, "category": category_var.get(),
                        "date": date_var.get(), "note": note_var.get()})
            self.update_ledger()
            self.update_dashboard()
            self.update_budgets_view()
            self.maybe_alert_budget(exp["category"])
            self.save_data()
            win.destroy()

        ttk.Button(win, text="Save", command=save_changes).pack(pady=8)

    # ====================== DASHBOARD TAB ======================
    def build_dashboard_tab(self):
        self.dash_frame = ttk.Frame(self.tab_dashboard, padding=20)
        self.dash_frame.pack(fill="both", expand=True)
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(9.5, 4.8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.dash_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_dashboard(self):
        self.ax1.clear()
        self.ax2.clear()
        if not self.expenses:
            self.ax1.text(0.5,0.5,"No data yet",ha="center",va="center")
            self.ax2.text(0.5,0.5,"No data yet",ha="center",va="center")
        else:
            cat_totals = {}
            for e in self.expenses:
                cat_totals[e["category"]] = cat_totals.get(e["category"],0)+e["amount"]
            colors = plt.cm.Set3(np.linspace(0,1,max(3,len(cat_totals))))
            self.ax1.pie(cat_totals.values(),labels=cat_totals.keys(),autopct="%1.1f%%",colors=colors)
            self.ax1.set_title("By Category")

            daily = {}
            for e in self.expenses:
                d=e["date"]
                if d not in daily: daily[d]={}
                daily[d][e["category"]] = daily[d].get(e["category"],0)+e["amount"]
            days = sorted(daily.keys())
            cats = sorted({c for v in daily.values() for c in v})
            stack={c:[daily[d].get(c,0) for d in days] for c in cats}
            colors=plt.cm.tab20(np.linspace(0,1,max(3,len(cats))))
            bottom=np.zeros(len(days))
            for i,c in enumerate(cats):
                self.ax2.bar(days,stack[c],bottom=bottom,label=c,color=colors[i])
                bottom+=np.array(stack[c])
            self.ax2.set_title("Daily (stacked)")
            self.ax2.tick_params(axis="x",rotation=45)
            self.ax2.legend(fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

    # ====================== BUDGETS TAB ======================
    def build_budgets_tab(self):
        self.b_frame = ttk.Frame(self.tab_budget, padding=16)
        self.b_frame.pack(fill="both", expand=True)
        self.budget_entries={}
        self.spent_labels={}
        self.remain_labels={}
        self.progress_bars={}

        for cat in CATEGORIES:
            row=ttk.Frame(self.b_frame)
            row.pack(fill="x", pady=6)
            ttk.Label(row,text=cat,width=12).grid(row=0,column=0,sticky="w")
            e=ttk.Entry(row,width=10)
            e.insert(0,f"{self.budgets.get(cat,0):.2f}")
            e.grid(row=0,column=1)
            self.budget_entries[cat]=e
            self.spent_labels[cat]=ttk.Label(row,text="0.00",width=10)
            self.spent_labels[cat].grid(row=0,column=2)
            self.remain_labels[cat]=ttk.Label(row,text="0.00",width=10)
            self.remain_labels[cat].grid(row=0,column=3)
            pb=ttk.Progressbar(row,length=250,mode="determinate",maximum=100)
            pb.grid(row=0,column=4,padx=8)
            self.progress_bars[cat]=pb
            ttk.Button(row,text="Save",command=lambda c=cat:self.save_budget_for(c)).grid(row=0,column=5,padx=4)

        ttk.Button(self.b_frame,text="Save All",command=self.save_all_budgets).pack(pady=6)
        self.update_budgets_view()

    def save_budget_for(self,category):
        val=self._parse_budget_entry(self.budget_entries[category].get())
        if val is None:
            messagebox.showerror("Invalid",f"Budget for {category} must be number >=0")
            return
        self.budgets[category]=val
        self.budget_entries[category].delete(0,tk.END)
        self.budget_entries[category].insert(0,f"{val:.2f}")
        self.update_budgets_view()
        self.maybe_alert_budget(category)
        self.save_data()

    def save_all_budgets(self):
        for cat in CATEGORIES:
            v=self._parse_budget_entry(self.budget_entries[cat].get())
            if v is None:
                messagebox.showerror("Invalid",f"Budget for {cat} must be number >=0")
                return
        for cat in CATEGORIES:
            v=float(self.budget_entries[cat].get())
            self.budgets[cat]=v
            self.budget_entries[cat].delete(0,tk.END)
            self.budget_entries[cat].insert(0,f"{v:.2f}")
        self.update_budgets_view()
        for cat in CATEGORIES:self.maybe_alert_budget(cat)
        self.save_data()

    def _parse_budget_entry(self,s):
        try:
            v=float(s);return v if v>=0 else None
        except: return None

    def calc_spent_per_category(self):
        spent={c:0.0 for c in CATEGORIES}
        for e in self.expenses:
            spent[e["category"]]+=e["amount"]
        return spent

    def update_budgets_view(self):
        spent=self.calc_spent_per_category()
        for cat in CATEGORIES:
            b=self.budgets.get(cat,0.0)
            s=spent[cat]
            remain=(b-s) if b>0 else float("inf")
            self.spent_labels[cat].config(text=f"{s:.2f}")
            self.remain_labels[cat].config(text=("∞" if b==0 else f"{remain:.2f}"))
            if b>0:self.progress_bars[cat]["value"]=min(100,(s/b)*100)
            else:self.progress_bars[cat]["value"]=0
            if b>0 and s>b:self.spent_labels[cat].config(foreground="red")
            elif b>0 and s>=0.9*b:self.spent_labels[cat].config(foreground="orange")
            else:self.spent_labels[cat].config(foreground="black")

    def maybe_alert_budget(self,category):
        b=self.budgets.get(category,0)
        if b<=0:return
        s=self.calc_spent_per_category()[category]
        if s>b:
            messagebox.showwarning("Budget Exceeded",f"{category} budget exceeded!\nBudget: {b:.2f}, Spent: {s:.2f}")
        elif s>=0.9*b:
            messagebox.showinfo("Budget Near Limit",f"{category} budget nearly reached.\nBudget: {b:.2f}, Spent: {s:.2f}")

if __name__=="__main__":
    app=ExpenseTracker()
    app.mainloop()
