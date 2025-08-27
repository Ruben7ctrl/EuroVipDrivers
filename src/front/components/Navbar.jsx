// import { Link } from "react-router-dom";

// export const Navbar = () => {

// 	return (
// 		<nav className="navbar navbar-light bg-light">
// 			<div className="container">
// 				<Link to="/">
// 					<span className="navbar-brand mb-0 h1">React Boilerplate</span>
// 				</Link>
// 				<div className="ml-auto">
// 					<Link to="/demo">
// 						<button className="btn btn-primary">Check the Context in action</button>
// 					</Link>
// 				</div>
// 			</div>
// 		</nav>
// 	);
// };

import React, { useState } from "react";
import { Link } from "react-router-dom";
import "../Navbar.css";
import logoImg from "../assets/eurodriversvip/Logo3.png"
export const Navbar = () => {



	return (
		<nav className="navbar navbar-expand-lg navbar-dark ed-nav">
			<div className="container-fluid ed-container">
				{/* Logo a la izquierda */}
				<Link className="navbar-brand ed-logo d-flex align-items-center" to="/">
					<img src={logoImg} alt="Eurovipdrivers logo" className="ed-logo-img" />
					<span className="ed-logo-text">Eurovipdrivers</span></Link>

				{/* Toggler (solo visible < lg por Bootstrap) */}
				<button
					className="navbar-toggler ed-toggler"
					type="button"
					data-bs-toggle="collapse"
					data-bs-target="#edNavbar"
					aria-controls="edNavbar"
					aria-expanded="false"
					aria-label="Toggle navigation"
				>
					<span className="navbar-toggler-icon"></span>
				</button>

				{/* Menú colapsable */}
				<div className="collapse navbar-collapse justify-content-end" id="edNavbar">
					<ul className="navbar-nav mb-2 mb-lg-0 align-items-lg-center gap-lg-3">
						<li className="nav-item"><a className="nav-link" href="#book">Book a Ride</a></li>
						<li className="nav-item"><a className="nav-link" href="#services">Services</a></li>
						<li className="nav-item"><a className="nav-link" href="#fleet">Fleet</a></li>
						<li className="nav-item"><a className="nav-link" href="#contact">Contact</a></li>
						<li className="nav-item mt-2 mt-lg-0">
							<Link className="btn ed-btn ed-btn--gold ms-lg-2" to="signin">Sign In</Link>
						</li>
					</ul>
				</div>
			</div>
		</nav>
	);
}