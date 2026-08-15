import { useEffect, useState } from "react";
import { Loader2, Save, Settings } from "lucide-react";

import {
  updateBusiness,
  validateWhatsAppNumber,
} from "../../utils/authApi";

export default function BusinessSettingsCard({ business, onSaved }) {
  const [formData, setFormData] = useState({
    businessName: "",
    whatsappNumber: "",
  });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setFormData({
      businessName: business?.business_name || "",
      whatsappNumber: business?.whatsapp_number || "",
    });
  }, [business]);

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: "" }));
    setSubmitError("");
    setSuccessMessage("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const nextErrors = {};

    if (formData.businessName.trim().length < 2) {
      nextErrors.businessName = "Enter your business name.";
    }

    const whatsappError = validateWhatsAppNumber(formData.whatsappNumber);
    if (whatsappError) {
      nextErrors.whatsappNumber = whatsappError;
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError("");

      const updated = await updateBusiness({
        business_name: formData.businessName.trim(),
        whatsapp_number: formData.whatsappNumber.trim().replace(/\s+/g, "").replace(/-/g, ""),
      });

      setSuccessMessage("Business settings saved.");
      onSaved?.(updated);
    } catch (error) {
      setSubmitError(error.message || "Could not save business settings.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <article className="dash-card dash-card--wide">
      <div className="dash-card__head">
        <div className="dash-card__icon dash-card__icon--blue">
          <Settings size={20} aria-hidden="true" />
        </div>
        <h2>Business Settings</h2>
      </div>

      <form className="auth-form settings-form" onSubmit={handleSubmit} noValidate>
        <div className={`saas-field ${errors.businessName ? "saas-field--error" : ""}`}>
          <label htmlFor="settingsBusinessName">Business Name</label>
          <input
            id="settingsBusinessName"
            className="saas-input"
            value={formData.businessName}
            onChange={(event) => updateField("businessName", event.target.value)}
          />
          {errors.businessName ? (
            <p className="field-error" role="alert">{errors.businessName}</p>
          ) : null}
        </div>

        <div className={`saas-field ${errors.whatsappNumber ? "saas-field--error" : ""}`}>
          <label htmlFor="settingsWhatsapp">WhatsApp Number</label>
          <input
            id="settingsWhatsapp"
            className="saas-input"
            value={formData.whatsappNumber}
            onChange={(event) => updateField("whatsappNumber", event.target.value)}
          />
          {errors.whatsappNumber ? (
            <p className="field-error" role="alert">{errors.whatsappNumber}</p>
          ) : null}
        </div>

        {submitError ? <p className="form-error" role="alert">{submitError}</p> : null}
        {successMessage ? <p className="form-success" role="status">{successMessage}</p> : null}

        <button
          type="submit"
          className="saas-btn saas-btn-primary"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader2 size={16} className="saas-spinner" aria-hidden="true" />
              Saving…
            </>
          ) : (
            <>
              <Save size={16} aria-hidden="true" />
              Save settings
            </>
          )}
        </button>
      </form>
    </article>
  );
}
