<div align="center">

  <img src="assets/default.png" alt="ScholarSync Logo" width="150" />
  
  # ScholarSync
  
  <a href="https://readme-typing-svg.herokuapp.com?font=Poppins&size=24&color=36BCF7&center=true&vCenter=true&width=500&lines=Stop+Studying+Alone.;Start+Studying+Together.">
    <img src="https://readme-typing-svg.herokuapp.com?font=Poppins&size=24&color=36BCF7&center=true&vCenter=true&width=500&lines=Stop+Studying+Alone.;Start+Studying+Together." alt="Stop Studying Alone. Start Studying Together." />
  </a>

  <br>
  
  <p align="center">
    <a href="https://www.python.org/" target="_blank">
      <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
    </a>
    <a href="https://www.djangoproject.com/" target="_blank">
      <img src="https://img.shields.io/badge/Django-4.x-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django Version">
    </a>
    <a href="https://github.com/eswardas/scholarsync/actions" target="_blank">
      <img src="https://img.shields.io/github/actions/workflow/status/eswardas/scholarsync/django.yml?branch=main&style=for-the-badge" alt="Build Status">
    </a>
    <a href="https://github.com/eswardas/scholarsync/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/eswardas/scholarsync?style=for-the-badge&color=purple" alt="License">
    </a>
  </p>

</div>

**ScholarSync** is a next-generation collaborative learning platform built on Django. It transcends traditional study groups by providing a persistent, real-time environment for students to connect, share, and achieve academic excellence. This isn't just a chat room; it's a dedicated ecosystem for focused, community-driven learning.

---

## ✨ Features & Live Demo

| Feature | Preview |
| :--- | :--- |
| **Real-Time Chat & Replies** | <img src="" alt="Live Chat Demo" width="600"> |
| **Private Room Creation** | <img src="" alt="Private Room Demo" width="600"> |
| **Advanced Admin Moderation** | <img src="" alt="Moderation Demo" width="600"> |

---

## 🛠️ Tech Stack & Architecture

This platform is built on a scalable and powerful stack.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap">
  <img src="https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white" alt="jQuery">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

### Architectural Model
ScholarSync operates on a robust client-server model.
1.  **Django Backend (The Core):** Serves all HTML templates and handles all business logic. This includes authentication, permissions, and database operations.
2.  **AJAX Polling Engine (The "Live" Feel):** The client-side (`room.html`) contains JavaScript that polls the server every 2 seconds via a dedicated API endpoint (`get_room_data`). This fetches *only* new messages, providing a real-time chat experience without the overhead of persistent WebSocket connections.
3.  **API Endpoints (The Actions):** Nearly every user interaction (voting, deleting, reporting) is handled by a dedicated AJAX `POST` endpoint. This allows for instant UI updates without a full page reload.

---

## 🚀 Core Features Matrix

| Feature Module | Capability | Status |
| :--- | :--- | :---: |
| **Real-Time Hub** | Live room discussions via efficient AJAX polling. | ✅ |
| | Dynamic participant list updates. | ✅ |
| | "My Recent Activity" live-feed on dashboard. | ✅ |
| **Room Management** | **Public Rooms:** Discoverable rooms based on topics. | ✅ |
| | **Private Rooms:** Secure, invite-only rooms with auto-generated 8-character IDs and passwords. | ✅ |
| **User Engagement** | **Rich Messages:** Post replies, text, and file attachments (images, audio, video, docs). | ✅ |
| | **Voting System:** Upvote/downvote messages to promote quality content. | ✅ |
| | **User Profiles:** Public profiles with stats, bios, and activity feeds. | ✅ |
| **Advanced Moderation** | **Report System:** Users can report any message for admin review. | ✅ |
| | **Admin Dashboard:** Centralized queue for all reports, with search and filtering. | ✅ |
| | **Moderator Actions:** Resolve reports, delete messages, **suspend** users for N days, or **ban** (delete) users. | ✅ |
| | **Suspension Enforcement:** Suspended users are automatically blocked at the login gate. | ✅ |

---

## ⚡ Get Started: Local Deployment

Launch your own ScholarSync instance in minutes.

### 1. Prerequisites
* Python 3.10+
* `pip` (Python package installer)

### 2. Installation & Setup
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/eswardas/scholarsync.git](https://github.com/eswardas/scholarsync.git)
    cd scholarsync
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt 
    ```
    *(**Note:** You will need to create a `requirements.txt` file by running `pip freeze > requirements.txt` in your local environment.)*

4.  **Run Database Migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create a Superuser (Admin):**
    ```bash
    python manage.py createsuperuser
    ```
    *(Follow the prompts to create your admin account for accessing the moderation panel.)*

6.  **Launch the Server!**
    ```bash
    python manage.py runserver
    ```
    Your instance is now live at `http://127.0.0.1:8000/`.

---

## 📊 Repository Stats

<div align="center">
  <img src="https://github-readme-stats.vercel.app/api?username=eswardas&repo=scholarsync&show_icons=true&theme=gotham" alt="Repository Stats" />
  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=eswardas&layout=compact&theme=gotham" alt="Top Languages" />
</div>

---

## <details><summary>🔬 Deep Dive: The Moderation Engine</summary>
<br>

A standout feature is the `admin_report_action` view, which serves as a secure, centralized API for all moderator actions.

* It's protected by two decorators: `@require_POST` (preventing `GET` requests) and `@user_passes_test` (ensuring only superusers can access it).
* It receives an `action` (e.g., `'suspend_user'`) from the admin dashboard's JavaScript.
* A single `if/elif` block routes to the correct logic:
    * **`ban_user`**: `author.delete()` - Permanently deletes the user.
    * **`suspend_user`**: Calculates `timezone.now() + timedelta(days=days)` and saves it to the `UserProfile.suspended_until` field. The `loginPage` view then checks this field, enforcing the ban.
    * **`delete_message`**: `msg.delete()` - Removes the offending message.
* This design is secure, efficient, and easily extensible.

</details>

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository, create a new feature branch, and submit a pull request for review.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
