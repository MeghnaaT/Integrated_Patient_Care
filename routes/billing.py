# =============================================================================
# routes/billing.py — Billing & Payments Blueprint
# =============================================================================
# URL Prefix: /billing
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.decorators import role_required
from forms.billing_forms import PatientBillingForm
from services.billing_service import (
    generate_bill_for_patient, get_bill_by_id_or_number, list_billing_history
)
from models.patient import Patient
from models.billing import Bill

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/patient-billing', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Receptionist', 'Pharmacist')
def patient_billing():
    """Patient Billing Dashboard matching Slide 16 mockup."""
    form = PatientBillingForm()
    selected_bill = None
    target_patient = None

    patient_query = request.args.get('patient_id', 'P1001').strip()
    # Resolve Patient
    if patient_query.isdigit():
        target_patient = Patient.query.get(int(patient_query))
    if not target_patient and patient_query.startswith('P'):
        pid = patient_query.replace('P', '').replace('PAT', '')
        if pid.isdigit():
            target_patient = Patient.query.get(int(pid))
    if not target_patient:
        target_patient = Patient.query.filter_by(id=4).first() # Fallback to Rahul Kumar

    if target_patient:
        selected_bill = Bill.query.filter_by(patient_id=target_patient.id).order_by(Bill.created_at.desc()).first()

    if form.validate_on_submit():
        try:
            pid = form.patient_id.data.strip()
            p_obj = None
            if pid.isdigit():
                p_obj = Patient.query.get(int(pid))
            elif pid.upper().startswith('P'):
                clean_id = pid.upper().replace('PAT', '').replace('P', '')
                if clean_id.isdigit():
                    p_obj = Patient.query.get(int(clean_id))
            
            if not p_obj:
                p_obj = target_patient or Patient.query.first()

            new_bill = generate_bill_for_patient(
                patient_id=p_obj.id,
                payment_method=form.payment_method.data,
                transaction_id=form.transaction_id.data or None,
                discount=float(form.discount.data or 0.00),
                tax_amount=float(form.tax_amount.data or 0.00)
            )
            flash(f"Payment recorded successfully! Invoice {new_bill.bill_number} generated.", 'success')
            return redirect(url_for('billing.patient_billing', patient_id=p_obj.id))
        except Exception as e:
            flash(f"Billing error: {e}", 'danger')

    billing_history = list_billing_history()

    return render_template(
        'billing/patient_billing.html',
        form=form,
        patient=target_patient,
        bill=selected_bill,
        history=billing_history,
        title='Billing & Payment Management'
    )


@billing_bp.route('/invoice/<int:bill_id>', methods=['GET'])
@login_required
def view_invoice(bill_id):
    """Printable Digital Patient Invoice."""
    bill = get_bill_by_id_or_number(str(bill_id))
    if not bill:
        flash("Invoice not found.", "danger")
        return redirect(url_for('billing.patient_billing'))

    return render_template('billing/invoice.html', bill=bill, title=f"Invoice {bill.bill_number}")


@billing_bp.route('/history', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Receptionist', 'Pharmacist')
def billing_history():
    """Billing History Listing."""
    history = list_billing_history()
    return render_template('billing/history.html', history=history, title='Billing History')
