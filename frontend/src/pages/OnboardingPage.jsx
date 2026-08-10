import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AuthLayout from "../components/auth/AuthLayout";
import { useAuth } from "../context/AuthContext";
import { saveBusinessOnboarding, validateWhatsAppNumber } from "../utils/authApi";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const [formData, setFormData] = useState({
    businessName: "",
    whatsappNumber: "",
  });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: "" }));
    setSubmitError("");
  };

  const validateForm = () => {
    const nextErrors = {};

    if (formData.businessName.trim().length < 2) {
      nextErrors.businessName = "Enter your business name.";
    }

    const whatsappError = validateWhatsAppNumber(formData.whatsappNumber);
    if (whatsappError) {
      nextErrors.whatsappNumber = whatsappError;
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError("");

      await saveBusinessOnboarding({
        business_name: formData.businessName.trim(),
        whatsapp_number: formData.whatsappNumber.trim().replace(/\s+/g, "").replace(/-/g, ""),
      });

      await refreshUser();
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmitError(error.message || "Could not save your business details.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Set up your business"
      subtitle="Tell us about your business so we can prepare your assistant."
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="saas-field">
          <label htmlFor="businessName">Business Name</label>
          <input
            id="businessName"
            type="text"
            value={formData.businessName}
            onChange={(event) => updateField("businessName", event.target.value)}
            autoComplete="organization"
            aria-invalid={Boolean(errors.businessName)}
          />
          {errors.businessName ? (
            <p className="field-error">{errors.businessName}</p>
          ) : null}
        </div>

        <div className="saas-field">
          <label htmlFor="whatsappNumber">WhatsApp Number</label>
          <input
            id="whatsappNumber"
            type="tel"
            inputMode="tel"
            placeholder="+923001234567"
            value={formData.whatsappNumber}
            onChange={(event) => updateField("whatsappNumber", event.target.value)}
            autoComplete="tel"
            aria-invalid={Boolean(errors.whatsappNumber)}
          />
          <p className="field-hint">
            This is the WhatsApp number you want to use with your Business Assistant.
            Include your country code, for example +923001234567.
          </p>
          {errors.whatsappNumber ? (
            <p className="field-error">{errors.whatsappNumber}</p>
          ) : null}
        </div>

        {submitError ? <p className="form-error">{submitError}</p> : null}

        <button
          type="submit"
          className="saas-btn saas-btn-primary saas-btn-block"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Saving…" : "Save and Continue"}
        </button>
      </form>
    </AuthLayout>
  );
}
