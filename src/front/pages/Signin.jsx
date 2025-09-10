
import React, { useState } from "react";
import "../styles/signin.css";
import userServices from "../services/userServices";
export const Signin = () => {


    const [error, setError] = useState(""); // Estado para mensajes de error
    const [shake, setShake] = useState(false); // Estado para activar animación

    const [formData, setFormData] = useState({
        email: "",
        password: "",
        confirmPassword: ""
    });

    const handleChange = e => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }



    const handleSubmit = e => {
        e.preventDefault();
        console.log("Form submitted", formData);
        userServices.register(formData).then(data => console.log(data))

        if (!formData.email || !formData.password || !formData.confirmPassword) {
            setError("Fill all the required elements");
            triggerShake();
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match!");
            triggerShake();
            return;
        }
        setError("");
        console.log("Formulario válido, enviando datos...");
    }

    const triggerShake = () => {
        setShake(true);
        setTimeout(() => setShake(false), 800); // La duración coincide con la animación
    };




    return (
        <div className="fondoMain d-flex justify-content-center align-items-center full-height">
            <form onSubmit={handleSubmit}>
                <div className={`ed-card ${shake ? "shake-vertical" : ""}`}>
                    <h2 className="card-title">REGISTER</h2>

                    {/* Email */}
                    <div className="mb-3">
                        <label className="form-label">Email address</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            className={`form-control ${error && !formData.email ? "is-invalid" : ""}`}
                            placeholder="name@example.com"
                        />
                    </div>

                    {/* Password */}
                    <div className="mb-3">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className={`form-control ${error && !formData.password ? "is-invalid" : ""}`}
                        />
                    </div>

                    {/* Confirm Password */}
                    <div className="mb-3">
                        <label className="form-label">Confirm Password</label>
                        <input
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className={`form-control ${error && (!formData.confirmPassword || formData.password !== formData.confirmPassword) ? "is-invalid" : ""}`}
                        />
                    </div>

                    {/* Error */}
                    {error && <div className="invalid-feedback d-block">{error}</div>}

                    {/* Submit */}
                    <div className="d-flex justify-content-center mt-3">
                        <button type="submit" className="ed-btn-gold">
                            Register
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}