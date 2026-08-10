import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Building2, Loader2, Phone } from "lucide-react";

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
      variant="onboarding"
      stepLabel="Step 1 of 1 · Business Setup"
      sideTitle="Almost there — tell us about your business"
      title="Set up your business"
      subtitle="We'll save these details to prepare your assistant. WhatsApp connection comes next."
    >
      <div className="onboarding-progress" aria-hidden="true">
        <div className="onboarding-progress__bar">
          <span style={{ width: "100%" }} />
        </div>
        <p>Business details</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className={`saas-field ${errors.businessName ? "saas-field--error" : ""}`}>
          <label htmlFor="businessName">
            <Building2 size={16} aria-hidden="true" />
            Business Name
          </label>
          <input
            id="businessName"
            type="text"
            className="saas-input"
            value={formData.businessName}
            onChange={(event) => updateField("businessName", event.target.value)}
            autoComplete="organization"
            aria-invalid={Boolean(errors.businessName)}
            placeholder="Your store or company name"
          />
          {errors.businessName ? (
            <p className="field-error" role="alert">{errors.businessName}</p>
          ) : null}
        </div>

        <div className={`saas-field ${errors.whatsappNumber ? "saas-field--error" : ""}`}>
          <label htmlFor="whatsappNumber">
            <Phone size={16} aria-hidden="true" />
            WhatsApp Number
          </label>
          <input
            id="whatsappNumber"
            type="tel"
            inputMode="tel"
            className="saas-input"
            placeholder="+923001234567"
            value={formData.whatsappNumber}
            onChange={(event) => updateField("whatsappNumber", event.target.value)}
            autoComplete="tel"
            aria-invalid={Boolean(errors.whatsappNumber)}
          />
          <p className="field-hint">
            The WhatsApp number you want to use with your Business Assistant.
            Include country code, e.g. +923001234567.
          </p>
          {errors.whatsappNumber ? (
            <p className="field-error" role="alert">{errors.whatsappNumber}</p>
          ) : null}
        </div>

        {submitError ? <p className="form-error" role="alert">{submitError}</p> : null}

        <button
          type="submit"
          className="saas-btn saas-btn-primary saas-btn-block"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader2 size={18} className="saas-spinner" aria-hidden="true" />
              Saving…
            </>
          ) : (
            <>
              Complete Setup
              <ArrowRight size={18} aria-hidden="true" />
            </>
          )}
        </button>
      </form>
    </AuthLayout>
  );
}
