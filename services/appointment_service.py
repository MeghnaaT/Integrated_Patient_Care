# =============================================================================
# services/appointment_service.py — Service layer for Appointment Management
# =============================================================================
# Handles booking, updating, cancellation, timing validation against doctor hours,
# and database conflict prevention.
# =============================================================================

from typing import List, Optional, Tuple
import datetime
from database.connection import db
from models.appointment import Appointment


def parse_available_time(avail_str: str) -> Optional[Tuple[datetime.time, datetime.time]]:
    """Parse a doctor's availability string (e.g. '10:00 AM - 01:00 PM') into time objects."""
    try:
        parts = avail_str.split('-')
        if len(parts) != 2:
            return None
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        
        start_time = datetime.datetime.strptime(start_str, "%I:%M %p").time()
        end_time = datetime.datetime.strptime(end_str, "%I:%M %p").time()
        return start_time, end_time
    except Exception:
        return None


def check_doctor_availability(
    doctor_id: int, 
    date: datetime.date, 
    time: datetime.time, 
    exclude_appt_id: Optional[int] = None
) -> Tuple[bool, str]:
    """Verify if the doctor is within active hours and does not have an overlapping booking."""
    from models.doctor import Doctor
    
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return False, "Doctor profile not found."

    # 1. Validate doctor's hours
    avail = parse_available_time(doctor.available_time)
    if avail:
        start_time, end_time = avail
        # Compare times
        if not (start_time <= time <= end_time):
            return False, f"Selected time falls outside of Dr. {doctor.last_name}'s available hours ({doctor.available_time})."

    # 2. Check for overlapping appointment
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == date,
        Appointment.appointment_time == time,
        Appointment.status != 'Cancelled'
    )
    if exclude_appt_id:
        query = query.filter(Appointment.id != exclude_appt_id)

    conflict = query.first()
    if conflict:
        return False, "This doctor is already scheduled for another consultation at this exact date and time."

    return True, ""


def check_patient_conflict(
    patient_id: int, 
    date: datetime.date, 
    time: datetime.time, 
    exclude_appt_id: Optional[int] = None
) -> Tuple[bool, str]:
    """Verify if the patient does not have another active booking at the same slot."""
    query = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.appointment_date == date,
        Appointment.appointment_time == time,
        Appointment.status != 'Cancelled'
    )
    if exclude_appt_id:
        query = query.filter(Appointment.id != exclude_appt_id)

    conflict = query.first()
    if conflict:
        return False, "This patient already has another active appointment scheduled at this exact date and time."

    return True, ""


def book_appointment(data: dict) -> Tuple[Optional[Appointment], str]:
    """Create and persist a new appointment after validation checks."""
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    appt_date = data.get('appointment_date')
    appt_time = data.get('appointment_time')
    status = data.get('status', 'Pending')

    if not patient_id or not doctor_id or not appt_date or not appt_time:
        return None, "All scheduling fields (Patient, Doctor, Date, Time) are required."

    # Validate date is not in the past
    if appt_date < datetime.date.today():
        return None, "Appointment date cannot be in the past."

    # Check doctor availability
    ok, err = check_doctor_availability(doctor_id, appt_date, appt_time)
    if not ok:
        return None, err

    # Check patient conflict
    ok, err = check_patient_conflict(patient_id, appt_date, appt_time)
    if not ok:
        return None, err

    # Create record
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        appointment_time=appt_time,
        status=status
    )
    db.session.add(appt)

    # Trigger Booking Notification
    from services.notification_service import send_notification
    from models.doctor import Doctor
    doc = db.session.get(Doctor, doctor_id)
    doc_name = f"Dr. {doc.full_name}" if doc else f"Doctor ID: {doctor_id}"
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Your appointment with {doc_name} has been booked for {appt_date} at {appt_time}. Status: {status}. Created at: {ts}."
    send_notification(patient_id, 'Appointment Reminder', msg, commit=False)

    db.session.commit()
    return appt, ""


def update_appointment(appt_id: int, data: dict) -> Tuple[Optional[Appointment], str]:
    """Update scheduling details or status for an existing appointment."""
    appt = Appointment.query.get_or_404(appt_id)

    patient_id = data.get('patient_id', appt.patient_id)
    doctor_id = data.get('doctor_id', appt.doctor_id)
    appt_date = data.get('appointment_date', appt.appointment_date)
    appt_time = data.get('appointment_time', appt.appointment_time)
    status = data.get('status', appt.status)

    # Validate date is not in the past if it's changing
    if appt_date != appt.appointment_date and appt_date < datetime.date.today():
        return None, "Appointment date cannot be in the past."

    # Validate doctor conflict (exclude current appt)
    ok, err = check_doctor_availability(doctor_id, appt_date, appt_time, exclude_appt_id=appt_id)
    if not ok:
        return None, err

    # Validate patient conflict (exclude current appt)
    ok, err = check_patient_conflict(patient_id, appt_date, appt_time, exclude_appt_id=appt_id)
    if not ok:
        return None, err

    # Track status and scheduling modifications
    old_date = appt.appointment_date
    old_time = appt.appointment_time
    old_status = appt.status
    old_doctor_id = appt.doctor_id

    # Save updates
    appt.patient_id = patient_id
    appt.doctor_id = doctor_id
    appt.appointment_date = appt_date
    appt.appointment_time = appt_time
    appt.status = status

    # Trigger notifications based on update type
    rescheduled = (appt_date != old_date or appt_time != old_time or doctor_id != old_doctor_id)
    status_changed = (status != old_status)

    from services.notification_service import send_notification
    from models.doctor import Doctor
    doc = db.session.get(Doctor, doctor_id)
    doc_name = f"Dr. {doc.full_name}" if doc else f"Doctor ID: {doctor_id}"

    if rescheduled:
        msg = f"Your appointment with {doc_name} has been rescheduled to {appt_date} at {appt_time}. Status: {status}."
        send_notification(patient_id, 'Appointment Reminder', msg, commit=False)
    elif status_changed:
        msg = f"Your appointment with {doc_name} on {appt_date} at {appt_time} is now {status}."
        send_notification(patient_id, 'Appointment Reminder', msg, commit=False)

    db.session.commit()
    return appt, ""


def cancel_appointment(appt_id: int) -> Appointment:
    """Set the status of an appointment to Cancelled."""
    appt = Appointment.query.get_or_404(appt_id)
    old_status = appt.status
    appt.status = 'Cancelled'

    if old_status != 'Cancelled':
        from services.notification_service import send_notification
        from models.doctor import Doctor
        doc = db.session.get(Doctor, appt.doctor_id)
        doc_name = f"Dr. {doc.full_name}" if doc else f"Doctor ID: {appt.doctor_id}"
        msg = f"Your appointment with {doc_name} on {appt.appointment_date} at {appt.appointment_time} is now Cancelled."
        send_notification(appt.patient_id, 'Appointment Reminder', msg, commit=False)

    db.session.commit()
    return appt


def get_appointment(appt_id: int) -> Appointment:
    """Retrieve a single appointment by ID."""
    return Appointment.query.get_or_404(appt_id)


def list_appointments(
    page: int = 1,
    per_page: int = 10,
    filters: Optional[dict] = None,
    sort_by: str = "appointment_date",
    sort_dir: str = "asc",
) -> Tuple[List[Appointment], int]:
    """List appointments with sorting, filtering, and pagination."""
    query = Appointment.query

    # Apply filters
    if filters:
        if filters.get('patient_id'):
            query = query.filter(Appointment.patient_id == filters['patient_id'])
        if filters.get('doctor_id'):
            query = query.filter(Appointment.doctor_id == filters['doctor_id'])
        if filters.get('status'):
            query = query.filter(Appointment.status == filters['status'])
        if filters.get('date'):
            query = query.filter(Appointment.appointment_date == filters['date'])
        if filters.get('upcoming_only'):
            today = datetime.date.today()
            query = query.filter(Appointment.appointment_date >= today)

    # Sort
    allowed_sorts = {"appointment_date", "created_at"}
    if sort_by not in allowed_sorts:
        sort_by = "appointment_date"
    
    order_clause = getattr(Appointment, sort_by)
    if sort_dir.lower() == "desc":
        order_clause = order_clause.desc()
    else:
        order_clause = order_clause.asc()

    # Secondary order by time to keep schedules chronological
    if sort_by == "appointment_date":
        if sort_dir.lower() == "desc":
            query = query.order_by(order_clause, Appointment.appointment_time.desc())
        else:
            query = query.order_by(order_clause, Appointment.appointment_time.asc())
    else:
        query = query.order_by(order_clause)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total
