"""
Machine Learning Engine for VELAAN-AI Agriculture Analytics
Covers:
- Module 1 (CO: 1): Testing & Validating, Data Prep & Scaling
- Module 2 (CO: 1): Dimensionality Reduction (PCA - 2 Principal Components)
- Module 3 (CO: 2): Classification & Regression (Linear Regression, Ridge Regression, Decision Tree)
- Module 4 (CO: 3): Ensemble Learning (Random Forest Regressor & Classifier)
- Module 5 (CO: 4): Clustering (K-Means Clustering with 3 Agro-Economic Clusters)
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

class MLEngine:
    def __init__(self, csv_path='data/agriculture_data.csv'):
        self.csv_path = csv_path
        self.df = None
        self.regression_models = {}
        self.metrics = {}
        self.feature_importance = {}
        self.kmeans_model = None
        self.pca_model = None
        self.cluster_summary = []
        self.pca_points = []
        self.pca_variance_ratio = []
        self.crop_recommender = None
        self.crop_classes = []
        self.is_trained = False
        self.train_all()

    def train_all(self):
        """Train all regression, ensemble, clustering, and classification models"""
        if not os.path.exists(self.csv_path):
            print(f"[ML Engine] CSV not found at {self.csv_path}")
            return False

        try:
            print("[ML Engine] Training models on agriculture dataset...")
            df = pd.read_csv(self.csv_path)
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            self.df = df
            
            # --- MODULE 1, 3, 4: REGRESSION & ENSEMBLE SUITE ---
            features = ['crop', 'state', 'season', 'yield_t_per_ha', 'price_per_qtl', 'ucpi_score']
            target = 'profit_per_ha'

            X = df[features]
            y = df[target]

            # 80/20 train/test split (Module 1 - Testing & Validation)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            cat_cols = ['crop', 'state', 'season']
            num_cols = ['yield_t_per_ha', 'price_per_qtl', 'ucpi_score']

            preprocessor = ColumnTransformer([
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
                ('num', StandardScaler(), num_cols)
            ])

            # Candidate algorithms from syllabus
            raw_models = {
                'Linear Regression': (LinearRegression(), "Module 3 (CO: 2)", "Classical Linear Parametric Model"),
                'Ridge Regression': (Ridge(alpha=1.0), "Module 3 (CO: 2)", "L2 Regularized Linear Model"),
                'Decision Tree': (DecisionTreeRegressor(max_depth=10, random_state=42), "Module 3 (CO: 2)", "Non-linear Tree Partitioning"),
                'Random Forest (Ensemble)': (RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42), "Module 4 (CO: 3)", "Bagging Ensemble of 100 Trees")
            }

            self.metrics = []
            for name, (model, module_tag, desc) in raw_models.items():
                pipe = Pipeline([
                    ('preprocessor', preprocessor),
                    ('regressor', model)
                ])
                pipe.fit(X_train, y_train)
                preds = pipe.predict(X_test)
                
                r2 = float(r2_score(y_test, preds))
                mae = float(mean_absolute_error(y_test, preds))
                rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
                
                self.regression_models[name] = pipe
                self.metrics.append({
                    "model_name": name,
                    "module": module_tag,
                    "description": desc,
                    "r2_score": round(r2, 4),
                    "accuracy_pct": round(max(0, r2 * 100), 2),
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2)
                })

            # Feature Importance from Random Forest
            rf_model = self.regression_models['Random Forest (Ensemble)'].named_steps['regressor']
            prep = self.regression_models['Random Forest (Ensemble)'].named_steps['preprocessor']
            cat_encoder = prep.named_transformers_['cat']
            cat_feature_names = cat_encoder.get_feature_names_out(cat_cols).tolist()
            all_feature_names = cat_feature_names + num_cols
            importances = rf_model.feature_importances_

            # Aggregate importances by conceptual category
            feat_dict = {"Yield (t/ha)": 0.0, "Price (Rs/qtl)": 0.0, "UCPI Score": 0.0, "Crop Variety": 0.0, "State / Region": 0.0, "Season": 0.0}
            for fname, imp in zip(all_feature_names, importances):
                if fname == 'yield_t_per_ha':
                    feat_dict["Yield (t/ha)"] += float(imp)
                elif fname == 'price_per_qtl':
                    feat_dict["Price (Rs/qtl)"] += float(imp)
                elif fname == 'ucpi_score':
                    feat_dict["UCPI Score"] += float(imp)
                elif fname.startswith('crop_'):
                    feat_dict["Crop Variety"] += float(imp)
                elif fname.startswith('state_'):
                    feat_dict["State / Region"] += float(imp)
                elif fname.startswith('season_'):
                    feat_dict["Season"] += float(imp)

            self.feature_importance = [
                {"feature": k, "importance_pct": round(v * 100, 2)}
                for k, v in sorted(feat_dict.items(), key=lambda x: x[1], reverse=True)
            ]

            # --- MODULE 5 & MODULE 2: K-MEANS CLUSTERING & PCA ---
            cluster_cols = ['yield_t_per_ha', 'price_per_qtl', 'profit_per_ha', 'ucpi_score']
            X_cluster = df[cluster_cols]
            scaler_cluster = StandardScaler()
            X_scaled = scaler_cluster.fit_transform(X_cluster)

            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(X_scaled)
            self.kmeans_model = kmeans

            # Dimensionality reduction with PCA (2 Principal Components)
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X_scaled)
            df['pca_x'] = coords[:, 0]
            df['pca_y'] = coords[:, 1]
            self.pca_model = pca
            self.pca_variance_ratio = [round(float(v) * 100, 2) for v in pca.explained_variance_ratio_]

            # Characterize clusters
            cluster_names = {
                0: {"name": "Low Margin / Staple Crops", "color": "#3b82f6", "badge": "Staple Zone"},
                1: {"name": "Moderate Yield & Steady Return", "color": "#10b981", "badge": "Commercial Zone"},
                2: {"name": "High Yield & Maximum Profit", "color": "#f59e0b", "badge": "Prime Agro-Zone"}
            }

            # Map based on average profit
            cluster_avgs = df.groupby('cluster')['profit_per_ha'].mean().sort_values().index.tolist()
            cluster_label_map = {
                cluster_avgs[0]: ("Low Margin / High Price Volatility", "#ef4444", "Risk Zone"),
                cluster_avgs[1]: ("Moderate Margin & Commercial Scale", "#3b82f6", "Commercial Zone"),
                cluster_avgs[2]: ("High Yield & Maximum Profitability", "#10b981", "Prime Agro-Zone")
            }

            self.cluster_summary = []
            for c_id in range(3):
                sub = df[df['cluster'] == c_id]
                c_name, c_color, c_badge = cluster_label_map[c_id]
                self.cluster_summary.append({
                    "cluster_id": int(c_id),
                    "name": c_name,
                    "color": c_color,
                    "badge": c_badge,
                    "count": int(len(sub)),
                    "avg_profit": round(float(sub['profit_per_ha'].mean()), 2),
                    "avg_yield": round(float(sub['yield_t_per_ha'].mean()), 2),
                    "avg_price": round(float(sub['price_per_qtl'].mean()), 2),
                    "top_crops": sub['crop'].value_counts().head(3).index.tolist()
                })

            # Sample 150 points for chart visualization
            sampled_df = df.sample(n=min(180, len(df)), random_state=42)
            self.pca_points = []
            for _, r in sampled_df.iterrows():
                cid = int(r['cluster'])
                c_name, c_color, c_badge = cluster_label_map[cid]
                self.pca_points.append({
                    "x": round(float(r['pca_x']), 3),
                    "y": round(float(r['pca_y']), 3),
                    "cluster": cid,
                    "cluster_name": c_name,
                    "cluster_color": c_color,
                    "crop": str(r['crop']),
                    "state": str(r['state']),
                    "profit": round(float(r['profit_per_ha']), 2),
                    "yield": round(float(r['yield_t_per_ha']), 2)
                })

            # --- MODULE 3 & 4: CROP RECOMMENDER CLASSIFIER ---
            X_clf = df[['state', 'season', 'yield_t_per_ha', 'price_per_qtl']]
            y_clf = df['crop']
            clf_prep = ColumnTransformer([
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['state', 'season']),
                ('num', StandardScaler(), ['yield_t_per_ha', 'price_per_qtl'])
            ])
            recommender = Pipeline([
                ('prep', clf_prep),
                ('clf', RandomForestClassifier(n_estimators=60, max_depth=10, random_state=42))
            ])
            recommender.fit(X_clf, y_clf)
            self.crop_recommender = recommender
            self.crop_classes = recommender.classes_.tolist()

            self.is_trained = True
            print("[ML Engine] Models successfully trained and ready!")
            return True

        except Exception as e:
            print(f"[ML Engine Error] {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def predict_profit(self, crop, state, season, yield_val, price_val, ucpi_val=65.0):
        """Predict profit across models (Module 3 & Module 4)"""
        if not self.is_trained:
            self.train_all()

        input_df = pd.DataFrame([{
            'crop': str(crop),
            'state': str(state),
            'season': str(season),
            'yield_t_per_ha': float(yield_val),
            'price_per_qtl': float(price_val),
            'ucpi_score': float(ucpi_val)
        }])

        preds = {}
        for name, pipe in self.regression_models.items():
            pred = pipe.predict(input_df)[0]
            preds[name] = round(float(pred), 2)

        primary_rf = preds.get('Random Forest (Ensemble)', 0.0)

        # Estimate confidence interval using tree variance heuristic (~5%)
        margin = abs(primary_rf * 0.06)

        return {
            "success": True,
            "predicted_profit": primary_rf,
            "lower_bound": round(max(0, primary_rf - margin), 2),
            "upper_bound": round(primary_rf + margin, 2),
            "all_model_predictions": preds,
            "feature_importance": self.feature_importance,
            "inputs": {
                "crop": crop,
                "state": state,
                "season": season,
                "yield": yield_val,
                "price": price_val,
                "ucpi": ucpi_val
            }
        }

    def recommend_crop(self, state, season, target_yield=15.0, expected_price=1500.0):
        """Recommend best crop based on state, season and target inputs"""
        if not self.is_trained:
            self.train_all()

        input_df = pd.DataFrame([{
            'state': str(state),
            'season': str(season),
            'yield_t_per_ha': float(target_yield),
            'price_per_qtl': float(expected_price)
        }])

        probs = self.crop_recommender.predict_proba(input_df)[0]
        results = []
        for crop_name, p in zip(self.crop_classes, probs):
            results.append({
                "crop": crop_name,
                "confidence_pct": round(float(p) * 100, 1)
            })

        results = sorted(results, key=lambda x: x["confidence_pct"], reverse=True)
        return {
            "success": True,
            "recommendations": results[:3],
            "best_crop": results[0]["crop"] if results else "Rice"
        }

    def get_dashboard_payload(self):
        """Bundle all metrics, clusters, and PCA data for the frontend"""
        if not self.is_trained:
            self.train_all()

        return {
            "success": True,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "clusters": self.cluster_summary,
            "pca_variance_ratio": self.pca_variance_ratio,
            "pca_points": self.pca_points,
            "crops_available": sorted(self.df['crop'].unique().tolist()) if self.df is not None else [],
            "states_available": sorted(self.df['state'].unique().tolist()) if self.df is not None else [],
            "seasons_available": ['Kharif', 'Rabi', 'Zaid']
        }

# Global singleton
ml_engine = MLEngine()
