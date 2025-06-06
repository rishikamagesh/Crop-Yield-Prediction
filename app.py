import os
import pandas as pd
import pickle
from flask import Flask, request, jsonify, send_file, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)
DATABASE_URL = 'mysql+pymysql://root:Elsarishi%4026@localhost:3306/project'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PredictionsCrop(db.Model):
    __tablename__ = "predictions_crop"
    id = db.Column(db.Integer, primary_key=True)
    Year = db.Column(db.Integer, nullable=False)
    Area = db.Column(db.String(100), nullable=False)
    Item = db.Column(db.String(100), nullable=False)
    pesticides_tonnes = db.Column(db.Float, nullable=False)
    avg_temp = db.Column(db.Float, nullable=False)
    average_rain_fall_mm_per_year = db.Column(db.Float, nullable=False)
    prediction = db.Column(db.Float, nullable=False)
try:
    dtr = pickle.load(open("dtr_model.pkl", "rb"))
    preprocessor = pickle.load(open("preprocesser.pkl", "rb"))
except FileNotFoundError:
    print("Error: Model files not found.")
    exit()

try:
    data = pd.read_csv("yield_df.csv")
except FileNotFoundError:
    print("Error: Dataset 'yield_df.csv' not found.")
    exit()

def create_yield_recommendations(data):
    """Create crop yield recommendations based on average yields."""
    yield_data = data.groupby(['Area', 'Item'])['hg/ha_yield'].mean().reset_index()
    recommendations = {}

    for area in yield_data['Area'].unique():
        crops_in_area = yield_data[yield_data['Area'] == area]
        if not crops_in_area.empty:
            best_crop = crops_in_area.loc[crops_in_area['hg/ha_yield'].idxmax()]
            recommendations[area.lower()] = {
                'best_crop': (best_crop['Item'], best_crop['hg/ha_yield']),
            }

    return recommendations

def get_default_recommendations(crop):
    """Get default recommendations for fertilizers and pesticides based on the crop."""
    recommendations = {
        "maize": {
            "pesticides": "Insecticides such as Pyrethroids can be effective.",
            "fertilizers": "Use Nitrogen-Phosphorus-Potassium (NPK) fertilizers.",
        },
        "potatoes": {
            "pesticides": "Use insecticides like Imidacloprid for pest control.",
            "fertilizers": "Apply potassium and phosphorus-rich fertilizers.",
        },
        "rice, paddy": {
            "pesticides": "Use Carbofuran for pest control.",
            "fertilizers": "Urea is suitable for nitrogen.",
        },
        "sorghum": {
            "pesticides": "Apply systemic insecticides for shoot fly control.",
            "fertilizers": "Use nitrogen-rich fertilizers for better growth.",
        },
        "soybeans": {
            "pesticides": "Consider using fungicides for disease control.",
            "fertilizers": "Fertilizers rich in phosphorus and potassium.",
        },
        "wheat": {
            "pesticides": "Use herbicides for weed control.",
            "fertilizers": "Apply nitrogen-based fertilizers for better yield.",
        },
        "cassava": {
            "pesticides": "Apply insecticides for whitefly control.",
            "fertilizers": "Use potassium-rich fertilizers for tuber development.",
        },
        "sweet potatoes": {
            "pesticides": "Use nematicides for nematode control.",
            "fertilizers": "Apply phosphorus-based fertilizers for root growth.",
        },
        "plantains and others": {
            "pesticides": "Use fungicides for leaf spot control.",
            "fertilizers": "Apply potassium and nitrogen-rich fertilizers.",
        },
        "yams": {
            "pesticides": "Consider using Carbofuran for pest control.",
            "fertilizers": "A base of organic matter and phosphorus.",
        },
    }
    return recommendations.get(crop.lower(), {})

def get_specific_agricultural_tips(crop):
    """Return specific agricultural tips for the given crop."""
    crop_tips = {
        "maize": [
            "Ensure that the soil is well-drained and rich in organic matter.",
            "Regularly check for pest infestations and diseases.",
            "Consider intercropping with legumes to enhance soil nitrogen."
        ],
        "potatoes": [
            "Ensure soil is loose and well-drained.",
            "Control fungal infections with proper fungicides.",
            "Rotate crops to avoid soil-borne diseases."
        ],
        "rice, paddy": [
            "Maintain a consistent water level in the fields during growth.",
            "Use fertilizers rich in nitrogen for better yield.",
            "Monitor for pests like rice stem borers and use appropriate pest control."
        ],
        "sorghum": [
            "Plant in well-drained soils.",
            "Use drought-resistant varieties in dry regions.",
            "Monitor for pests like aphids and apply insecticides as needed."
        ],
        "soybeans": [
            "Ensure good drainage and avoid waterlogging.",
            "Inoculate seeds with rhizobium for effective nitrogen fixation.",
            "Rotate with cereals to break disease cycles."
        ],
        "wheat": [
            "Ensure proper spacing to reduce fungal infections.",
            "Use balanced fertilizers for better yield.",
            "Monitor for rust and apply fungicides."
        ],
        "cassava": [
            "Use disease-free planting materials.",
            "Control whiteflies to prevent virus transmission.",
            "Practice crop rotation to maintain soil fertility."
        ],
        "sweet potatoes": [
            "Ensure well-drained sandy soil.",
            "Monitor for sweet potato weevils.",
            "Apply organic compost for better root development."
        ],
        "plantains and others": [
            "Ensure proper spacing to avoid fungal diseases.",
            "Use mulch to retain soil moisture.",
            "Apply potassium-based fertilizers."
        ],
        "yams": [
            "Ensure adequate soil moisture for healthy tuber formation.",
            "Practice crop rotation to prevent soil nutrient depletion.",
            "Use organic matter to enhance soil fertility."
        ],
    }
    return crop_tips.get(crop.lower(), ["No specific tips available for this crop."])

def get_info(area):
    """Fetch average temperature based on area."""
    area = area.lower()
    temp_data = data[data['Area'].str.lower() == area]['avg_temp']

    if not temp_data.empty:
        avg_temp = temp_data.mean()
        return avg_temp  # return average temperature value

    return None  # if no data found

@app.route("/", methods=["GET", "POST"])
def home():
    years = data["Year"].unique().tolist()
    countries = data["Area"].unique().tolist()
    crops = data["Item"].unique().tolist()

    if request.method == "POST":
        try:
            Year = int(request.form["year"])
            Area = request.form["area"]
            Item = request.form["item"]
            pesticides_tonnes = float(request.form["pesticides_tonnes"])
            avg_temp = float(request.form["avg_temp"])
            rainfall = float(request.form["rainfall"])

            features = pd.DataFrame(
                [[Year, pesticides_tonnes, avg_temp, rainfall, Area, Item]],
                columns=["Year", "pesticides_tonnes", "avg_temp", "average_rain_fall_mm_per_year", "Area", "Item"]
            )

            transformed_features = preprocessor.transform(features)
            prediction = dtr.predict(transformed_features)[0]

            new_prediction = PredictionsCrop(
                Year=Year, Area=Area, Item=Item,
                pesticides_tonnes=pesticides_tonnes, avg_temp=avg_temp,
                average_rain_fall_mm_per_year=rainfall, prediction=prediction
            )
            db.session.add(new_prediction)
            db.session.commit()

            return jsonify({"prediction": prediction, "success": True})

        except Exception as e:
            db.session.rollback()
            print("Error:", str(e))
            return jsonify({"error": str(e), "success": False})

    return render_template("indexapp.html", years=years, countries=countries, crops=crops)

@app.route('/download_report', methods=['POST'])
def download_report():
    try:
        data = request.json
        Year = data.get('Year', 'N/A')
        Area = data.get('Area', 'N/A')
        Item = data.get('Item', 'N/A')
        pesticides_tonnes = float(data.get('pesticides_tonnes', 0))
        avg_temp = float(data.get('avg_temp', 0))
        rainfall = float(data.get('rainfall', 0))
        prediction = float(data.get('prediction', 0))


        report_path = "dynamic_report.pdf"
        pdf = canvas.Canvas(report_path, pagesize=letter)


        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(100, 750, "Farmify: Crop Yield Prediction Report")


        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.grey)

        pdf.setFillColor(colors.black)

        y_position = 710
        def add_text(text, font="Helvetica", size=10, spacing=15):
            nonlocal y_position
            if y_position <= 50:
                pdf.showPage()
                y_position = 750
            pdf.setFont(font, size)
            pdf.drawString(120, y_position, text)
            y_position -= spacing


        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, y_position, "About Farmify:")
        y_position -= 20
        add_text("Farmify is an advanced agricultural analytics platform that helps farmers")
        add_text("enhance productivity by leveraging data-driven crop yield predictions.")
        add_text("With the use of machine learning models like Decision Tree Regressor,")
        add_text("Farmify analyzes factors like pesticides usage, temperature, and rainfall.")


        y_position -= 20
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, y_position, "Model and Features Used:")
        y_position -= 15
        add_text("- Decision Tree Regressor (DTR) model for predictions.")
        add_text("- Features include Year, Pesticides (tonnes), Average Temperature, and Rainfall.")


        y_position -= 20
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, y_position, "Prediction Results:")
        y_position -= 15
        results_lines = [
            f"Year: {Year}",
            f"Area: {Area}",
            f"Item: {Item}",
            f"Pesticides (tonnes): {pesticides_tonnes:.2f}",
            f"Average Temperature (°C): {avg_temp:.2f}",
            f"Rainfall (mm): {rainfall:.2f}",
            f"Predicted Yield (tonnes): {prediction:.2f}"
        ]

        for line in results_lines:
            add_text(line)


        recommendations = get_default_recommendations(Item)
        if recommendations:
            y_position -= 20
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(100, y_position, f"Recommendations for {Item.capitalize()}:")
            y_position -= 15
            for key, value in recommendations.items():
                add_text(f"{key.capitalize()}: {value}")


        y_position -= 20
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, y_position, "General Agricultural Tips:")
        y_position -= 15
        tips = [
            "1. Rotate crops to maintain soil fertility.",
            "2. Use organic compost to enrich the soil.",
            "3. Implement proper irrigation methods to prevent water wastage.",
            "4. Monitor weather conditions for pest control.",
            "5. Regularly test soil pH and nutrient levels."
        ]

        for tip in tips:
            add_text(tip)


        y_position -= 20
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, y_position, "Conclusion:")
        y_position -= 15
        add_text("Using the right guidance, farmers can maximize productivity and enhance soil health.")

        pdf.save()

        return send_file(report_path, as_attachment=True)

    except Exception as e:
        print("Error while generating report:", str(e))
        return jsonify({'error': str(e), 'success': False}), 400


@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json.get("query", "").lower().strip()

    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]

    if not user_query:
        return jsonify({"response": "Please provide a question."})

    if any(greeting in user_query for greeting in greetings):
        return jsonify({
            "response": "Hello! I can provide information about:\n- Average temperature,\n- Rainfall,\n- Pesticide Usage,\n- Weather forecasts for specific areas,\n- Crop recommendations for specific areas,\n- Agricultural Tips for crops.\n\nPlease ask your question in this format: 'What is the average temperature in [Area]?' or 'Recommendation of crops in [Area]?'"
        })

    print(f"User query: {user_query}")

    areas = data['Area'].str.lower().unique()
    crops = data['Item'].str.lower().unique()

    found_area = next((area for area in areas if area in user_query), None)
    found_crop = next((crop for crop in crops if crop in user_query), None)

    print(f"Found area: {found_area}, Found crop: {found_crop}")

    # Checking for incorrect terms
    incorrect_terms = []
    if found_area is None and any(word in user_query for word in areas):
        incorrect_terms.append("area")
    if found_crop is None and any(word in user_query for word in crops):
        incorrect_terms.append("crop")

    if incorrect_terms:
        suggestion = []
        if "area" in incorrect_terms:
            suggestion.append("Did you mean one of these areas? " + ", ".join(areas))
        if "crop" in incorrect_terms:
            suggestion.append("Did you mean one of these crops? " + ", ".join(crops))
        return jsonify({"response": "I could not understand your question. " + " ".join(suggestion)})

    # Handling average data queries
    if found_area and "average" in user_query:
        average_data = []

        # Check for average temperature request
        if "temperature" in user_query:
            avg_temp = data[data['Area'].str.lower() == found_area]['avg_temp'].mean()
            if avg_temp is not None:
                average_data.append(f"Average Temperature in {found_area.capitalize()}: {avg_temp:.2f} °C.")

                # Get crop recommendations based on this temperature
                recommendations = get_temperature_based_recommendations(avg_temp)
                average_data.append(recommendations)
            else:
                return jsonify({"response": f"No temperature data available for {found_area.capitalize()}."})

        # Check for average rainfall request
        if "rainfall" in user_query:
            avg_rainfall = data[data['Area'].str.lower() == found_area]['average_rain_fall_mm_per_year'].mean()
            average_data.append(f"Average Rainfall in {found_area.capitalize()}: {avg_rainfall:.2f} mm.")

        # Check for average pesticide usage request
        if "pesticide usage" in user_query:
            avg_pesticides = data[data['Area'].str.lower() == found_area]['pesticides_tonnes'].mean()
            average_data.append(f"Average Pesticide usage in {found_area.capitalize()}: {avg_pesticides:.2f} tonnes.")

        return jsonify({"response": " | ".join(average_data)})

    # Handle crop recommendations based on found area
    if found_area and "recommendation" in user_query:
        crop_recommendations = create_yield_recommendations(data).get(found_area, {})
        if crop_recommendations:
            best_crop = crop_recommendations.get('best_crop', None)
            if best_crop:
                response = f"The best crop to plant in {found_area} is {best_crop[0]} with an average yield of {best_crop[1]:.2f} hg/ha."
                return jsonify({"response": response})
            else:
                return jsonify({"response": "No crop recommendations available for this area."})

    # Handle fertilizer requests for found crops
    if found_crop and "fertilizer" in user_query:
        recommendations = get_default_recommendations(found_crop)
        response = (
            f"Fertilizer recommendations for {found_crop}: "
            f"{recommendations.get('fertilizers', 'No information available.')}"
        )
        return jsonify({"response": response})


    # Handle pesticide requests for found crops
    if found_crop and "pesticide" in user_query:
        recommendations = get_default_recommendations(found_crop)
        response = (
            f"Pesticide recommendations for {found_crop}: "
            f"{recommendations.get('pesticides', 'No information available.')}"
        )
        return jsonify({"response": response})

    return jsonify({"response": "I could not understand your question. Please ask about average temperature, rainfall information, weather forecasts, or crop recommendations in the following format: 'What is the average temperature in [Area]?' or 'What are the best crops to grow in [Area]?'."})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)