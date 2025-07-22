import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.table import Table
import tkinter as tk
from tkinter import Text, Scrollbar, Checkbutton, IntVar
from io import StringIO
import hashlib
import os
import re


# Load CSV function with robust parsing and cleaning
def load_csv(file_path):
    try:
        df = pd.read_csv(
            file_path,
            header=0,
            skiprows=[1],  # Skip only the blank row after headers if present
            skipfooter=0,
            engine='python',
            na_values=['N/A', '-', ''],
            delimiter=',',
            quotechar='"',  # Handle quoted fields
            thousands=',',  # Parse commas in numbers
            usecols=[4, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
        )
        # Assign fixed column names
        df.columns = ['Category', 'Item Key', 'Name', 'Quantity', 'Purchase Cost', 'Hours', 'T/O', 'Income', 'ROI', 'Avg Yrl ROI', 'Subrental', 'Repair']

        # Remove entirely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')

        # Remove repeated header rows where 'Item Key' == 'Item Key'
        df = df[df['Item Key'] != 'Item Key']

        # Convert numeric columns to floats
        numeric_cols = ['Quantity', 'Purchase Cost', 'Hours', 'T/O', 'Income', 'ROI', 'Avg Yrl ROI', 'Subrental', 'Repair']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Strip whitespace from string columns
        str_cols = ['Category', 'Item Key', 'Name']
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].str.strip()

        # Drop any remaining rows that are all NaN in numeric columns
        df = df.dropna(subset=numeric_cols, how='all')

        print(f"Data imported successfully from {file_path}! Loaded {len(df)} rows.")
        return df
    except Exception as e:
        print(f"Error loading CSV {file_path}: {e}")
        return None


# Visualize function with enhanced validation
def visualize_data(df, text_area, canvas_frame):
    if df is None or df.empty:
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

    print(f"Visualized data! Unique categories count: {df['Category'].nunique() if 'Category' in df else 'N/A'}.")


# Plot aggregation with optional grouping, year selection, and axis toggle
def plot_aggregation(df, canvas_frame, group_trade_show, group_tent, group_creative, group_av, group_tabletop, group_party, group_lav, selected_years, by_year, include_trade_show, include_tent, include_creative, include_av, include_tabletop, include_party, include_lav):
    if df is None or df.empty:
        return

    # Filter by selected years
    plot_df = df[df['Year'].isin(selected_years)].copy()
    if plot_df.empty:
        return

    original_unique = plot_df['Category'].nunique()
    print(f"Starting plot with {original_unique} unique categories.")

    # Exclude categories based on include checkboxes
    if not include_trade_show:
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and ('Trade Show' in x or x == 'Show Turf and Flooring' or x == 'Electrical Distribution Equipment'))]
        print("Excluded Trade Show categories.")

    if not include_tent:
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and 'Tent' in x)]
        print("Excluded Tent categories.")

    if not include_creative:
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and ('Creative' in x or x == 'Event Props'))]
        print("Excluded Creative categories.")

    if not include_av:
        av_categories = ['Audio', 'Video Display', 'Lighting AV', 'Presentation Aid', 'Lighting', 'Video Camera']
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and x in av_categories)]
        print("Excluded Audio/Visual categories.")

    if not include_tabletop:
        tabletop_keywords = ['Linen', 'Napkin', 'Flatware', 'Dishware', 'Glassware', 'Beverage Dispensers', 'Concession Equipment', 'Platters & Serving', 'Chargers']
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and any(kw in x for kw in tabletop_keywords))]
        print("Excluded Table Top categories.")

    if not include_party:
        party_categories = ['Chairs', 'Tables', 'Miscellaneous  Party', 'Staging', 'Cooling & Heating Equipment', 'Dividers and Fencing', 'Dance Floor', 'Grills & Griddles']
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and x in party_categories)]
        print("Excluded Party Rental categories.")

    if not include_lav:
        lav_categories = ['Luxury Restroom & Shower Trailers', 'Refrigerator & Freezer Trailers']
        plot_df = plot_df[~plot_df['Category'].apply(lambda x: isinstance(x, str) and x in lav_categories)]
        print("Excluded Lavatory categories.")

    # Apply groupings only if included and group checked
    if group_trade_show and include_trade_show:
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Trade Show' if isinstance(x, str) and ('Trade Show' in x or x == 'Show Turf and Flooring' or x == 'Electrical Distribution Equipment') else x)
        print("Grouped Trade Show categories.")

    if group_tent and include_tent:
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Tent' if isinstance(x, str) and 'Tent' in x else x)
        print("Grouped Tent categories.")

    if group_creative and include_creative:
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Creative' if isinstance(x, str) and ('Creative' in x or x == 'Event Props') else x)
        print("Grouped Creative categories.")

    if group_av and include_av:
        av_categories = ['Audio', 'Video Display', 'Lighting AV', 'Presentation Aid', 'Lighting', 'Video Camera']
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Audio/Visual' if isinstance(x, str) and x in av_categories else x)
        print("Grouped Audio/Visual categories.")

    if group_tabletop and include_tabletop:
        tabletop_keywords = ['Linen', 'Napkin', 'Flatware', 'Dishware', 'Glassware', 'Beverage Dispensers', 'Concession Equipment', 'Platters & Serving', 'Chargers']
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Table Top' if isinstance(x, str) and any(kw in x for kw in tabletop_keywords) else x)
        print("Grouped Table Top categories.")

    if group_party and include_party:
        party_categories = ['Chairs', 'Tables', 'Miscellaneous  Party', 'Staging', 'Cooling & Heating Equipment', 'Dividers and Fencing', 'Dance Floor', 'Grills & Griddles']
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Party Rental' if isinstance(x, str) and x in party_categories else x)
        print("Grouped Party Rental categories.")

    if group_lav and include_lav:
        lav_categories = ['Luxury Restroom & Shower Trailers', 'Refrigerator & Freezer Trailers']
        plot_df['Category'] = plot_df['Category'].apply(lambda x: 'Lavatory' if isinstance(x, str) and x in lav_categories else x)
        print("Grouped Lavatory categories.")

    updated_unique = plot_df['Category'].nunique()
    print(f"After grouping, unique categories: {updated_unique}. Reduction by {original_unique - updated_unique}.")

    # Aggregate based on axis choice
    if by_year:
        agg_df = plot_df.groupby(['Year', 'Category'])['Income'].sum().unstack(fill_value=0)
        agg_df = agg_df.sort_index(ascending=True)  # Sort years chronologically
        x_label = "Year"
        title = "Total Income by Year and Category (Chronological)"
    else:
        agg_df = plot_df.groupby(['Category', 'Year'])['Income'].sum().unstack(fill_value=0)
        agg_df = agg_df.loc[agg_df.sum(axis=1).sort_values(ascending=False).index]  # Sort categories by total income
        x_label = "Category"
        title = "Total Income by Category and Year (Sorted)"

    if group_trade_show and include_trade_show:
        title += " - Trade Shows Grouped"
    if group_tent and include_tent:
        title += " - Tents Grouped"
    if group_creative and include_creative:
        title += " - Creatives Grouped"
    if group_av and include_av:
        title += " - Audio/Visual Grouped"
    if group_tabletop and include_tabletop:
        title += " - Table Top Grouped"
    if group_party and include_party:
        title += " - Party Rentals Grouped"
    if group_lav and include_lav:
        title += " - Lavatories Grouped"

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    agg_df.plot(kind='bar', ax=ax, color=plt.cm.Paired(range(len(agg_df.columns))))
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Income ($)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{x:,.0f}'))
    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.legend(title='Category' if by_year else 'Year')
    plt.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])

    # Clear previous canvas
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    print("Plot rendered! Total income summed: {0:,.2f}.".format(agg_df.sum().sum()))


# Export cleaned DF to CSV
def export_csv(df):
    if df is None or df.empty:
        return
    file_path = tk.filedialog.asksaveasfilename(title="Save Cleaned CSV", defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv")])
    if file_path:
        df.to_csv(file_path, index=False)
        print(f"Exported cleaned data to {file_path}. File size in bytes: {os.path.getsize(file_path)}.")


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

    # Load All Data button
    load_button = tk.Button(toolbar_frame, text="Load All Data", command=lambda: load_all_data(root))
    load_button.pack(fill=tk.X, pady=5)

    # Plot aggregation button
    plot_button = tk.Button(toolbar_frame, text="Plot Income by Category", state=tk.DISABLED)
    plot_button.pack(fill=tk.X, pady=5)

    # Axis toggle button
    axis_var = IntVar(value=0)  # 0 for Category, 1 for Year
    axis_button = tk.Button(toolbar_frame, text="Switch to Year Axis", command=lambda: toggle_axis(root, axis_var, plot_button))
    axis_button.pack(fill=tk.X, pady=5)

    # Group and Include checkboxes
    group_trade_var = IntVar(value=1)
    include_trade_var = IntVar(value=1)
    trade_frame = tk.Frame(toolbar_frame)
    trade_frame.pack(fill=tk.X, pady=5)
    Checkbutton(trade_frame, text="Group Trade Show Categories", variable=group_trade_var).pack(side=tk.LEFT)
    Checkbutton(trade_frame, text="Include Trade Show", variable=include_trade_var).pack(side=tk.LEFT)

    group_tent_var = IntVar(value=1)
    include_tent_var = IntVar(value=1)
    tent_frame = tk.Frame(toolbar_frame)
    tent_frame.pack(fill=tk.X, pady=5)
    Checkbutton(tent_frame, text="Group Tent Categories", variable=group_tent_var).pack(side=tk.LEFT)
    Checkbutton(tent_frame, text="Include Tent", variable=include_tent_var).pack(side=tk.LEFT)

    group_creative_var = IntVar(value=1)
    include_creative_var = IntVar(value=1)
    creative_frame = tk.Frame(toolbar_frame)
    creative_frame.pack(fill=tk.X, pady=5)
    Checkbutton(creative_frame, text="Group Creative Categories", variable=group_creative_var).pack(side=tk.LEFT)
    Checkbutton(creative_frame, text="Include Creative", variable=include_creative_var).pack(side=tk.LEFT)

    group_av_var = IntVar(value=1)
    include_av_var = IntVar(value=1)
    av_frame = tk.Frame(toolbar_frame)
    av_frame.pack(fill=tk.X, pady=5)
    Checkbutton(av_frame, text="Group Audio/Visual Categories", variable=group_av_var).pack(side=tk.LEFT)
    Checkbutton(av_frame, text="Include Audio/Visual", variable=include_av_var).pack(side=tk.LEFT)

    group_tabletop_var = IntVar(value=1)
    include_tabletop_var = IntVar(value=1)
    tabletop_frame = tk.Frame(toolbar_frame)
    tabletop_frame.pack(fill=tk.X, pady=5)
    Checkbutton(tabletop_frame, text="Group Table Top Categories", variable=group_tabletop_var).pack(side=tk.LEFT)
    Checkbutton(tabletop_frame, text="Include Table Top", variable=include_tabletop_var).pack(side=tk.LEFT)

    group_party_var = IntVar(value=1)
    include_party_var = IntVar(value=1)
    party_frame = tk.Frame(toolbar_frame)
    party_frame.pack(fill=tk.X, pady=5)
    Checkbutton(party_frame, text="Group Party Rental Categories", variable=group_party_var).pack(side=tk.LEFT)
    Checkbutton(party_frame, text="Include Party Rental", variable=include_party_var).pack(side=tk.LEFT)

    group_lav_var = IntVar(value=1)
    include_lav_var = IntVar(value=1)
    lav_frame = tk.Frame(toolbar_frame)
    lav_frame.pack(fill=tk.X, pady=5)
    Checkbutton(lav_frame, text="Group Lavatory Categories", variable=group_lav_var).pack(side=tk.LEFT)
    Checkbutton(lav_frame, text="Include Lavatory", variable=include_lav_var).pack(side=tk.LEFT)

    # Year checkboxes
    year_vars = {year: IntVar(value=1) for year in range(2015, 2025)}
    for year in sorted(year_vars.keys()):
        Checkbutton(toolbar_frame, text=f"Include {year}", variable=year_vars[year]).pack(fill=tk.X, pady=2)

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
    text_area = Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=5)
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_area.yview)

    def load_all_data(root):
        data_path = r"G:\expo\Software\NumberCruncher\data\csv"
        if not os.path.exists(data_path):
            text_area.insert(tk.END, f"Data path not found: {data_path}\n")
            return

        csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv') and 'All_Items_' in f]
        dfs = []
        for file in sorted(csv_files):
            file_path = os.path.join(data_path, file)
            year_match = re.search(r'(\d{4})', file)
            if year_match:
                year = int(year_match.group(1))
                single_df = load_csv(file_path)
                if single_df is not None:
                    single_df['Year'] = year
                    dfs.append(single_df)

        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            visualize_data(combined_df, text_area, canvas_frame)
            def plot_cmd():
                selected = [yr for yr, var in year_vars.items() if var.get()]
                plot_aggregation(combined_df, canvas_frame, bool(group_trade_var.get()), bool(group_tent_var.get()), bool(group_creative_var.get()), bool(group_av_var.get()), bool(group_tabletop_var.get()), bool(group_party_var.get()), bool(group_lav_var.get()), selected, bool(axis_var.get()), bool(include_trade_var.get()), bool(include_tent_var.get()), bool(include_creative_var.get()), bool(include_av_var.get()), bool(include_tabletop_var.get()), bool(include_party_var.get()), bool(include_lav_var.get()))
            plot_button.config(state=tk.NORMAL, command=plot_cmd)
            export_button.config(state=tk.NORMAL, command=lambda: export_csv(combined_df))

    def toggle_axis(root, axis_var, plot_button):
        axis_var.set(1 - axis_var.get())  # Toggle between 0 and 1
        axis_button.config(text="Switch to Year Axis" if axis_var.get() == 0 else "Switch to Category Axis")
        plot_button.invoke()  # Trigger plot update

    root.mainloop()


if __name__ == "__main__":
    create_ui()