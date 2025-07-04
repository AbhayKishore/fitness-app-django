
# Fitness App Django

A Django-based virtual fitness companion that generates workout plans based on assessments, tracks nutrition intake, and manages trainer-customer sessions.

## Features

- AI-powered workout plans (bulk, cut, maintenance)
- Diet logging & nutrient tracking using AI
- Admin, Trainer, and Customer dashboards
- Built with Django + MySQL

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AbhayKishore/fitness-app-django/blob/main/LICENSE)

A comprehensive web-based **Fitness Management System** built with Django and MySQL that connects fitness enthusiasts with trainers, helps track workouts, progress, and offers a virtual fitness companion experience.

---

## 🎯 Project Overview

Fitness App Django is designed to make fitness tracking and training management seamless for both customers and trainers. Whether you want to log workouts, book sessions, or monitor progress, this app helps bridge the gap between users and fitness professionals in a simple, user-friendly way.

---

## 🚀 Features

- **User Authentication**: Secure login system for customers and trainers.
- **Workout Planner**: Customized workout plans based on user goals and assessments with the help of API.
- **Exercise Tracking**: Log and monitor workouts, track progress over time.
- **Trainer-Customer Interaction**: Trainers can create and update workout plans and schedule sessions.
- **Session Booking & Management**: Book, cancel, and manage fitness sessions easily.
- **Progress Assessments**: Periodically assess fitness parameters to tailor plans.
- **Diet Intake Tracker**: Log daily nutrition intake (calories, macros, water) along with using AI to convert your food to macros.
- **Payment Management**: Track payments for training sessions.
- **Responsive UI**: Clean and accessible user interface for all users.

---

## 🛠️ Technology Stack

- **Backend:** Django (Python)
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **APIs:** AJAX for asynchronous updates
- **Deployment:** Can be deployed on any WSGI-compatible server

---

## 📁 Installation & Setup

To run this project locally:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AbhayKishore/fitness-app-django.git

2. **Navigate into the directory:**

   ```bash
   cd fitness-app-django
   ```

3. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

4. **Set up environment variables:**

   * Copy `.env.example` to `.env` in your project root:

     ```bash
     cp .env.example .env
     ```

   * Open `.env` and paste your actual API keys, database credentials, and other sensitive info.


5. **Configure your database:**

   * Ensure your MySQL database is set up and credentials match those in `.env` and your Django `settings.py`.

6. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

7. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

8. **Open your browser:**

   Go to `http://127.0.0.1:8000/Home` to access the app.

---

## 📄 License

This project is licensed under the MIT License.

For full details, see the LICENSE file.

---

© 2025 Abhay Kishore
All rights reserved.

Please give proper credit to **Abhay Kishore** when using or referencing this project in any form.

```python
# Copyright (c) 2025 Abhay Kishore
# Licensed under the MIT License
```

---

## 🤝 Contributions
Contributions and suggestions are welcome! Feel free to open issues or submit pull requests to improve the app.
---

## 📞 Contact
For any queries or support, reach out via email:
**Abhay Kishore** – [abhaykishore2004@gmail.com](mailto:abhaykishore2004@gmail.com)

