import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";

import AuthLayout from "../components/auth/AuthLayout";
import PasswordField from "../components/auth/PasswordField";
import { useAuth } from "../context/AuthContext";
import { isValidEmail, validatePassword } from "../utils/authApi";

export default function SignupPage() {
  const navigate = useNavigate();
  const { signup } = useAuth();

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
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

    if (formData.fullName.trim().length < 2) {
      nextErrors.fullName = "Enter your full name.";
    }

    if (!isValidEmail(formData.email)) {
      nextErrors.email = "Enter a valid email address.";
    }

    const passwordError = validatePassword(formData.password);
    if (passwordError) {
      nextErrors.password = passwordError;
    }

    if (formData.confirmPassword !== formData.password) {
      nextErrors.confirmPassword = "Passwords do not match.";
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

      await signup({
        full_name: formData.fullName.trim(),
        email: formData.email.trim(),
        password: formData.password,
        confirm_password: formData.confirmPassword,
      });

      navigate("/onboarding", { replace: true });
    } catch (error) {
      setSubmitError(error.message || "Could not create your account.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create your business assistant account"
      subtitle="Start with your name, email, and a secure password."
      footer={
        <p>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      }
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className={`saas-field ${errors.fullName ? "saas-field--error" : ""}`}>
          <label htmlFor="fullName">Full Name</label>
          <input
            id="fullName"
            type="text"
            className="saas-input"
            value={formData.fullName}
            onChange={(event) => updateField("fullName", event.target.value)}
            autoComplete="name"
            aria-invalid={Boolean(errors.fullName)}
            placeholder="Your full name"
          />
          {errors.fullName ? <p className="field-error" role="alert">{errors.fullName}</p> : null}
        </div>

        <div className={`saas-field ${errors.email ? "saas-field--error" : ""}`}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            className="saas-input"
            value={formData.email}
            onChange={(event) => updateField("email", event.target.value)}
            autoComplete="email"
            aria-invalid={Boolean(errors.email)}
            placeholder="you@company.com"
          />
          {errors.email ? <p className="field-error" role="alert">{errors.email}</p> : null}
        </div>

        <PasswordField
          id="password"
          label="Password"
          value={formData.password}
          onChange={(event) => updateField("password", event.target.value)}
          autoComplete="new-password"
          error={errors.password}
        />

        <PasswordField
          id="confirmPassword"
          label="Confirm Password"
          value={formData.confirmPassword}
          onChange={(event) => updateField("confirmPassword", event.target.value)}
          autoComplete="new-password"
          error={errors.confirmPassword}
        />

        {submitError ? <p className="form-error" role="alert">{submitError}</p> : null}

        <button
          type="submit"
          className="saas-btn saas-btn-primary saas-btn-block"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader2 size={18} className="saas-spinner" aria-hidden="true" />
              Creating account…
            </>
          ) : (
            <>
              Create Account
              <ArrowRight size={18} aria-hidden="true" />
            </>
          )}
        </button>
      </form>
    </AuthLayout>
  );
}
