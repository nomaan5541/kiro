# School Management System API Documentation

## Overview

The School Management System provides a RESTful API for programmatic access to all system features. All API endpoints require authentication and follow REST conventions.

## Base URL
```
http://localhost:5000/api
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Get Authentication Token

**POST** `/api/login`

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "role": "school_admin"
  }
}
```

## Students API

### List Students

**GET** `/api/students`

Query Parameters:
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 25)
- `search` (string): Search by name, admission number, or roll number
- `class_id` (int): Filter by class ID
- `status` (string): Filter by status (active, inactive, graduated, transferred)

**Response:**
```json
{
  "students": [
    {
      "id": 1,
      "name": "John Doe",
      "admission_no": "STU001",
      "roll_number": "10A001",
      "class_id": 1,
      "status": "active",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 25,
    "total": 120
  }
}
```

### Get Student Details

**GET** `/api/students/{student_id}`

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "admission_no": "STU001",
  "roll_number": "10A001",
  "father_name": "Robert Doe",
  "mother_name": "Jane Doe",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "9876543210",
  "email": "john.doe@example.com",
  "address": "123 Main Street, City",
  "blood_group": "O+",
  "class_info": {
    "id": 1,
    "class_name": "Class 10",
    "section": "A"
  },
  "status": "active",
  "created_at": "2024-01-15T10:30:00"
}
```

### Create Student

**POST** `/api/students`

```json
{
  "name": "John Doe",
  "admission_no": "STU001",
  "roll_number": "10A001",
  "class_id": 1,
  "father_name": "Robert Doe",
  "mother_name": "Jane Doe",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "9876543210",
  "email": "john.doe@example.com",
  "address": "123 Main Street, City",
  "blood_group": "O+"
}
```

### Update Student

**PUT** `/api/students/{student_id}`

Same payload as create student.

### Delete Student

**DELETE** `/api/students/{student_id}`

## Attendance API

### Mark Attendance

**POST** `/api/attendance`

```json
{
  "class_id": 1,
  "date": "2024-01-15",
  "attendance_data": [
    {
      "student_id": 1,
      "status": "present"
    },
    {
      "student_id": 2,
      "status": "absent"
    }
  ]
}
```

### Get Attendance

**GET** `/api/attendance`

Query Parameters:
- `class_id` (int): Class ID
- `date` (string): Date in YYYY-MM-DD format
- `student_id` (int): Specific student ID
- `start_date` (string): Start date for range
- `end_date` (string): End date for range

**Response:**
```json
{
  "attendance_records": [
    {
      "id": 1,
      "student_id": 1,
      "student_name": "John Doe",
      "class_id": 1,
      "date": "2024-01-15",
      "status": "present",
      "marked_by": 2,
      "marked_at": "2024-01-15T09:30:00"
    }
  ]
}
```

### Get Attendance Summary

**GET** `/api/attendance/summary/{student_id}`

Query Parameters:
- `month` (int): Month (1-12)
- `year` (int): Year

**Response:**
```json
{
  "student_id": 1,
  "month": 1,
  "year": 2024,
  "total_days": 22,
  "present_days": 20,
  "absent_days": 2,
  "leave_days": 0,
  "attendance_percentage": 90.91
}
```

## Payments API

### Record Payment

**POST** `/api/payments`

```json
{
  "student_id": 1,
  "amount": 5000.00,
  "payment_mode": "cash",
  "transaction_id": "TXN123456",
  "remarks": "First installment payment"
}
```

**Response:**
```json
{
  "success": true,
  "payment": {
    "id": 1,
    "receipt_no": "RCP001202401150001",
    "amount": 5000.00,
    "payment_date": "2024-01-15",
    "status": "completed"
  }
}
```

### Get Payment History

**GET** `/api/payments/student/{student_id}`

**Response:**
```json
{
  "payments": [
    {
      "id": 1,
      "receipt_no": "RCP001202401150001",
      "amount": 5000.00,
      "payment_date": "2024-01-15",
      "payment_mode": "cash",
      "status": "completed"
    }
  ],
  "fee_status": {
    "total_fee": 50000.00,
    "paid_amount": 5000.00,
    "remaining_amount": 45000.00,
    "payment_percentage": 10.0
  }
}
```

## Classes API

### List Classes

**GET** `/api/classes`

**Response:**
```json
{
  "classes": [
    {
      "id": 1,
      "class_name": "Class 10",
      "section": "A",
      "capacity": 60,
      "student_count": 35,
      "academic_year": "2024-25"
    }
  ]
}
```

### Get Class Details

**GET** `/api/classes/{class_id}`

**Response:**
```json
{
  "id": 1,
  "class_name": "Class 10",
  "section": "A",
  "capacity": 60,
  "academic_year": "2024-25",
  "students": [
    {
      "id": 1,
      "name": "John Doe",
      "roll_number": "10A001"
    }
  ],
  "subjects": [
    {
      "id": 1,
      "name": "Mathematics",
      "code": "MATH"
    }
  ]
}
```

## Reports API

### Attendance Report

**GET** `/api/reports/attendance`

Query Parameters:
- `class_id` (int): Filter by class
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)
- `format` (string): Response format (json, csv, pdf)

### Fee Collection Report

**GET** `/api/reports/fees`

Query Parameters:
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)
- `format` (string): Response format (json, csv, pdf)

### School Overview Report

**GET** `/api/reports/overview`

**Response:**
```json
{
  "school_info": {
    "name": "Demo School",
    "total_students": 150,
    "total_classes": 12
  },
  "statistics": {
    "overall_attendance_percentage": 89.5,
    "fee_collection_percentage": 75.2,
    "total_fees_collected": 2500000.00,
    "outstanding_fees": 825000.00
  }
}
```

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": {
    "field": "Specific field error"
  }
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

API requests are limited to:
- **Authentication endpoints**: 5 requests per minute
- **Data modification endpoints**: 60 requests per minute
- **Read-only endpoints**: 100 requests per minute

## Webhooks

The system supports webhooks for real-time notifications:

### Payment Webhook

**POST** `{your_webhook_url}`

```json
{
  "event": "payment.completed",
  "data": {
    "payment_id": 1,
    "student_id": 1,
    "amount": 5000.00,
    "receipt_no": "RCP001202401150001"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Attendance Webhook

**POST** `{your_webhook_url}`

```json
{
  "event": "attendance.marked",
  "data": {
    "student_id": 1,
    "class_id": 1,
    "date": "2024-01-15",
    "status": "absent"
  },
  "timestamp": "2024-01-15T09:30:00Z"
}
```

## SDK and Libraries

### Python SDK

```python
from school_management_sdk import SchoolAPI

api = SchoolAPI(base_url="http://localhost:5000/api", token="your-jwt-token")

# Get students
students = api.students.list(page=1, per_page=25)

# Mark attendance
api.attendance.mark(class_id=1, date="2024-01-15", attendance_data=[
    {"student_id": 1, "status": "present"},
    {"student_id": 2, "status": "absent"}
])

# Record payment
payment = api.payments.create(
    student_id=1,
    amount=5000.00,
    payment_mode="cash"
)
```

### JavaScript SDK

```javascript
import SchoolAPI from 'school-management-js-sdk';

const api = new SchoolAPI({
  baseURL: 'http://localhost:5000/api',
  token: 'your-jwt-token'
});

// Get students
const students = await api.students.list({ page: 1, perPage: 25 });

// Mark attendance
await api.attendance.mark({
  classId: 1,
  date: '2024-01-15',
  attendanceData: [
    { studentId: 1, status: 'present' },
    { studentId: 2, status: 'absent' }
  ]
});
```

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Multi-role authentication system
- Student management
- Attendance tracking
- Fee management
- Basic reporting
- Notification system framework

### Planned Features (v1.1.0)
- Advanced analytics dashboard
- Mobile app support
- Bulk data import/export
- Advanced notification templates
- Integration with external payment gateways
- Multi-language support

---

For more detailed information, please refer to the inline code documentation and the user manual.