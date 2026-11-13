"""
Inventory and Reorder Tracker
A small desktop application for an electronics laboratory or shop.
Run: python app.py
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from tkinter import Tk, Toplevel, StringVar, messagebox, filedialog
from tkinter import ttk

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "inventory.csv"
MOVEMENTS_FILE = ROOT / "data" / "movements.csv"
ITEM_FIELDS = ["item_id", "name", "category", "quantity", "reorder_level", "unit_price", "updated_on"]
MOVEMENT_FIELDS = ["date", "item_id", "item_name", "movement", "quantity", "note"]


@dataclass
class Item:
    item_id: str
    name: str
    category: str
    quantity: int
    reorder_level: int
    unit_price: float
    updated_on: str

    @classmethod
    def from_row(cls, row: dict) -> "Item":
        item = cls(
            item_id=str(row["item_id"]).strip(),
            name=str(row["name"]).strip(),
            category=str(row["category"]).strip(),
            quantity=int(row["quantity"]),
            reorder_level=int(row["reorder_level"]),
            unit_price=round(float(row["unit_price"]), 2),
            updated_on=str(row.get("updated_on") or date.today().isoformat()).strip(),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if not self.item_id or not self.name or not self.category:
            raise ValueError("Item ID, name and category cannot be blank.")
        if self.quantity < 0 or self.reorder_level < 0:
            raise ValueError("Quantity and reorder level must be zero or greater.")
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        datetime.strptime(self.updated_on, "%Y-%m-%d")

    @property
    def status(self) -> str:
        if self.quantity == 0:
            return "OUT OF STOCK"
        if self.quantity <= self.reorder_level:
            return "REORDER"
        return "IN STOCK"


def load_items(path: Path = DATA_FILE) -> list[Item]:
    if not path.exists():
        return []
    loaded = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = set(ITEM_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError("CSV is missing columns: " + ", ".join(sorted(missing)))
        for line_no, row in enumerate(reader, start=2):
            try:
                loaded.append(Item.from_row(row))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid inventory row {line_no}: {exc}") from exc
    ids = [item.item_id for item in loaded]
    if len(ids) != len(set(ids)):
        raise ValueError("Item IDs must be unique.")
    return loaded


def save_items(items: list[Item], path: Path = DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ITEM_FIELDS)
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))


def log_movement(item: Item, movement: str, quantity: int, note: str = "") -> None:
    MOVEMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    exists = MOVEMENTS_FILE.exists()
    with MOVEMENTS_FILE.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MOVEMENT_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({
            "date": date.today().isoformat(), "item_id": item.item_id,
            "item_name": item.name, "movement": movement,
            "quantity": quantity, "note": note
        })


def get_summary(items: list[Item]) -> dict:
    quantities = np.array([item.quantity for item in items], dtype=float)
    values = np.array([item.quantity * item.unit_price for item in items], dtype=float)
    return {
        "items": len(items),
        "units": int(quantities.sum()) if len(quantities) else 0,
        "inventory_value": float(values.sum()) if len(values) else 0.0,
        "average_stock": float(np.mean(quantities)) if len(quantities) else 0.0,
        "reorder": sum(item.status == "REORDER" for item in items),
        "out": sum(item.status == "OUT OF STOCK" for item in items),
    }


def category_report(items: list[Item]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["category", "item_count", "units", "stock_value"])
    frame = pd.DataFrame([asdict(item) for item in items])
    frame["stock_value"] = frame["quantity"] * frame["unit_price"]
    return (frame.groupby("category", as_index=False)
            .agg(item_count=("item_id", "count"),
                 units=("quantity", "sum"),
                 stock_value=("stock_value", "sum"))
            .sort_values("category"))


def monthly_movement_report(path: Path = MOVEMENTS_FILE) -> pd.DataFrame:
    columns = ["month", "movement", "quantity"]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame["month"] = pd.to_datetime(frame["date"], errors="coerce").dt.to_period("M").astype(str)
    return (frame.groupby(["month", "movement"], as_index=False)["quantity"]
            .sum().sort_values(["month", "movement"]))


def export_json(items: list[Item], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump([asdict(item) | {"status": item.status} for item in items],
                  handle, indent=2)


class InventoryApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Inventory & Reorder Tracker")
        self.root.geometry("1080x680")
        self.items = load_items()
        self.search_var = StringVar()
        self.status_var = StringVar(value="All")
        self._build()
        self.refresh()

    def _build(self):
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="INVENTORY & REORDER TRACKER",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(header, text="Simple stock control for a small electronics lab or shop").pack(anchor="w")

        actions = ttk.Frame(self.root, padding=(12, 4))
        actions.pack(fill="x")
        for label, command in [
            ("Add item", self.add_item), ("Edit selected", self.edit_item),
            ("Delete selected", self.delete_item), ("Stock in / out", self.adjust_stock),
            ("Import CSV", self.import_csv), ("Export CSV", self.export_csv),
            ("Export JSON", self.export_json_file), ("Reports", self.show_reports),
        ]:
            ttk.Button(actions, text=label, command=command).pack(side="left", padx=3, pady=4)

        filters = ttk.Frame(self.root, padding=(12, 4))
        filters.pack(fill="x")
        ttk.Label(filters, text="Search:").pack(side="left")
        search = ttk.Entry(filters, textvariable=self.search_var, width=28)
        search.pack(side="left", padx=5)
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Label(filters, text="Status:").pack(side="left", padx=(16, 3))
        status = ttk.Combobox(filters, textvariable=self.status_var,
                              values=["All", "IN STOCK", "REORDER", "OUT OF STOCK"],
                              state="readonly", width=16)
        status.pack(side="left")
        status.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

        metrics = ttk.Frame(self.root, padding=12)
        metrics.pack(fill="x")
        self.metric_labels = {}
        for key, title in [("items", "ITEM TYPES"), ("units", "TOTAL UNITS"),
                           ("inventory_value", "STOCK VALUE (₹)"),
                           ("reorder", "REORDER ALERTS"), ("out", "OUT OF STOCK")]:
            card = ttk.LabelFrame(metrics, text=title, padding=10)
            card.pack(side="left", fill="x", expand=True, padx=4)
            label = ttk.Label(card, text="0", font=("Segoe UI", 16, "bold"))
            label.pack()
            self.metric_labels[key] = label

        table_frame = ttk.Frame(self.root, padding=12)
        table_frame.pack(fill="both", expand=True)
        cols = ("item_id", "name", "category", "quantity", "reorder_level",
                "unit_price", "status", "updated_on")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", height=17)
        headings = {
            "item_id": "Item ID", "name": "Item name", "category": "Category",
            "quantity": "Quantity", "reorder_level": "Reorder at",
            "unit_price": "Unit price (₹)", "status": "Status", "updated_on": "Updated"
        }
        widths = {"item_id": 90, "name": 190, "category": 130, "quantity": 85,
                  "reorder_level": 90, "unit_price": 110, "status": 130, "updated_on": 100}
        for col in cols:
            self.table.heading(col, text=headings[col])
            self.table.column(col, width=widths[col], anchor="center")
        self.table.tag_configure("alert", foreground="#a35b00")
        self.table.tag_configure("empty", foreground="#b00020")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.root.bind("<Delete>", lambda _event: self.delete_item())

    def refresh(self):
        query = self.search_var.get().lower().strip()
        chosen = self.status_var.get()
        for row in self.table.get_children():
            self.table.delete(row)
        visible = [item for item in self.items
                   if (query in item.item_id.lower() or query in item.name.lower()
                       or query in item.category.lower())
                   and (chosen == "All" or item.status == chosen)]
        for item in sorted(visible, key=lambda x: x.name.lower()):
            tag = "empty" if item.status == "OUT OF STOCK" else (
                "alert" if item.status == "REORDER" else "")
            self.table.insert("", "end", iid=item.item_id,
                values=(item.item_id, item.name, item.category, item.quantity,
                        item.reorder_level, f"{item.unit_price:.2f}",
                        item.status, item.updated_on), tags=(tag,))
        summary = get_summary(self.items)
        for key, label in self.metric_labels.items():
            value = summary[key]
            label.config(text=f"{value:,.2f}" if key == "inventory_value" else str(value))

    def selected_item(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Select item", "Please select an item from the table.")
            return None
        return next((x for x in self.items if x.item_id == selected[0]), None)

    def item_form(self, title, initial=None, on_save=None):
        win = Toplevel(self.root)
        win.title(title)
        win.transient(self.root)
        win.grab_set()
        fields = [
            ("Item ID", "item_id"), ("Item name", "name"), ("Category", "category"),
            ("Quantity", "quantity"), ("Reorder level", "reorder_level"),
            ("Unit price (₹)", "unit_price"), ("Updated on (YYYY-MM-DD)", "updated_on")
        ]
        vars_ = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(win, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=6)
            default = getattr(initial, key) if initial else (
                date.today().isoformat() if key == "updated_on" else "")
            var = StringVar(value=str(default))
            vars_[key] = var
            entry = ttk.Entry(win, textvariable=var, width=32)
            entry.grid(row=row, column=1, padx=10, pady=6)
            if initial and key == "item_id":
                entry.configure(state="readonly")
        def save():
            try:
                item = Item.from_row({key: var.get() for key, var in vars_.items()})
                on_save(item)
                win.destroy()
                self.refresh()
            except (ValueError, TypeError) as exc:
                messagebox.showerror("Invalid item", str(exc), parent=win)
        ttk.Button(win, text="Save", command=save).grid(row=len(fields), column=1, sticky="e", padx=10, pady=12)

    def add_item(self):
        def save(item):
            if any(x.item_id == item.item_id for x in self.items):
                raise ValueError("That Item ID already exists.")
            self.items.append(item)
            save_items(self.items)
            log_movement(item, "OPENING", item.quantity, "New item added")
        self.item_form("Add inventory item", on_save=save)

    def edit_item(self):
        old = self.selected_item()
        if old is None:
            return
        def save(item):
            index = self.items.index(old)
            self.items[index] = item
            save_items(self.items)
        self.item_form("Edit inventory item", initial=old, on_save=save)

    def delete_item(self):
        item = self.selected_item()
        if item is None:
            return
        if messagebox.askyesno("Confirm delete", f"Delete {item.name} ({item.item_id})?"):
            self.items.remove(item)
            save_items(self.items)
            self.refresh()

    def adjust_stock(self):
        item = self.selected_item()
        if item is None:
            return
        win = Toplevel(self.root)
        win.title("Stock in / out")
        win.transient(self.root)
        win.grab_set()
        ttk.Label(win, text=f"{item.name} — current stock: {item.quantity}",
                  font=("Segoe UI", 11, "bold")).pack(padx=12, pady=10)
        mode = StringVar(value="IN")
        ttk.Combobox(win, textvariable=mode, values=["IN", "OUT"],
                     state="readonly", width=12).pack(pady=4)
        qty = StringVar()
        ttk.Entry(win, textvariable=qty, width=15).pack(pady=4)
        note = StringVar()
        ttk.Entry(win, textvariable=note, width=32).pack(pady=4)
        ttk.Label(win, text="Quantity, then optional note").pack()
        def apply():
            try:
                amount = int(qty.get())
                if amount <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                if mode.get() == "OUT" and amount > item.quantity:
                    raise ValueError("Cannot issue more units than available.")
                item.quantity += amount if mode.get() == "IN" else -amount
                item.updated_on = date.today().isoformat()
                save_items(self.items)
                log_movement(item, mode.get(), amount, note.get())
                win.destroy()
                self.refresh()
            except ValueError as exc:
                messagebox.showerror("Invalid stock movement", str(exc), parent=win)
        ttk.Button(win, text="Apply movement", command=apply).pack(pady=12)

    def import_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filename:
            return
        try:
            incoming = load_items(Path(filename))
            existing = {x.item_id for x in self.items}
            duplicates = existing.intersection(x.item_id for x in incoming)
            if duplicates:
                raise ValueError("Duplicate Item IDs found: " + ", ".join(sorted(duplicates)))
            self.items.extend(incoming)
            save_items(self.items)
            self.refresh()
            messagebox.showinfo("Import complete", f"Imported {len(incoming)} item(s).")
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv")])
        if filename:
            save_items(self.items, Path(filename))
            messagebox.showinfo("Export complete", "Inventory CSV exported.")

    def export_json_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")])
        if filename:
            export_json(self.items, Path(filename))
            messagebox.showinfo("Export complete", "Inventory JSON exported.")

    def show_reports(self):
        summary = get_summary(self.items)
        report = category_report(self.items)
        monthly = monthly_movement_report()
        win = Toplevel(self.root)
        win.title("Inventory reports")
        win.geometry("760x520")
        text = (
            f"Inventory overview\n"
            f"Item types: {summary['items']}\nTotal units: {summary['units']}\n"
            f"Stock value: ₹{summary['inventory_value']:,.2f}\n"
            f"Average units per item: {summary['average_stock']:.2f}\n"
            f"Reorder alerts: {summary['reorder']} | Out of stock: {summary['out']}\n\n"
            f"Category summary (Pandas)\n{report.to_string(index=False)}\n\n"
            f"Monthly stock movements\n{monthly.to_string(index=False) if not monthly.empty else 'No stock movements recorded yet.'}"
        )
        box = ttk.Label(win, text=text, justify="left", font=("Consolas", 10))
        box.pack(anchor="nw", padx=14, pady=14)
        ttk.Button(win, text="Show category chart", command=lambda: self.show_chart(report)).pack(anchor="w", padx=14)

    def show_chart(self, report):
        if report.empty:
            messagebox.showinfo("No data", "There are no category records to chart.")
            return
        plt.figure(figsize=(7, 4))
        plt.bar(report["category"], report["units"])
        plt.title("Available units by category")
        plt.xlabel("Category")
        plt.ylabel("Units in stock")
        plt.tight_layout()
        plt.show()


def main():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        save_items([
            Item("EL001", "Resistor 1kΩ", "Passive", 120, 30, 0.50, date.today().isoformat()),
            Item("EL002", "LED Red 5mm", "Semiconductor", 18, 25, 1.50, date.today().isoformat()),
            Item("EL003", "BC547 Transistor", "Semiconductor", 42, 15, 3.00, date.today().isoformat()),
            Item("EL004", "Breadboard", "Tools", 7, 10, 85.00, date.today().isoformat()),
            Item("EL005", "Jumper Wire Set", "Tools", 0, 5, 35.00, date.today().isoformat()),
            Item("EL006", "Capacitor 100µF", "Passive", 55, 20, 2.00, date.today().isoformat()),
            Item("EL007", "IC 555 Timer", "IC", 12, 10, 18.00, date.today().isoformat()),
            Item("EL008", "Diode 1N4007", "Semiconductor", 28, 20, 1.00, date.today().isoformat()),
        ])
    root = Tk()
    InventoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
