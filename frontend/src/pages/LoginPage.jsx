import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthLayout from "../components/auth/AuthLayout";
import PasswordField from "../components/auth/PasswordField";
import { useAuth } from "../context/AuthContext";
import { isValidEmail } from "../utils/authApi";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
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

    if (!isValidEmail(formData.email)) {
      nextErrors.email = "Enter a valid email address.";
    }

    if (!formData.password) {
      nextErrors.password = "Enter your password.";
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

      const user = await login({
        email: formData.email.trim(),
        password: formData.password,
      });

      navigate(user.onboarding_completed ? "/dashboard" : "/onboarding", {
        replace: true,
      });
    } catch (error) {
      setSubmitError(error.message || "Could not log in.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to continue setting up your Business Assistant."
      footer={
        <p>
          New here? <Link to="/signup">Create an account</Link>
        </p>
      }
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="saas-field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={formData.email}
            onChange={(event) => updateField("email", event.target.value)}
            autoComplete="email"
            aria-invalid={Boolean(errors.email)}
          />
          {errors.email ? <p className="field-error">{errors.email}</p> : null}
        </div>

        <PasswordField
          id="password"
          label="Password"
          value={formData.password}
          onChange={(event) => updateField("password", event.target.value)}
          autoComplete="current-password"
          error={errors.password}
        />

        {submitError ? <p className="form-error">{submitError}</p> : null}

        <button
          type="submit"
          className="saas-btn saas-btn-primary saas-btn-block"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Logging in…" : "Log In"}
        </button>
      </form>
    </AuthLayout>
  );
}
