import React from "react";



import "../fleet.css";

import car1 from "../assets/eurovipdrivers/mercedesE.png";
import car2 from "../assets/eurovipdrivers/mercedesV.png";
import car3 from "../assets/eurovipdrivers/mercedesS.png";
import car4 from "../assets/eurovipdrivers/mercedesVito.png";

const FLEET = [
    {
        id: "mb-s",
        title: "Mercedes-Benz S-Class",
        desc: "Lujo y confort de referencia. Traslados ejecutivos y eventos premium.",
        img: car1,
    },
    {
        id: "bmw-7",
        title: "BMW 7 Series",
        desc: "Elegancia moderna y tecnología de primer nivel. Ideal para viajes largos.",
        img: car2,
    },
    {
        id: "audi-a8",
        title: "Audi A8",
        desc: "Sobriedad y potencia con interior exquisito. Experiencia de alto nivel.",
        img: car3,
    },
    {
        id: "tesla-s",
        title: "Tesla Model S",
        desc: "Lujo eléctrico: silencio absoluto y aceleración instantánea.",
        img: car4,
    },
];

export default function FleetCarousel({ onReserve }) {
    const handleReserve = (car) => {
        if (typeof onReserve === "function") onReserve(car);
    };

    return (
        <section className="fleet-bs">
            <div className="container">
                <header className="text-center mb-3">
                    <h2 className="fleet-title">Our Premium Fleet</h2>
                    <p className="fleet-subtitle">Vehículos de lujo negros con chofer profesional</p>
                </header>

                <div id="fleetCarousel" className="carousel slide" data-bs-ride="carousel" data-bs-interval="6000">
                    {/* Indicadores */}
                    <div className="carousel-indicators">
                        {FLEET.map((_, i) => (
                            <button
                                key={i}
                                type="button"
                                data-bs-target="#fleetCarousel"
                                data-bs-slide-to={i}
                                className={i === 0 ? "active" : ""}
                                aria-current={i === 0 ? "true" : "false"}
                                aria-label={`Slide ${i + 1}`}
                            />
                        ))}
                    </div>

                    {/* Slides */}
                    <div className="carousel-inner">
                        {FLEET.map((car, i) => (
                            <div key={car.id} className={`carousel-item ${i === 0 ? "active" : ""}`}>
                                <div className="card fleet-card mx-auto">
                                    <div className="fleet-img-wrap">
                                        <img src={car.img} className="d-block w-100 fleet-img" alt={car.title} />
                                    </div>
                                    <div className="card-body text-center">
                                        <h3 className="card-title fleet-card-title">{car.title}</h3>
                                        <p className="card-text fleet-card-desc">{car.desc}</p>
                                        <button className="ed-btn ed-btn--gold" onClick={() => handleReserve(car)}>
                                            Reserve
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Controles */}
                    <button className="carousel-control-prev" type="button" data-bs-target="#fleetCarousel" data-bs-slide="prev">
                        <span className="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span className="visually-hidden">Previous</span>
                    </button>
                    <button className="carousel-control-next" type="button" data-bs-target="#fleetCarousel" data-bs-slide="next">
                        <span className="carousel-control-next-icon" aria-hidden="true"></span>
                        <span className="visually-hidden">Next</span>
                    </button>
                </div>
            </div>
        </section>
    );
}