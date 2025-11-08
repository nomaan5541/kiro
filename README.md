# School Management System

A comprehensive web-based school management system built with Flask, featuring student enrollment, attendance tracking, fee management, and multi-role authentication.

## 🚀 Features

### 👥 Multi-Role Authentication
- **Super Admin**: System-wide management and school registration
- **School Admin**: Complete school operations management
- **Teacher**: Class management and attendance tracking
- **Student**: Personal dashboard and information access

### 🎓 Student Management
- Student enrollment and profile management
- Class assignment and academic tracking
- Photo upload and ID card generation
- Comprehensive student search and filtering

### 📋 Attendance System
- Daily attendance marking with bulk operations
- Real-time attendance statistics and reporting
- Class-wise and student-wise attendance tracking
- Automated attendance notifications

### 💰 Fee Management
- Flexible fee structure configuration
- Multiple payment modes (Cash, Online, Cheque, Bank Transfer)
- Payment tracking and receipt generation
- Fee status visualization and overdue management

### 📊 Reports & Analytics
- Attendance reports and summaries
- Fee collection reports
- Student performance analytics
- School overview dashboards

### 🔔 Notification System
- SMS and WhatsApp integration ready
- Automated attendance alerts
- Payment confirmations
- Customizable message templates

## 🛠 Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Tailwind CSS
- **Authentication**: Session-based with role management
- **PDF Generation**: ReportLab for receipts and reports
- **Notifications**: SMS/WhatsApp API integration

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd school-management-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Initialize Database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## 🔐 Default Login Credentials

### Super Admin
- **Email**: admin@schoolsystem.com
- **Password**: admin123

### Demo School Admin
- **Email**: demo@school.com
- **Password**: school123

### Teacher
- **Email**: teacher@demo.com
- **Password**: teacher123

### Student
- **Email**: student@demo.com
- **Password**: student123

## 📁 Project Structure

```
school-management-system/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── extensions.py         # Flask extensions
├── run.py               # Application entry point
├── init_db.py           # Database initialization
├── requirements.txt     # Python dependencies
├── blueprints/          # Route blueprints
│   ├── auth.py         # Authentication routes
│   ├── super_admin.py  # Super admin routes
│   ├── school_admin.py # School admin routes
│   ├── teacher.py      # Teacher routes
│   ├── student.py      # Student routes
│   └── api.py          # API endpoints
├── models/             # Database models
│   ├── user.py        # User model
│   ├── school.py      # School model
│   ├── classes.py     # Class and Subject models
│   ├── student.py     # Student model
│   ├── attendance.py  # Attendance models
│   ├── fee.py         # Fee and Payment models
│   ├── activity.py    # Activity logging
│   └── notification.py # Notification models
├── services/           # Business logic services
│   ├── payment_service.py
│   └── report_service.py
├── utils/              # Utility functions
│   ├── auth.py        # Authentication utilities
│   ├── helpers.py     # General helpers
│   ├── validators.py  # Input validation
│   ├── pdf_generator.py # PDF generation
│   └── notification_service.py
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── auth/          # Authentication templates
│   ├── super_admin/   # Super admin templates
│   ├── school_admin/  # School admin templates
│   ├── teacher/       # Teacher templates
│   ├── student/       # Student templates
│   └── errors/        # Error pages
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── images/       # Images and icons
└── instance/         # Instance-specific files
    └── *.db          # SQLite database files
```

## 🎨 Theme & Design

The application uses the **Tactical Ops v2.1.7** theme featuring:
- Dark background (#101010)
- Orange accent color (#FF6F00)
- Monospace fonts (JetBrains Mono, Fira Code)
- Responsive design with mobile support
- Smooth animations and hover effects

## 🔧 Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/school_management.db
JWT_SECRET_KEY=your-jwt-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SMS_API_KEY=your-sms-api-key
WHATSAPP_API_KEY=your-whatsapp-api-key
```

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL (recommended)

## 📱 API Endpoints

The system provides RESTful API endpoints for:
- User authentication
- Student management
- Attendance tracking
- Payment processing
- Report generation

API documentation is available at `/api/docs` when running the application.

## 🧪 Testing

Run tests using:
```bash
python -m pytest tests/
```

## 📈 Performance

- Optimized database queries with proper indexing
- Caching for frequently accessed data
- Pagination for large data sets
- Compressed static assets

## 🔒 Security Features

- Password hashing with bcrypt
- Session-based authentication
- Role-based access control
- Input validation and sanitization
- CSRF protection
- SQL injection prevention

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact: support@schoolsystem.com
- Documentation: [Wiki](https://github.com/your-repo/wiki)

## 🚀 Deployment

### Production Deployment

1. **Set up production environment**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@localhost/dbname
   ```

2. **Install production dependencies**
   ```bash
   pip install gunicorn psycopg2-binary
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📊 Monitoring

- Application logs are stored in `logs/` directory
- Health check endpoint: `/health`
- Metrics endpoint: `/metrics`

---

**Built with ❤️ for educational institutions worldwide**