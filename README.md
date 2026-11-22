# RESQAI – AI-Powered Disaster Response & Rescue Management System

**RESQAI** is an AI-powered disaster response platform designed to support faster, smarter, and more coordinated emergency management. It helps identify disaster-affected areas, visualize incidents on an interactive map, assess damage, and support rescue and relief operations.

https://resqai-0dsu.onrender.com

## 🚀 Key Features

- **Disaster Monitoring:** Monitor active disaster events through a centralized dashboard.
- **Interactive Live Map:** Visualize disaster locations and affected areas using Leaflet.js.
- **AI-Powered Damage Assessment:** Designed to analyze drone, satellite, and street-level images to identify damaged buildings and affected infrastructure.
- **Incident Visualization:** Display disaster-related information and emergency events geographically.
- **Route Visualization:** Support route selection and distance estimation for emergency response planning.
- **Earthquake & Fire Monitoring:** Display live earthquake and fire-related information through available data sources.
- **Response Prioritization:** Support the identification of vulnerable areas and prioritization of rescue and relief operations.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Mapping | Leaflet.js |
| Database | SQLite |
| Map Tiles | CARTO / Esri |
| Version Control | Git & GitHub |
| Deployment | Render |

## 📂 Project Structure

```text
RESQAI/
│
├── manage.py
├── requirements.txt
├── db.sqlite3
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── base.html
│   └── dashboard.html
│
├── [Django application folders]/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── serializers.py
│
└── README.md
```

*The structure above is illustrative; actual folders may differ.*

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/RESQAI.git
cd RESQAI
```

### 2. Create a Virtual Environment

```bash
python -m venv env
```

Activate it on Windows:

```bash
env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create an Admin Account

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Open the application:

```text
http://127.0.0.1:8000/
```

## 🌍 How RESQAI Works

1. Disaster-related information and available imagery are collected.
2. The platform processes available incident information.
3. Disaster locations and events are displayed on an interactive map.
4. Damage assessment and vulnerability information help identify priority areas.
5. Emergency teams can use the available information for rescue and relief planning.

## 🎯 Project Objective

The primary objective of RESQAI is to improve disaster response by combining artificial intelligence, geospatial visualization, and centralized incident monitoring.

The platform aims to reduce response delays, improve situational awareness, and help emergency responders make more informed decisions.

## 🔮 Future Enhancements

- Advanced AI-based building damage detection.
- Automated drone and satellite image processing.
- Real-time emergency team tracking.
- Smart rescue route optimization.
- Disaster severity prediction.
- Automated resource allocation.
- Integration with additional government and emergency data sources.

## 👨‍💻 Development Team

**Project:** RESQAI  
**Hackathon:** Smart India Hackathon (SIH)  
**Team:** CodeCrest

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Commit and push your changes.
5. Submit a pull request.

## 📄 License

This project is developed for educational, innovation, and disaster-management purposes. Add a suitable open-source license before allowing reuse or redistribution.

---

**RESQAI – Smarter Technology. Faster Response. Safer Communities.**
