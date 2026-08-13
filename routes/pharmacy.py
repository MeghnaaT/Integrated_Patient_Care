# =============================================================================
# routes/pharmacy.py — Pharmacy Blueprint
# =============================================================================
# URL Prefix: /pharmacy
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import role_required
from forms.pharmacy_forms import MedicineForm, StockUpdateForm, DispenseMedicineForm
from services.pharmacy_service import (
    get_pharmacy_metrics, list_inventory, add_medicine, update_medicine_stock, dispense_medicine
)
from models.pharmacy import Medicine

pharmacy_bp = Blueprint('pharmacy', __name__)

@pharmacy_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Pharmacist')
def dashboard():
    """Pharmacist Dashboard matching Slide 11 mockup."""
    search_q = request.args.get('q', '').strip()
    metrics = get_pharmacy_metrics()
    inventory = list_inventory(search_q)
    
    med_choices = [(m.id, f"{m.medicine_name} ({m.stock} available)") for m in inventory if m.status != 'Expired']
    dispense_form = DispenseMedicineForm()
    dispense_form.medicine_id.choices = med_choices or [(0, 'No medicines available')]

    add_form = MedicineForm()
    stock_form = StockUpdateForm()

    return render_template(
        'pharmacy/dashboard.html',
        metrics=metrics,
        inventory=inventory,
        search_query=search_q,
        dispense_form=dispense_form,
        add_form=add_form,
        stock_form=stock_form,
        title='Pharmacy Management'
    )


@pharmacy_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Pharmacist')
def add_medicine_view():
    """Add new medicine to pharmacy inventory."""
    form = MedicineForm()
    if form.validate_on_submit():
        try:
            add_medicine(
                medicine_code=form.medicine_code.data.strip().upper(),
                name=form.medicine_name.data.strip(),
                category=form.category.data,
                manufacturer=form.manufacturer.data.strip(),
                stock=form.stock.data,
                unit_price=float(form.unit_price.data),
                expiry_date=form.expiry_date.data
            )
            flash(f"Medicine '{form.medicine_name.data}' added to inventory successfully!", 'success')
            return redirect(url_for('pharmacy.dashboard'))
        except Exception as e:
            flash(f"Error adding medicine: {e}", 'danger')

    return render_template('pharmacy/dashboard.html', add_form=form, title='Add Medicine')


@pharmacy_bp.route('/update-stock/<int:medicine_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Pharmacist')
def update_stock_view(medicine_id):
    """Quick update stock quantity."""
    form = StockUpdateForm()
    if form.validate_on_submit():
        try:
            med = update_medicine_stock(medicine_id, form.stock.data)
            flash(f"Stock for '{med.medicine_name}' updated to {med.stock} successfully!", 'success')
        except Exception as e:
            flash(f"Stock update failed: {e}", 'danger')
    return redirect(url_for('pharmacy.dashboard'))


@pharmacy_bp.route('/dispense', methods=['POST'])
@login_required
@role_required('Admin', 'Pharmacist', 'Doctor')
def dispense_view():
    """Dispense medicine to patient."""
    form = DispenseMedicineForm()
    # Re-populate choices
    inventory = list_inventory()
    form.medicine_id.choices = [(m.id, m.medicine_name) for m in inventory]

    if form.validate_on_submit():
        try:
            dispense = dispense_medicine(
                patient_id=form.patient_id.data,
                medicine_id=form.medicine_id.data,
                quantity=form.quantity.data,
                dispensed_by=current_user.id
            )
            flash(f"Successfully dispensed {dispense.quantity} unit(s) of medicine!", 'success')
        except Exception as e:
            flash(f"Dispensing failed: {e}", 'danger')
    return redirect(url_for('pharmacy.dashboard'))
