import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.table import Table
import tkinter as tk
from tkinter import filedialog, Text, Scrollbar, Checkbutton, IntVar
from io import StringIO
import hashlib
import os


# Load CSV function with robust parsing
def load_csv(file_path):
    try:
        df = pd.read_csv(
            file_path,
            header=0,
            skiprows=[1],  # Skip only the blank row after headers
            skipfooter=0,
            engine='python',
            na_values=['N/A', '-', ''],
            delimiter=',',
            quotechar='"',  # Handle quoted fields
            thousands=',',  # Parse commas in numbers
        )
        df = df.dropna(how='all').dropna(axis=1, how='all')

        # Convert numeric columns to floats
        numeric_cols = ['Qty', 'Purchase Costs', 'Hours', 'Times Out', 'Income']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Strip whitespace from string columns
        str_cols = ['Category', 'Item Key', 'Name']
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].str.strip()

        print(f"Data imported successfully! Loaded {len(df)} rows— that's a factorial waiting to happen if it were smaller.")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None


# Visualize function with enhanced validation
def visualize_data(df, text_area, canvas_frame):
    if df is None:
        text_area.insert(tk.END, "No data loaded.\n")
        return

    # Clear previous content
    text_area.delete(1.0, tk.END)

    # Text summaries
    text_area.insert(tk.END, "First 5 rows:\n" + str(df.head()) + "\n\n")
    text_area.insert(tk.END, "Last 5 rows:\n" + str(df.tail()) + "\n\n")

    # Capture df.info() output
    buffer = StringIO()
    df.info(buf=buffer, verbose=False)
    text_area.insert(tk.END, "Data info:\n" + buffer.getvalue() + "\n")
    text_area.insert(tk.END, "Summary stats:\n" + str(df.describe()) + "\n\n")

    # Validation checks
    text_area.insert(tk.END, "Validation Checks:\n")
    text_area.insert(tk.END, f"Total rows: {len(df)}\n")
    text_area.insert(tk.END, f"Total columns: {len(df.columns)}\n")
    text_area.insert(tk.END, f"Column names: {df.columns.tolist()}\n")
    text_area.insert(tk.END, f"Unique Categories: {df['Category'].nunique() if 'Category' in df else 'N/A'}\n")
    text_area.insert(tk.END, f"Unique Item Keys: {df['Item Key'].nunique() if 'Item Key' in df else 'N/A'}\n")
    text_area.insert(tk.END, f"Unique Names: {df['Name'].nunique() if 'Name' in df else 'N/A'}\n")
    text_area.insert(tk.END, f"Total Income: {df['Income'].sum():,.2f}\n")
    text_area.insert(tk.END, f"Missing values per column:\n{str(df.isnull().sum())}\n")

    # Row hash for data integrity
    row_hash = hashlib.md5(df.to_string().encode()).hexdigest()[:8]
    text_area.insert(tk.END, f"Data hash (first 8 chars): {row_hash}\n\n")

    # Clear previous canvas
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    # Matplotlib table viz (top 10 rows)
    fig, ax = plt.subplots(figsize=(12, 5))  # Wider for column names
    ax.axis('off')
    table = Table(ax, bbox=[0, 0, 1, 1])

    # Headers
    for j, col in enumerate(df.columns):
        table.add_cell(0, j, width=1 / len(df.columns), height=0.05, text=col, loc='center', facecolor='lightgray')

    # Data rows (top 10)
    for i in range(min(10, len(df))):
        for j, val in enumerate(df.iloc[i]):
            table.add_cell(i + 1, j, width=1 / len(df.columns), height=0.05, text=str(val), loc='center')

    ax.add_table(table)
    fig.suptitle("Sample Data Table View")

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    print(f"Visualized data! Unique categories count: {df['Category'].nunique() if 'Category' in df else 'N/A'}— prime for some grouping algebra.")


# Plot aggregation with optional grouping
def plot_aggregation(df, canvas_frame, group_trade_show, group_tent):
    if df is None:
        return

    # Clear previous canvas
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    # Optionally group categories
    plot_df = df.copy()
    original_unique = plot_df['Category'].nunique()
    print(f"Starting plot with {original_unique} unique categories— let's see if we can reduce that dimension.")

    if group_trade_show:
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Trade Show' if isinstance(x, str) and 'Trade Show' in x else x)
        print("Grouped Trade Show categories: Combining coefficients like in a polynomial.")

    if group_tent:
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Tent' if isinstance(x, str) and 'Tent' in x else x)
        print("Grouped Tent categories: Merging terms to simplify the category equation.")

    updated_unique = plot_df['Category'].nunique()
    print(f"After grouping, unique categories: {updated_unique}. Reduction by {original_unique - updated_unique}— that's subtractive fun!")

    # Aggregate: Sum Income by Category, sort descending
    agg_df = plot_df.groupby('Category')['Income'].sum().reset_index().sort_values('Income', ascending=False)

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(agg_df['Category'], agg_df['Income'], color='#1f77b4')
    title = "Total Income by Category (Sorted)"
    if group_trade_show:
        title += " - Trade Shows Grouped"
    if group_tent:
        title += " - Tents Grouped"
    ax.set_title(title)
    ax.set_xlabel("Category")
    ax.set_ylabel("Income ($)")
    plt.xticks(rotation=45, ha='right', fontsize=7)  # Smaller font
    plt.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])  # Extra padding

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    print("Plot rendered! Total income summed: {0:,.2f}— a grand total in the ledger of numbers.".format(agg_df['Income'].sum()))


# Export cleaned DF to CSV
def export_csv(df):
    if df is None:
        return
    file_path = filedialog.asksaveasfilename(title="Save Cleaned CSV", defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")])
    if file_path:
        df.to_csv(file_path, index=False)
        print(f"Exported cleaned data to {file_path}. File size in bytes: {os.path.getsize(file_path)}— counting every bit.")


# Tkinter UI setup
def create_ui():
    root = tk.Tk()
    root.title("NumberCruncher - Enhanced Interface")
    root.geometry("900x700")

    # Configure grid for proportions
    root.grid_columnconfigure(0, weight=0)  # Toolbar column
    root.grid_columnconfigure(1, weight=1)  # Content column
    root.grid_rowconfigure(0, weight=9)    # Canvas row (90%)
    root.grid_rowconfigure(1, weight=1)    # Text row (10%)

    # Toolbar frame on left
    toolbar_frame = tk.Frame(root)
    toolbar_frame.grid(row=0, column=0, rowspan=2, sticky='ns', padx=10, pady=10)

    # Load CSV button
    load_button = tk.Button(toolbar_frame, text="Load CSV", command=lambda: load_file(root))
    load_button.pack(fill=tk.X, pady=5)

    # Plot aggregation button
    plot_button = tk.Button(toolbar_frame, text="Plot Income by Category", state=tk.DISABLED)
    plot_button.pack(fill=tk.X, pady=5)

    # Group Trade Show checkbox
    group_trade_var = IntVar(value=1)  # Default to grouped
    group_trade_check = Checkbutton(toolbar_frame, text="Group Trade Show Categories", variable=group_trade_var)
    group_trade_check.pack(fill=tk.X, pady=5)

    # Group Tent checkbox
    group_tent_var = IntVar(value=1)  # Default to grouped
    group_tent_check = Checkbutton(toolbar_frame, text="Group Tent Categories", variable=group_tent_var)
    group_tent_check.pack(fill=tk.X, pady=5)

    # Export button
    export_button = tk.Button(toolbar_frame, text="Export Cleaned CSV", state=tk.DISABLED)
    export_button.pack(fill=tk.X, pady=5)

    # Frame for Matplotlib canvas (top right)
    canvas_frame = tk.Frame(root)
    canvas_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

    # Text area for summaries (bottom right)
    text_frame = tk.Frame(root)
    text_frame.grid(row=1, column=1, sticky='ew', padx=10, pady=10)
    scrollbar = Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area = Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=5)  # Approximate height for 10%
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_area.yview)

    def load_file(root):
        file_path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV files", "*.csv")])
        if file_path:
            df = load_csv(file_path)
            if df is not None:
                visualize_data(df, text_area, canvas_frame)
                plot_button.config(state=tk.NORMAL, command=lambda: plot_aggregation(df, canvas_frame, bool(group_trade_var.get()), bool(group_tent_var.get())))
                export_button.config(state=tk.NORMAL, command=lambda: export_csv(df))

    root.mainloop()


if __name__ == "__main__":
    create_ui()