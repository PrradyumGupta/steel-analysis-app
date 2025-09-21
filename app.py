import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'

# Home Page
@app.route('/')
def index():
    return render_template('upload.html')

# Handle CSV Upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file uploaded"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    # Save file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Read CSV
    df = pd.read_csv(filepath, parse_dates=['Date'])

    # Efficiency calculation
    df["TotalInput"] = df["Coal"] + df["Limestone"] + df["IronOre"]
    df["TotalWaste"] = df["SlagWaste"] + df["CoalWaste"] + df["OreWaste"]
    df["Efficiency(%)"] = (df["FinalSteel"] / (df["TotalInput"] - df["TotalWaste"])) * 100

    # === Monthly summary ===
    numeric_cols = [
        "Coal", "Limestone", "IronOre",
        "SlagWaste", "CoalWaste", "OreWaste",
        "FinalSteel", "Efficiency(%)"
    ]

    monthly_summary = (
        df.groupby(df['Date'].dt.to_period("M"))[numeric_cols]
          .agg({
              "Coal": "sum",
              "Limestone": "sum",
              "IronOre": "sum",
              "SlagWaste": "sum",
              "CoalWaste": "sum",
              "OreWaste": "sum",
              "FinalSteel": "sum",
              "Efficiency(%)": "mean"
          })
          .reset_index()
    )
    monthly_summary['Date'] = monthly_summary['Date'].astype(str)

    # === Overall Total and Average ===
    totals = monthly_summary.drop(columns=["Date"]).sum(numeric_only=True)
    totals_df = pd.DataFrame([totals])
    totals_df.insert(0, "Date", "Overall Total")

    averages = monthly_summary.drop(columns=["Date"]).mean(numeric_only=True)
    avg_df = pd.DataFrame([averages])
    avg_df.insert(0, "Date", "Overall Average")

    # Keep monthly and overall separately
    monthly_table = monthly_summary.copy()
    overall_table = pd.concat([totals_df, avg_df], ignore_index=True)

    # === Add Units ===
    for col in ["Coal", "Limestone", "IronOre", "SlagWaste", "CoalWaste", "OreWaste", "FinalSteel"]:
        monthly_table[col] = monthly_table[col].astype(float).round(2).astype(str) + " tons"
        overall_table[col] = overall_table[col].astype(float).round(2).astype(str) + " tons"

    monthly_table["Efficiency(%)"] = monthly_table["Efficiency(%)"].astype(float).round(2).astype(str) + " %"
    overall_table["Efficiency(%)"] = overall_table["Efficiency(%)"].astype(float).round(2).astype(str) + " %"

    # === Generate Charts ===
    charts = {}

    # Raw materials trend
    plt.figure(figsize=(8,5))
    plt.plot(monthly_summary['Date'], df.groupby(df['Date'].dt.to_period("M"))["Coal"].sum(), label="Coal")
    plt.plot(monthly_summary['Date'], df.groupby(df['Date'].dt.to_period("M"))["Limestone"].sum(), label="Limestone")
    plt.plot(monthly_summary['Date'], df.groupby(df['Date'].dt.to_period("M"))["IronOre"].sum(), label="Iron Ore")
    plt.xticks(rotation=45)
    plt.ylabel("Tons")
    plt.title("Monthly Raw Material Consumption")
    plt.legend()
    raw_chart = os.path.join(app.config['STATIC_FOLDER'], 'raw_materials.png')
    plt.savefig(raw_chart, bbox_inches="tight")
    charts['raw_materials'] = 'raw_materials.png'
    plt.close()

    # Waste analysis
    waste_grouped = df.groupby(df['Date'].dt.to_period("M"))[["SlagWaste","CoalWaste","OreWaste"]].sum().reset_index()
    waste_grouped["Date"] = waste_grouped["Date"].astype(str)

    plt.figure(figsize=(8,5))
    plt.bar(waste_grouped['Date'], waste_grouped['SlagWaste'], label="Slag Waste")
    plt.bar(waste_grouped['Date'], waste_grouped['CoalWaste'], bottom=waste_grouped['SlagWaste'], label="Coal Waste")
    plt.bar(waste_grouped['Date'], waste_grouped['OreWaste'], bottom=waste_grouped['SlagWaste']+waste_grouped['CoalWaste'], label="Ore Waste")
    plt.xticks(rotation=45)
    plt.ylabel("Tons")
    plt.title("Monthly Waste Generated")
    plt.legend()
    waste_chart = os.path.join(app.config['STATIC_FOLDER'], 'waste.png')
    plt.savefig(waste_chart, bbox_inches="tight")
    charts['waste'] = 'waste.png'
    plt.close()

    # Final steel production
    steel_grouped = df.groupby(df['Date'].dt.to_period("M"))["FinalSteel"].sum().reset_index()
    steel_grouped["Date"] = steel_grouped["Date"].astype(str)

    plt.figure(figsize=(8,5))
    plt.plot(steel_grouped['Date'], steel_grouped['FinalSteel'], marker='o', color='green')
    plt.xticks(rotation=45)
    plt.ylabel("Tons")
    plt.title("Monthly Final Steel Production")
    steel_chart = os.path.join(app.config['STATIC_FOLDER'], 'steel.png')
    plt.savefig(steel_chart, bbox_inches="tight")
    charts['steel'] = 'steel.png'
    plt.close()

    # Efficiency
    eff_grouped = df.groupby(df['Date'].dt.to_period("M"))["Efficiency(%)"].mean().reset_index()
    eff_grouped["Date"] = eff_grouped["Date"].astype(str)

    plt.figure(figsize=(8,5))
    plt.plot(eff_grouped['Date'], eff_grouped['Efficiency(%)'], marker='s', color='red')
    plt.xticks(rotation=45)
    plt.ylabel("Efficiency %")
    plt.title("Monthly Efficiency (%)")
    eff_chart = os.path.join(app.config['STATIC_FOLDER'], 'efficiency.png')
    plt.savefig(eff_chart, bbox_inches="tight")
    charts['efficiency'] = 'efficiency.png'
    plt.close()

    # Show results
    return render_template(
        "result.html", 
        monthly_table=[monthly_table.to_html(classes='data', index=False, escape=False)],
        overall_table=[overall_table.to_html(classes='data overall-table', index=False, escape=False)],
        charts=charts
    )

if __name__ == "__main__":
    app.run(debug=True)
