import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell"""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell padding in dxa (1 pt = 20 dxa)"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = Document()

    # Page Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Palette
    COLOR_PRIMARY = RGBColor(79, 70, 229)     # Indigo #4F46E5
    COLOR_SECONDARY = RGBColor(124, 58, 237)  # Purple #7C3AED
    COLOR_DARK = RGBColor(30, 41, 59)         # Slate Dark #1E293B
    COLOR_MUTED = RGBColor(100, 116, 139)     # Slate Gray #64748B
    COLOR_SUCCESS = RGBColor(16, 185, 129)    # Emerald Green #10B981

    # Base Normal Style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = COLOR_DARK
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------
    # DOCUMENT TITLE / COVER HEADER
    # -------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    title_p.paragraph_format.space_before = Pt(10)
    title_run = title_p.add_run("VELAAN-AI: Agricultural Intelligence Platform")
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = COLOR_PRIMARY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(15)
    sub_run = sub_p.add_run("Comprehensive Technical & Academic Report: Machine Learning Intelligence Hub")
    sub_run.font.size = Pt(14)
    sub_run.font.bold = True
    sub_run.font.color.rgb = COLOR_SECONDARY

    # Metadata Banner Table
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    meta_data = [
        [("Course Modules Covered:", True), ("Module 1 (CO: 1), Module 2 (CO: 1), Module 3 (CO: 2), Module 4 (CO: 3), Module 5 (CO: 4)", False)],
        [("Algorithms Implemented:", True), ("Linear Regression, Ridge Regression, Decision Tree, Random Forest Ensemble, K-Means Clustering, PCA", False)]
    ]

    for r_idx, row in enumerate(meta_table.rows):
        for c_idx, cell in enumerate(row.cells):
            text, is_bold = meta_data[r_idx][c_idx]
            cell.text = text
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            p.runs[0].font.bold = is_bold
            p.runs[0].font.color.rgb = COLOR_DARK
            set_cell_background(cell, "F1F5F9" if is_bold else "F8FAFC")
            set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
            if c_idx == 0:
                cell.width = Inches(2.2)
            else:
                cell.width = Inches(4.3)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Helper function for Section Headings
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.size = Pt(12.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_callout(bold_prefix, text, fill_hex="EEF2FF", border_color="6366F1"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, fill_hex)
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        r_bold = p.add_run(bold_prefix + " ")
        r_bold.font.bold = True
        r_bold.font.size = Pt(10)
        r_bold.font.color.rgb = COLOR_DARK
        r_text = p.add_run(text)
        r_text.font.size = Pt(10)
        r_text.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # -------------------------------------------------------------
    # 1. EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # -------------------------------------------------------------
    add_h1("1. Executive Summary & Why Machine Learning is Needed")
    
    doc.add_paragraph(
        "Agriculture is the primary livelihood for more than 50% of the Indian workforce. However, farmers continually face high economic uncertainty due to unpredictable market price swings, fluctuating crop yields, and seasonal climatic variations. Traditional agricultural planning relies largely on historical guesswork or word-of-mouth recommendations, which frequently results in substantial financial losses or crop dumping during market gluts."
    )
    doc.add_paragraph(
        "The VELAAN-AI Machine Learning Intelligence Hub was engineered to transform raw, historical agro-economic records into predictive, real-time decision intelligence. By applying state-of-the-art Supervised Learning (Regression & Ensemble Trees) and Unsupervised Learning (Clustering & Dimensionality Reduction), the system provides accurate profit forecasts, cross-model benchmarking, zone risk assessments, and targeted crop recommendations."
    )

    add_callout("Key Problem Solved:", "Farmers and agricultural planners can simulate different crop choices, yield expectations, and market prices before sowing, receiving accurate profit estimates (R² = 99.01%) and risk indicators to maximize net farm revenue.")

    # -------------------------------------------------------------
    # 2. DATASET ARCHITECTURE & PREPROCESSING (MODULE 1)
    # -------------------------------------------------------------
    add_h1("2. Dataset Architecture & Preprocessing Pipeline (Module 1 - CO: 1)")

    doc.add_paragraph(
        "The underlying dataset (agriculture_data.csv) contains 3,000 empirical agricultural observations spanning 15 major Indian states, 8 primary crop varieties, and 3 distinct cropping seasons (Kharif, Rabi, and Zaid). Each observation incorporates both agronomic productivity and economic return attributes:"
    )

    data_desc_table = doc.add_table(rows=7, cols=3)
    data_desc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    data_desc_table.autofit = False

    data_desc_headers = ["Attribute Name", "Data Type", "Operational Description & Unit"]
    data_desc_rows = [
        ["crop", "Categorical", "Variety name (Rice, Wheat, Onion, Potato, Maize, Cucumber, Tomato, Chili)"],
        ["state", "Categorical", "Indian state / geographical agro-climatic region (15 unique states)"],
        ["season", "Categorical", "Agricultural season (Kharif - Monsoon, Rabi - Winter, Zaid - Summer)"],
        ["yield_t_per_ha", "Numerical (Float)", "Crop productivity expressed in metric tonnes per hectare (t/ha)"],
        ["price_per_qtl", "Numerical (Float)", "Market procurement price expressed in Rupees per quintal (Rs/qtl)"],
        ["ucpi_score", "Numerical (Float)", "Unit Crop Productivity Index (Quality and soil-health rating: 30 to 95)"]
    ]

    for c_idx, h_text in enumerate(data_desc_headers):
        cell = data_desc_table.rows[0].cells[c_idx]
        cell.text = h_text
        set_cell_background(cell, "3730A3")
        p = cell.paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(9.5)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)

    for r_idx, row_data in enumerate(data_desc_rows):
        for c_idx, val in enumerate(row_data):
            cell = data_desc_table.rows[r_idx + 1].cells[c_idx]
            cell.text = val
            set_cell_background(cell, "F8FAFC" if r_idx % 2 == 0 else "FFFFFF")
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(9)
            p.runs[0].font.color.rgb = COLOR_DARK
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)

    # Column widths
    for row in data_desc_table.rows:
        row.cells[0].width = Inches(1.5)
        row.cells[1].width = Inches(1.4)
        row.cells[2].width = Inches(3.6)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_h2("Preprocessing & Mathematical Transformation Pipeline")
    doc.add_paragraph("Because machine learning algorithms operate on numerical vectors rather than raw text, our backend pipeline executes the following preprocessing steps:")
    
    doc.add_paragraph("1. One-Hot Encoding (OHE) for Categorical Features: Categorical variables (crop, state, season) are converted into orthogonal binary indicator vectors. If a crop is 'Cucumber', its corresponding feature column receives a 1, while all other crop columns receive 0.")
    doc.add_paragraph("2. Z-Score Standardization for Continuous Numerical Features: Numerical columns (yield, price, UCPI) possess vastly different scales and variances (e.g. Yield: 1 to 50, Price: 500 to 5000). To prevent high-magnitude features from dominating gradient updates, features are normalized using Standard Scaling:")

    add_callout("StandardScaler Formula:", "z = (x - μ) / σ\nWhere x is the raw feature value, μ is the feature mean, and σ is the standard deviation across all training instances.")

    doc.add_paragraph("3. 80:20 Train-Test Validation Split: Conforming to Module 1 standards, the 3,000 records are partitioned randomly into 2,400 training rows (80%) and 600 testing rows (20%) using random_state=42 for deterministic reproducibility.")

    # -------------------------------------------------------------
    # 3. TAB 1: LIVE PROFIT PREDICTOR
    # -------------------------------------------------------------
    add_h1("3. Tab 1: Live Profit Predictor (Regression & Ensemble Learning)")

    doc.add_paragraph(
        "Tab 1 provides an interactive simulator where farmers or evaluators can test any operational scenario and immediately inspect profit forecasts across multiple model paradigms."
    )

    add_h2("A. Input Parameters")
    doc.add_paragraph("The user specifies six operational inputs:")
    doc.add_paragraph("• Crop Type: The agricultural crop selected for cultivation (e.g., Cucumber, Rice, Wheat, Tomato).")
    doc.add_paragraph("• State / Region: Geographical state (e.g., Tamil Nadu, Punjab, Odisha).")
    doc.add_paragraph("• Season: Cropping period (Kharif, Rabi, Zaid).")
    doc.add_paragraph("• Expected Yield (t/ha): Anticipated harvest volume in tonnes per hectare (e.g., 15.5 t/ha).")
    doc.add_paragraph("• Market Price (Rs/qtl): Expected mandi / market wholesale selling price in Rs per quintal (e.g., Rs 1,650/qtl).")
    doc.add_paragraph("• UCPI Quality Score: Overall quality and soil suitability index (e.g., 68 out of 100).")

    add_h2("B. The 4 Underlying Regression Algorithms & Formulas")

    doc.add_paragraph("When 'Run Ensemble Prediction' is triggered, the inputs are fed simultaneously to four algorithms:")

    doc.add_paragraph("1. Linear Regression (Module 3 - CO: 2):")
    doc.add_paragraph("Calculates expected profit as a linear combination of weighted features plus a bias intercept:")
    add_callout("Linear Regression Equation:", "ŷ_LR = w₀ + w₁(Yield) + w₂(Price) + w₃(UCPI) + ∑ w_c(Crop_c) + ∑ w_s(State_s) + ∑ w_z(Season_z)\nWhere weights w are learned via Ordinary Least Squares (OLS) minimizing the residual sum of squares: RSS = ∑(y_i - ŷ_i)².")

    doc.add_paragraph("2. Ridge Regression (Module 3 - CO: 2):")
    doc.add_paragraph("Addresses multicollinearity between features by imposing an L2 penalty on the magnitude of the model coefficients:")
    add_callout("Ridge Loss Function:", "L_Ridge = ∑(y_i - ŷ_i)² + α ∑ w_j²\nWhere α = 1.0 shrinks the coefficients, preventing overfitting and providing numerical stability.")

    doc.add_paragraph("3. Decision Tree Regressor (Module 3 - CO: 2):")
    doc.add_paragraph("Non-linear, non-parametric tree model that recursively splits feature space to minimize variance in each child partition:")
    add_callout("Decision Tree Splitting Criterion:", "MSE_split = (N_left / N) * MSE_left + (N_right / N) * MSE_right\nThe tree makes threshold decisions (e.g., 'Is Yield > 12.5?') down to terminal leaves that output the localized historical mean profit.")

    doc.add_paragraph("4. Random Forest Regressor (Module 4 - CO: 3 - Primary Predictor):")
    doc.add_paragraph("A bagging ensemble comprising 100 independent, decorrelated decision trees. Each individual tree is trained on a bootstrap sample of the training dataset with random feature subsampling. The final ensemble prediction is the arithmetic mean across all 100 trees:")
    add_callout("Random Forest Ensemble Formula:", "ŷ_RF = (1 / B) * ∑_{b=1}^{B} T_b(x)\nWhere B = 100 trees and T_b(x) is the prediction of the b-th tree. This ensemble averaging drastically suppresses the individual variance of single decision trees, achieving superior predictive power.")

    add_h2("C. Outputs Explained")
    doc.add_paragraph("1. Primary Predicted Profit: High-prominence display of the Random Forest forecast in Indian Rupees (e.g., Rs 1,19,566.98 per hectare).")
    doc.add_paragraph("2. 95% Confidence Interval: Upper and lower bounds (e.g., Rs 1,12,392 to Rs 1,26,741) reflecting statistical model uncertainty and historical price fluctuation margins.")
    doc.add_paragraph("3. Multi-Model Cross Comparison: Side-by-side cards comparing Random Forest (Rs 1,19,566), Decision Tree (Rs 1,30,548), Linear Regression (Rs 1,01,568), and Ridge Regression (Rs 1,00,171).")
    doc.add_paragraph("4. Key Feature Importance (Gini Impurity Reduction): Displays the percentage contribution of each feature category:")
    doc.add_paragraph("   • Crop Variety: 57.16% (The single largest determinant of profit)")
    doc.add_paragraph("   • Yield: 34.96% (Volume produced per hectare)")
    doc.add_paragraph("   • Market Price: 7.48% (Market rate per quintal)")
    doc.add_paragraph("   • Region & Season: ~0.40% (Geographical baseline adjustments)")

    add_callout("Real-World Example:", "Input: Crop = Cucumber, State = Tamil Nadu, Season = Kharif, Yield = 15.5 t/ha, Price = Rs 1,650/qtl, UCPI = 68.\nOutput: Predicted Profit = Rs 1,19,566.98 / hectare.\nInterpretation: Commercial vegetable crops in Tamil Nadu Kharif generate high return on investment because cucumber matures quickly with high yield volume.")

    # -------------------------------------------------------------
    # 4. TAB 2: MODEL BENCHMARKS & VALIDATION
    # -------------------------------------------------------------
    add_h1("4. Tab 2: Model Benchmarks & Validation Matrix (Module 1, 3, 4)")

    doc.add_paragraph(
        "Tab 2 provides academic rigor and proves that models were systematically tested and evaluated against standard quantitative metrics on unseen test data (600 rows)."
    )

    add_h2("A. Evaluation Metrics Defined")
    doc.add_paragraph("1. R² Score (Coefficient of Determination): Measures the proportion of total variance in profit explained by the model:")
    add_callout("R² Score Formula:", "R² = 1 - [ ∑(y_i - ŷ_i)² / ∑(y_i - ȳ)² ]\nWhere ȳ is the mean of true profit values. An R² close to 1.0 indicates near-perfect explanatory accuracy.")

    doc.add_paragraph("2. Mean Absolute Error (MAE): Measures the average magnitude of absolute errors in Rupees:")
    add_callout("MAE Formula:", "MAE = (1 / n) * ∑ |y_i - ŷ_i|")

    doc.add_paragraph("3. Root Mean Squared Error (RMSE): Penalizes large outlier errors more heavily by squaring residuals before taking the root:")
    add_callout("RMSE Formula:", "RMSE = √ [ (1 / n) * ∑(y_i - ŷ_i)² ]")

    add_h2("B. Empirical Benchmark Scorecard")

    bench_table = doc.add_table(rows=5, cols=7)
    bench_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    bench_table.autofit = False

    bench_headers = ["Algorithm Name", "Module Tag", "Methodology Classification", "R² Score", "Accuracy %", "MAE (Rs/ha)", "RMSE (Rs/ha)"]
    bench_rows = [
        ["Random Forest (Ensemble)", "Module 4 (CO: 3)", "Bagging (100 Trees Ensemble)", "0.9901", "99.01%", "Rs 7,700.70", "Rs 13,200.44"],
        ["Decision Tree Regressor", "Module 3 (CO: 2)", "Non-linear Recursive Partitioning", "0.9815", "98.15%", "Rs 11,380.46", "Rs 18,041.97"],
        ["Linear Regression", "Module 3 (CO: 2)", "Parametric Ordinary Least Squares", "0.9462", "94.62%", "Rs 20,894.58", "Rs 30,751.61"],
        ["Ridge Regression (L2)", "Module 3 (CO: 2)", "Regularized Parametric Linear", "0.9460", "94.60%", "Rs 20,876.22", "Rs 30,812.46"]
    ]

    for c_idx, h_text in enumerate(bench_headers):
        cell = bench_table.rows[0].cells[c_idx]
        cell.text = h_text
        set_cell_background(cell, "1E293B")
        p = cell.paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(8.5)
        set_cell_margins(cell, top=100, bottom=100, left=80, right=80)

    for r_idx, row_data in enumerate(bench_rows):
        is_rf = (r_idx == 0)
        for c_idx, val in enumerate(row_data):
            cell = bench_table.rows[r_idx + 1].cells[c_idx]
            cell.text = val
            set_cell_background(cell, "DCFCE7" if is_rf else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF"))
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(8.5)
            p.runs[0].font.bold = is_rf and (c_idx in [0, 3, 4])
            p.runs[0].font.color.rgb = RGBColor(22, 101, 52) if (is_rf and c_idx in [0, 3, 4]) else COLOR_DARK
            set_cell_margins(cell, top=80, bottom=80, left=80, right=80)

    # Column widths
    widths = [Inches(1.5), Inches(0.9), Inches(1.5), Inches(0.6), Inches(0.6), Inches(0.7), Inches(0.7)]
    for row in bench_table.rows:
        for idx, w in enumerate(widths):
            row.cells[idx].width = w

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_h2("C. Academic Viva Rationale: Why Random Forest Outperformed Others")
    doc.add_paragraph(
        "A critical question evaluators ask is why Random Forest achieves an R² of 99.01% while Linear Regression achieves 94.62% and a single Decision Tree achieves 98.15%."
    )
    doc.add_paragraph(
        "1. Inadequacy of Pure Linear Hypotheses: Crop profit = (Yield * Price) - Input Cost. The interaction between Yield and Price is multiplicative (non-linear). Linear models approximate this relationship linearly, capping their R² at ~94.6%."
    )
    doc.add_paragraph(
        "2. High Variance in Single Trees: A solitary Decision Tree captures non-linear splits well (98.15%), but is vulnerable to high variance—it overfits to local training anomalies."
    )
    doc.add_paragraph(
        "3. Variance Reduction via Bagging: Random Forest creates 100 decorrelated trees via bootstrapping and random feature selection at each split. Because tree errors are largely uncorrelated, averaging them reduces estimator variance without increasing bias: Var(Ensemble) = (1/B)*Var(Tree) + Covariances ≈ drastically lower error. This boosts R² to 99.01% and slashes MAE down to Rs 7,700."
    )

    # -------------------------------------------------------------
    # 5. TAB 3: AGRO-ECONOMIC CLUSTERING & PCA
    # -------------------------------------------------------------
    add_h1("5. Tab 3: Agro-Economic Clustering & 2D PCA Dimensionality Reduction (Module 2 & Module 5)")

    doc.add_paragraph(
        "While Supervised Learning predicts known profit labels, Tab 3 addresses Unsupervised Learning (CO: 4) and Dimensionality Reduction (CO: 1). It discovers hidden patterns across states and crop types without prior labeling."
    )

    add_h2("A. K-Means Clustering Formulation (Module 5 - CO: 4)")
    doc.add_paragraph("K-Means groups all 3,000 agricultural records into K = 3 homogeneous agro-economic clusters based on four normalized feature dimensions: Yield, Market Price, Net Profit, and UCPI Score.")
    add_callout("K-Means Objective Function:", "J = ∑_{k=1}^{K} ∑_{x_i ∈ C_k} || x_i - μ_k ||²\nWhere μ_k represents the centroid of cluster C_k. The algorithm iteratively assigns points to the nearest centroid and recomputes centroids until convergence.")

    doc.add_paragraph("The 3 Discovered Agro-Economic Clusters:")
    doc.add_paragraph("• Cluster 0 - Prime Agro-Zone (Green): High Yield (41.6 t/ha) & Maximum Profitability (Avg Profit: Rs 4,15,668/ha). Dominated by commercial cash crops like Cucumber and Tomato.")
    doc.add_paragraph("• Cluster 1 - Commercial Scale Zone (Blue): Moderate Yield (25.1 t/ha) & Steady Return (Avg Profit: Rs 1,50,577/ha). Dominated by staple commercial crops like Onion and Potato.")
    doc.add_paragraph("• Cluster 2 - Staple & Market Sensitive Zone (Red): Low Yield (3.7 t/ha) & Lower Margin with High Price Volatility (Avg Profit: Rs 42,508/ha). Dominated by field grains and spices like Wheat, Rice, and Chili.")

    add_h2("B. Principal Component Analysis (PCA) Dimensionality Reduction (Module 2 - CO: 1)")
    doc.add_paragraph(
        "Because our feature space consists of 4 numerical dimensions, visualizing the clusters directly is impossible for humans. To project the multi-dimensional clusters onto an interactive 2D graph, we apply Principal Component Analysis (PCA):"
    )
    doc.add_paragraph("1. Computes the 4x4 covariance matrix of normalized features: Σ = (1 / n) * X^T X.")
    doc.add_paragraph("2. Calculates the Eigenvalues (λ) and Eigenvectors (v): Σ v = λ v.")
    doc.add_paragraph("3. Projects data points onto the top two orthogonal eigenvectors with the highest eigenvalues, creating Principal Components PC1 and PC2.")

    add_callout("PCA Variance Retained:", "PC1 (Yield & Profit Dimension) captures 71.79% of total variance.\nPC2 (Price & Volatility Dimension) captures 19.26% of total variance.\nTotal Explained Variance = 71.79% + 19.26% = 91.05% Information Retained!\nThis mathematically validates that 2D visualization accurately reflects the true 4D cluster geometry without significant information loss.")

    # -------------------------------------------------------------
    # 6. TAB 4: SMART CROP RECOMMENDER
    # -------------------------------------------------------------
    add_h1("6. Tab 4: Smart Crop Recommender (Classification - Module 3 & 4)")

    doc.add_paragraph(
        "Tab 4 formulates crop selection as a Multi-Class Supervised Classification problem. When farmers know their location and season but are uncertain which crop guarantees the highest success probability, this module acts as a recommendation engine."
    )

    add_h2("A. Inputs and Classifier Operation")
    doc.add_paragraph("• Inputs: Geographical State (e.g. Punjab), Agricultural Season (e.g. Rabi), Target Yield Expectation (e.g. 20 t/ha), Expected Market Price (e.g. Rs 2,100/qtl).")
    doc.add_paragraph("• Underlying Model: Random Forest Multi-Class Classifier trained with 60 decision trees.")
    doc.add_paragraph("• Probability Calculation: For any input vector x, the classifier evaluates class distributions across all tree leaf nodes:")
    add_callout("Classification Probability Formula:", "P(Crop = c | x) = (1 / B) * ∑_{b=1}^{B} P_b(Crop = c | x)\nThe crops are then ranked in descending order of their confidence probability.")

    add_h2("B. Outputs & Practical Example")
    doc.add_paragraph("Output Display: Generates ranked cards displaying the Top 3 Recommended Crop Varieties with confidence badges (e.g. #1 Tomato - 29.4% Match, #2 Onion - 21.1% Match, #3 Maize - 20.4% Match).")
    doc.add_paragraph("This enables farmers to diversify crops and select varieties that match both soil climate conditions and their profit targets.")

    # -------------------------------------------------------------
    # 7. VIVA CHEAT SHEET FOR MA'AM
    # -------------------------------------------------------------
    add_h1("7. Quick Viva Presentation Cheat Sheet")

    viva_table = doc.add_table(rows=6, cols=2)
    viva_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    viva_table.autofit = False

    viva_qas = [
        ("What is the primary objective of this ML Hub?", "To replace agricultural guesswork with data-driven predictive models, calculating profit with 99.01% accuracy, identifying economic risk clusters, and recommending the best crops to plant."),
        ("Why did Random Forest beat Linear Regression?", "Linear Regression assumes linear relationships and achieved 94.62% R². But crop profit is non-linear (Yield * Price - Costs). Random Forest combines 100 decorrelated trees via Bagging, reducing variance and raising R² to 99.01%."),
        ("How did you validate your models (Module 1)?", "Using an 80:20 Train-Test split on 3,000 empirical records. Performance was validated on unseen test data using R² Score, Mean Absolute Error (MAE = Rs 7,700), and RMSE."),
        ("Where is Unsupervised Learning applied (Module 5)?", "K-Means Clustering (K=3) groups agricultural data into 3 economic zones: Prime Agro-Zone (Rs 4.15L profit), Commercial Zone (Rs 1.50L profit), and Risk/Staple Zone (Rs 42K profit)."),
        ("Why was PCA needed (Module 2)?", "Our data has 4 dimensions (Yield, Price, Profit, UCPI), which cannot be drawn on a screen. PCA reduced 4D to 2D (PC1 and PC2) while preserving 91% of total variance, enabling clear 2D scatter plotting.")
    ]

    for c_idx, h_text in enumerate(["Evaluator / Ma'am Question", "Model Response to Give"]):
        cell = viva_table.rows[0].cells[c_idx]
        cell.text = h_text
        set_cell_background(cell, "4F46E5")
        p = cell.paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(9.5)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)

    for r_idx, (q, a) in enumerate(viva_qas):
        cell_q = viva_table.rows[r_idx + 1].cells[0]
        cell_a = viva_table.rows[r_idx + 1].cells[1]
        
        cell_q.text = q
        cell_a.text = a

        set_cell_background(cell_q, "F1F5F9")
        set_cell_background(cell_a, "FFFFFF")

        pq = cell_q.paragraphs[0]
        pq.runs[0].font.bold = True
        pq.runs[0].font.size = Pt(9)
        pq.runs[0].font.color.rgb = COLOR_DARK

        pa = cell_a.paragraphs[0]
        pa.runs[0].font.size = Pt(9)
        pa.runs[0].font.color.rgb = COLOR_DARK

        set_cell_margins(cell_q, top=90, bottom=90, left=120, right=120)
        set_cell_margins(cell_a, top=90, bottom=90, left=120, right=120)

    for row in viva_table.rows:
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(4.3)

    output_path = r"c:\Users\admin\Downloads\AI\VELAAN_AI_Machine_Learning_Report.docx"
    doc.save(output_path)
    print(f"Report successfully generated at: {output_path}")

if __name__ == '__main__':
    create_report()
